"""Tests for chat workflow."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.workflows.chat_workflow import ChatWorkflow, ChatState, WorkflowConfig
from app.agents import AgentType


class TestChatWorkflow:
    """Test chat workflow functionality."""

    @pytest.fixture
    def mock_agents(self):
        """Create mock agents for testing."""
        with patch("app.workflows.chat_workflow.OrchestratorAgent") as mock_orch, \
             patch("app.workflows.chat_workflow.PortfolioAgent") as mock_portfolio, \
             patch("app.workflows.chat_workflow.RebalancingAgent") as mock_rebalancing, \
             patch("app.workflows.chat_workflow.SwapAgent") as mock_swap, \
             patch("app.workflows.chat_workflow.GeneralAgent") as mock_general:
            
            # Configure orchestrator
            orchestrator = MagicMock()
            orchestrator.route_query = AsyncMock(return_value={
                "agent": AgentType.GENERAL.value,
                "confidence": 0.9,
                "reasoning": "General query"
            })
            mock_orch.return_value = orchestrator
            
            # Configure other agents
            for mock_agent in [mock_portfolio, mock_rebalancing, mock_swap, mock_general]:
                agent = MagicMock()
                agent.invoke = AsyncMock(return_value="Test response")
                agent.tools = []
                agent.name = "test_agent"
                agent.model = "test_model"
                mock_agent.return_value = agent
            
            yield {
                "orchestrator": orchestrator,
                "portfolio": mock_portfolio.return_value,
                "rebalancing": mock_rebalancing.return_value,
                "swap": mock_swap.return_value,
                "general": mock_general.return_value
            }

    @pytest.mark.asyncio
    async def test_workflow_initialization(self, mock_agents):
        """Test workflow initialization."""
        config = WorkflowConfig(enable_memory=False)
        workflow = ChatWorkflow(config)
        
        assert workflow.config == config
        assert workflow.orchestrator is not None
        assert workflow.portfolio_agent is not None
        assert workflow.rebalancing_agent is not None
        assert workflow.swap_agent is not None
        assert workflow.general_agent is not None

    @pytest.mark.asyncio
    async def test_workflow_invoke_general_query(self, mock_agents):
        """Test workflow with general query."""
        config = WorkflowConfig(enable_memory=False)
        workflow = ChatWorkflow(config)
        
        # Configure general agent response
        mock_agents["general"].invoke.return_value = "DeFi stands for Decentralized Finance"
        
        # Test message
        messages = [HumanMessage(content="What is DeFi?")]
        
        # Invoke workflow
        result = await workflow.invoke(messages)
        
        assert "messages" in result
        assert len(result["messages"]) > 0
        
        # Check that general agent was called
        mock_agents["general"].invoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_routing_to_portfolio(self, mock_agents):
        """Test routing to portfolio agent."""
        config = WorkflowConfig(enable_memory=False)
        workflow = ChatWorkflow(config)
        
        # Configure orchestrator to route to portfolio
        mock_agents["orchestrator"].route_query.return_value = {
            "agent": AgentType.PORTFOLIO.value,
            "confidence": 0.95,
            "reasoning": "User asking about portfolio"
        }
        
        # Configure portfolio response
        mock_agents["portfolio"].invoke.return_value = "Your portfolio value is $10,000"
        
        messages = [HumanMessage(content="Show my portfolio")]
        
        result = await workflow.invoke(messages)
        
        # Verify portfolio agent was called
        mock_agents["portfolio"].invoke.assert_called_once()
        assert "routing_result" in result
        assert result["routing_result"]["agent"] == AgentType.PORTFOLIO.value

    @pytest.mark.asyncio
    async def test_workflow_with_tools(self, mock_agents):
        """Test workflow with agent that has tools."""
        config = WorkflowConfig(enable_memory=False)
        workflow = ChatWorkflow(config)
        
        # Configure swap agent with tools
        mock_tools = [MagicMock(name="get_quote"), MagicMock(name="execute_swap")]
        mock_agents["swap"].tools = mock_tools
        mock_agents["swap"].invoke_with_tools = AsyncMock(
            return_value=("Best swap route found", [{"name": "get_quote", "args": {}}])
        )
        
        # Configure orchestrator to route to swap
        mock_agents["orchestrator"].route_query.return_value = {
            "agent": AgentType.SWAP.value,
            "confidence": 0.98,
            "reasoning": "User wants to swap tokens"
        }
        
        messages = [HumanMessage(content="Swap 100 USDC to ETH")]
        
        result = await workflow.invoke(messages)
        
        # Verify swap agent with tools was called
        mock_agents["swap"].invoke_with_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_workflow_error_handling(self, mock_agents):
        """Test workflow error handling."""
        config = WorkflowConfig(enable_memory=False, fallback_to_general=True)
        workflow = ChatWorkflow(config)
        
        # Configure orchestrator to fail
        mock_agents["orchestrator"].route_query.side_effect = Exception("Routing error")
        
        # Configure general agent as fallback
        mock_agents["general"].invoke.return_value = "I encountered an error, but I can still help!"
        
        messages = [HumanMessage(content="Test error handling")]
        
        result = await workflow.invoke(messages)
        
        # Should fallback to general agent
        assert "error" in result or len(result["messages"]) > 0

    @pytest.mark.asyncio
    async def test_workflow_streaming(self, mock_agents):
        """Test workflow streaming functionality."""
        config = WorkflowConfig(enable_memory=False, enable_streaming=True)
        workflow = ChatWorkflow(config)
        
        # Configure general agent
        mock_agents["general"].invoke.return_value = "Streaming response"
        
        messages = [HumanMessage(content="Test streaming")]
        
        # Collect streamed events
        events = []
        async for event in workflow.stream(messages):
            events.append(event)
        
        # Should have routing and agent events
        assert len(events) > 0
        assert any("route_query" in event for event in events)
        assert any("general_agent" in event for event in events)

    @pytest.mark.asyncio
    async def test_workflow_with_session_memory(self, mock_agents):
        """Test workflow with session memory."""
        config = WorkflowConfig(enable_memory=True)
        
        with patch("app.workflows.chat_workflow.memory_manager") as mock_memory:
            mock_memory.get_messages_for_context = AsyncMock(return_value=[
                HumanMessage(content="Previous question"),
                AIMessage(content="Previous answer")
            ])
            mock_memory.add_message = AsyncMock()
            
            workflow = ChatWorkflow(config)
            
            messages = [HumanMessage(content="Follow up question")]
            session_id = "test-session-123"
            
            result = await workflow.invoke(messages, session_id=session_id)
            
            # Verify memory manager was used
            mock_memory.get_messages_for_context.assert_called_once_with(
                session_id, max_tokens=pytest.Any(int)
            )
            mock_memory.add_message.assert_called()

    @pytest.mark.asyncio
    async def test_workflow_state_management(self, mock_agents):
        """Test workflow state management."""
        config = WorkflowConfig(enable_memory=False)
        workflow = ChatWorkflow(config)
        
        # Initial state
        initial_state: ChatState = {
            "messages": [HumanMessage(content="Test message")],
            "current_agent": None,
            "routing_result": None,
            "metadata": {"test": True},
            "error": None
        }
        
        # Mock the app invoke
        workflow.app = AsyncMock()
        workflow.app.ainvoke = AsyncMock(return_value={
            "messages": initial_state["messages"] + [
                AIMessage(content="Test response", metadata={"agent": "general"})
            ],
            "current_agent": "general",
            "routing_result": {"agent": "general", "confidence": 0.9},
            "metadata": initial_state["metadata"],
            "error": None
        })
        
        result = await workflow.invoke(initial_state["messages"], metadata={"test": True})
        
        # Verify state was properly managed
        assert len(result["messages"]) == 2
        assert result["current_agent"] == "general"
        assert result["metadata"]["test"] is True

    @pytest.mark.asyncio
    async def test_workflow_agent_metadata(self, mock_agents):
        """Test that agent responses include proper metadata."""
        config = WorkflowConfig(enable_memory=False)
        workflow = ChatWorkflow(config)
        
        # Configure rebalancing agent
        mock_agents["orchestrator"].route_query.return_value = {
            "agent": AgentType.REBALANCING.value,
            "confidence": 0.92
        }
        
        mock_agents["rebalancing"].invoke.return_value = "Rebalancing recommendation"
        
        messages = [HumanMessage(content="Optimize my portfolio")]
        
        # Mock the workflow execution
        workflow.app = AsyncMock()
        workflow.app.ainvoke = AsyncMock(return_value={
            "messages": messages + [
                AIMessage(
                    content="Rebalancing recommendation",
                    metadata={
                        "agent": "rebalancing",
                        "agent_type": AgentType.REBALANCING.value,
                        "model": "test_model"
                    }
                )
            ],
            "current_agent": AgentType.REBALANCING.value,
            "routing_result": {"agent": AgentType.REBALANCING.value, "confidence": 0.92},
            "metadata": {},
            "error": None
        })
        
        result = await workflow.invoke(messages)
        
        # Check response metadata
        last_message = result["messages"][-1]
        assert isinstance(last_message, AIMessage)
        assert last_message.metadata["agent"] == "rebalancing"
        assert last_message.metadata["agent_type"] == AgentType.REBALANCING.value