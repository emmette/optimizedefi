"""LangGraph workflow for chat with agent routing."""

from typing import Dict, Any, List, Optional, TypedDict, Annotated, Sequence
from dataclasses import dataclass
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from app.agents import (
    OrchestratorAgent,
    PortfolioAgent,
    RebalancingAgent,
    SwapAgent,
    GeneralAgent,
    AgentType
)
from app.tools import get_tools_for_agent
from app.services.performance_logger import performance_logger
from app.services.metrics import metrics_collector
from app.services.memory_manager import memory_manager


# State definition
class ChatState(TypedDict):
    """State for the chat workflow."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    current_agent: Optional[str]
    routing_result: Optional[Dict[str, Any]]
    metadata: Dict[str, Any]
    error: Optional[str]


@dataclass
class WorkflowConfig:
    """Configuration for the chat workflow."""
    enable_memory: bool = True
    max_message_history: int = 50
    enable_streaming: bool = True
    fallback_to_general: bool = True


class ChatWorkflow:
    """LangGraph workflow for multi-agent chat."""
    
    def __init__(self, config: Optional[WorkflowConfig] = None):
        """
        Initialize the chat workflow.
        
        Args:
            config: Workflow configuration
        """
        self.config = config or WorkflowConfig()
        
        # Initialize agents
        self._init_agents()
        
        # Build workflow
        self.workflow = self._build_workflow()
        
        # Create app with memory if enabled
        if self.config.enable_memory:
            memory = MemorySaver()
            self.app = self.workflow.compile(checkpointer=memory)
        else:
            self.app = self.workflow.compile()
    
    def _init_agents(self):
        """Initialize all agents with their tools."""
        # Orchestrator (no tools needed)
        self.orchestrator = OrchestratorAgent()
        
        # Portfolio agent with tools
        portfolio_tools = get_tools_for_agent("portfolio")
        self.portfolio_agent = PortfolioAgent(tools=portfolio_tools)
        
        # Rebalancing agent with tools
        rebalancing_tools = get_tools_for_agent("rebalancing")
        self.rebalancing_agent = RebalancingAgent(tools=rebalancing_tools)
        
        # Swap agent with tools
        swap_tools = get_tools_for_agent("swap")
        self.swap_agent = SwapAgent(tools=swap_tools)
        
        # General agent with tools
        general_tools = get_tools_for_agent("general")
        self.general_agent = GeneralAgent(tools=general_tools)
        
        # Agent map
        self.agents = {
            AgentType.PORTFOLIO.value: self.portfolio_agent,
            AgentType.REBALANCING.value: self.rebalancing_agent,
            AgentType.SWAP.value: self.swap_agent,
            AgentType.GENERAL.value: self.general_agent,
        }
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Create workflow
        workflow = StateGraph(ChatState)
        
        # Add nodes
        workflow.add_node("route_query", self._route_query)
        workflow.add_node("portfolio_agent", self._portfolio_agent_node)
        workflow.add_node("rebalancing_agent", self._rebalancing_agent_node)
        workflow.add_node("swap_agent", self._swap_agent_node)
        workflow.add_node("general_agent", self._general_agent_node)
        workflow.add_node("handle_error", self._handle_error)
        
        # Set entry point
        workflow.set_entry_point("route_query")
        
        # Add conditional edges from router
        workflow.add_conditional_edges(
            "route_query",
            self._select_next_agent,
            {
                "portfolio": "portfolio_agent",
                "rebalancing": "rebalancing_agent",
                "swap": "swap_agent",
                "general": "general_agent",
                "error": "handle_error",
            }
        )
        
        # Add edges from agents to END
        workflow.add_edge("portfolio_agent", END)
        workflow.add_edge("rebalancing_agent", END)
        workflow.add_edge("swap_agent", END)
        workflow.add_edge("general_agent", END)
        workflow.add_edge("handle_error", END)
        
        return workflow
    
    async def _route_query(self, state: ChatState) -> ChatState:
        """Route the query to appropriate agent."""
        try:
            # Get last user message
            user_message = None
            for msg in reversed(state["messages"]):
                if isinstance(msg, HumanMessage):
                    user_message = msg
                    break
            
            if not user_message:
                state["error"] = "No user message found"
                return state
            
            # Track routing
            async with performance_logger.log_operation(
                operation_type="workflow_routing",
                workflow="chat",
                query=user_message.content[:100]
            ) as metrics:
                # Route query
                routing_result = await self.orchestrator.route_query(
                    user_message.content,
                    context=state.get("metadata", {})
                )
                
                # Update state
                state["routing_result"] = routing_result
                state["current_agent"] = routing_result["selected_agent"]
                
                metrics.metadata["selected_agent"] = routing_result["selected_agent"]
                metrics.metadata["confidence"] = routing_result["confidence"]
                
                # Log routing decision
                performance_logger.log_workflow_step(
                    workflow_id=state.get("metadata", {}).get("session_id", "unknown"),
                    step_name="route_query",
                    step_index=0,
                    duration_ms=metrics.duration_ms or 0,
                    status="completed",
                    metadata=routing_result
                )
                
                return state
                
        except Exception as e:
            state["error"] = f"Routing failed: {str(e)}"
            return state
    
    def _select_next_agent(self, state: ChatState) -> str:
        """Select next agent based on routing result."""
        if state.get("error"):
            return "error"
        
        current_agent = state.get("current_agent")
        if current_agent in self.agents:
            return current_agent
        
        # Fallback to general agent
        if self.config.fallback_to_general:
            return "general"
        
        return "error"
    
    async def _portfolio_agent_node(self, state: ChatState) -> ChatState:
        """Execute portfolio agent."""
        return await self._execute_agent(state, self.portfolio_agent, "portfolio")
    
    async def _rebalancing_agent_node(self, state: ChatState) -> ChatState:
        """Execute rebalancing agent."""
        return await self._execute_agent(state, self.rebalancing_agent, "rebalancing")
    
    async def _swap_agent_node(self, state: ChatState) -> ChatState:
        """Execute swap agent."""
        return await self._execute_agent(state, self.swap_agent, "swap")
    
    async def _general_agent_node(self, state: ChatState) -> ChatState:
        """Execute general agent."""
        return await self._execute_agent(state, self.general_agent, "general")
    
    async def _execute_agent(
        self,
        state: ChatState,
        agent: Any,
        agent_type: str
    ) -> ChatState:
        """Execute an agent and update state."""
        try:
            # Get last user message
            user_message = None
            for msg in reversed(state["messages"]):
                if isinstance(msg, HumanMessage):
                    user_message = msg
                    break
            
            if not user_message:
                raise ValueError("No user message found")
            
            # Track agent execution
            async with metrics_collector.track_request(
                agent=agent.name,
                model=agent.model
            ):
                # Add context from routing
                context = state.get("metadata", {}).copy()
                if state.get("routing_result"):
                    context["routing"] = state["routing_result"]
                
                # Execute agent
                if agent.tools:
                    response, tool_calls = await agent.invoke_with_tools(
                        user_message.content,
                        context=context
                    )
                    
                    # Log tool usage
                    if tool_calls:
                        performance_logger.log_custom(
                            "agent_tool_usage",
                            agent=agent.name,
                            tools_called=len(tool_calls),
                            tool_names=[tc.get("name") for tc in tool_calls]
                        )
                else:
                    response = await agent.invoke(
                        user_message.content,
                        context=context
                    )
                
                # Convert response to AIMessage if needed
                if isinstance(response, str):
                    response = AIMessage(
                        content=response,
                        metadata={
                            "agent": agent.name,
                            "agent_type": agent_type
                        }
                    )
                elif hasattr(response, 'metadata'):
                    response.metadata["agent"] = agent.name
                    response.metadata["agent_type"] = agent_type
                
                # Update state
                state["messages"].append(response)
                
                # Log completion
                performance_logger.log_workflow_step(
                    workflow_id=state.get("metadata", {}).get("session_id", "unknown"),
                    step_name=f"{agent_type}_agent",
                    step_index=1,
                    duration_ms=0,  # Already tracked by metrics collector
                    status="completed"
                )
                
                return state
                
        except Exception as e:
            state["error"] = f"{agent_type} agent failed: {str(e)}"
            performance_logger.logger.error(
                "agent_execution_failed",
                agent=agent.name,
                error=str(e)
            )
            return state
    
    async def _handle_error(self, state: ChatState) -> ChatState:
        """Handle errors in the workflow."""
        error_msg = state.get("error", "Unknown error occurred")
        
        # Create error response
        error_response = AIMessage(
            content=f"I encountered an error: {error_msg}. Please try rephrasing your question or contact support if the issue persists.",
            metadata={
                "agent": "error_handler",
                "error": error_msg
            }
        )
        
        state["messages"].append(error_response)
        return state
    
    async def invoke(
        self,
        messages: List[BaseMessage],
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        context_window_size: int = 8192
    ) -> ChatState:
        """
        Invoke the workflow with messages.
        
        Args:
            messages: Input messages
            session_id: Session ID for memory
            metadata: Additional metadata
            context_window_size: Model context window size
            
        Returns:
            Final state after workflow execution
        """
        # If session_id provided, use memory manager
        if session_id and self.config.enable_memory:
            # Get or create session
            user_address = metadata.get("user_address") if metadata else None
            session = await memory_manager.get_or_create_session(session_id, user_address)
            
            # Add new messages to memory
            for msg in messages:
                if isinstance(msg, (HumanMessage, AIMessage)):
                    await memory_manager.add_message(session_id, msg, context_window_size)
            
            # Get optimized message history
            messages = await memory_manager.get_messages_for_context(
                session_id,
                max_tokens=int(context_window_size * 0.9)  # Leave room for response
            )
        
        # Prepare initial state
        initial_state: ChatState = {
            "messages": messages,
            "current_agent": None,
            "routing_result": None,
            "metadata": metadata or {},
            "error": None
        }
        
        if session_id:
            initial_state["metadata"]["session_id"] = session_id
        
        # Run workflow
        config = {"configurable": {"thread_id": session_id}} if session_id else {}
        
        # Execute workflow
        result = await self.app.ainvoke(initial_state, config)
        
        # Store response in memory if session exists
        if session_id and self.config.enable_memory and result.get("messages"):
            last_msg = result["messages"][-1]
            if isinstance(last_msg, AIMessage):
                await memory_manager.add_message(session_id, last_msg, context_window_size)
        
        return result
    
    async def stream(
        self,
        messages: List[BaseMessage],
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        context_window_size: int = 8192
    ):
        """
        Stream the workflow execution.
        
        Args:
            messages: Input messages
            session_id: Session ID
            metadata: Additional metadata
            context_window_size: Model context window size
            
        Yields:
            Workflow events
        """
        # If session_id provided, use memory manager
        if session_id and self.config.enable_memory:
            # Get or create session
            user_address = metadata.get("user_address") if metadata else None
            session = await memory_manager.get_or_create_session(session_id, user_address)
            
            # Add new messages to memory
            for msg in messages:
                if isinstance(msg, (HumanMessage, AIMessage)):
                    await memory_manager.add_message(session_id, msg, context_window_size)
            
            # Get optimized message history
            messages = await memory_manager.get_messages_for_context(
                session_id,
                max_tokens=int(context_window_size * 0.9)
            )
        
        # Prepare initial state
        initial_state: ChatState = {
            "messages": messages,
            "current_agent": None,
            "routing_result": None,
            "metadata": metadata or {},
            "error": None
        }
        
        if session_id:
            initial_state["metadata"]["session_id"] = session_id
        
        # Stream workflow
        config = {"configurable": {"thread_id": session_id}} if session_id else {}
        
        # Track if we've captured the response
        response_captured = False
        
        async for event in self.app.astream(initial_state, config):
            # Capture AI response for memory
            if session_id and self.config.enable_memory and not response_captured:
                for node_name, node_output in event.items():
                    if node_name.endswith("_agent") and "messages" in node_output:
                        for msg in node_output["messages"]:
                            if isinstance(msg, AIMessage):
                                await memory_manager.add_message(session_id, msg, context_window_size)
                                response_captured = True
                                break
            
            yield event


# Removed global workflow instance to prevent startup crashes
# Workflows should be created lazily when needed

# Thread-safe workflow instance cache
_workflow_instance = None
_workflow_error = None

def get_chat_workflow():
    """
    Get or create a ChatWorkflow instance with proper error handling.
    
    Returns:
        ChatWorkflow instance or None if initialization fails
    """
    global _workflow_instance, _workflow_error
    
    # Return cached instance if available
    if _workflow_instance is not None:
        return _workflow_instance
    
    # Return None if we've already tried and failed
    if _workflow_error is not None:
        return None
    
    try:
        # Try to create workflow instance
        _workflow_instance = ChatWorkflow()
        return _workflow_instance
    except Exception as e:
        # Cache the error to avoid repeated attempts
        _workflow_error = str(e)
        import logging
        logging.error(f"Failed to initialize ChatWorkflow: {e}")
        return None