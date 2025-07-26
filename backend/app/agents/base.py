"""Base agent class with metrics integration."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, Union
import time
import uuid
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tools import Tool
from langchain_core.callbacks import BaseCallbackHandler
import tiktoken

from app.core.config import settings
from app.services.metrics import metrics_collector
from app.services.cost_calculator import cost_calculator
from app.services.rate_limit_manager import rate_limit_manager
from app.services.performance_logger import performance_logger


class MetricsCallbackHandler(BaseCallbackHandler):
    """Callback handler for collecting metrics during LLM calls."""
    
    def __init__(self, agent_name: str, model: str):
        """
        Initialize the metrics callback handler.
        
        Args:
            agent_name: Name of the agent
            model: Model being used
        """
        self.agent_name = agent_name
        self.model = model
        self.start_time: Optional[float] = None
        self.prompt_tokens: int = 0
        self.completion_tokens: int = 0
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs):
        """Called when LLM starts."""
        self.start_time = time.time()
    
    def on_llm_end(self, response, **kwargs):
        """Called when LLM ends."""
        if self.start_time:
            duration = time.time() - self.start_time
            
            # Extract token usage if available
            if hasattr(response, 'llm_output') and response.llm_output:
                usage = response.llm_output.get('token_usage', {})
                self.prompt_tokens = usage.get('prompt_tokens', 0)
                self.completion_tokens = usage.get('completion_tokens', 0)
            
            # Log performance
            performance_logger.log_llm_call(
                agent=self.agent_name,
                model=self.model,
                prompt_tokens=self.prompt_tokens,
                completion_tokens=self.completion_tokens,
                duration_ms=duration * 1000,
                cache_hit=False
            )


class BaseAgent(ABC):
    """Base class for all AI agents with metrics integration."""
    
    def __init__(
        self,
        name: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Tool]] = None,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize the base agent.
        
        Args:
            name: Name of the agent
            model: Model to use (defaults to config)
            temperature: Temperature for generation
            max_tokens: Maximum tokens to generate
            tools: List of tools available to the agent
            system_prompt: System prompt for the agent
        """
        self.name = name
        self.model = model or settings.DEFAULT_MODEL
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.tools = tools or []
        self.system_prompt = system_prompt or self._get_default_system_prompt()
        
        # Initialize LLM
        self.llm = self._create_llm()
        
        # Initialize token encoder
        self._init_tokenizer()
    
    def _create_llm(self) -> ChatOpenAI:
        """Create the LLM instance with OpenRouter."""
        return ChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": "https://optimizedefi.com",
                "X-Title": "OptimizeDeFi"
            },
            callbacks=[MetricsCallbackHandler(self.name, self.model)]
        )
    
    def _init_tokenizer(self):
        """Initialize the token encoder for counting tokens."""
        try:
            # Try to get encoding for the model
            self.encoding = tiktoken.encoding_for_model(self.model)
        except:
            # Fallback to cl100k_base encoding
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoding.encode(text))
    
    def _estimate_tokens(self, messages: List[BaseMessage]) -> int:
        """Estimate tokens for a list of messages."""
        total = 0
        for msg in messages:
            # Add message content
            total += self._count_tokens(msg.content)
            # Add overhead for message structure
            total += 4  # Approximate overhead per message
        return total
    
    @abstractmethod
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt for the agent."""
        pass
    
    async def _acquire_rate_limit(self, estimated_tokens: int) -> bool:
        """
        Acquire rate limit capacity.
        
        Args:
            estimated_tokens: Estimated tokens for the request
            
        Returns:
            True if acquired, False otherwise
        """
        return await rate_limit_manager.acquire(
            model=self.model,
            tokens=estimated_tokens,
            wait=True,
            max_wait=30.0
        )
    
    async def _release_rate_limit(self):
        """Release rate limit capacity."""
        await rate_limit_manager.release(self.model)
    
    async def _track_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        duration: float,
        cache_hit: bool = False
    ):
        """
        Track token usage and costs.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            duration: Duration in seconds
            cache_hit: Whether response was from cache
        """
        # Calculate cost
        cost, pricing_details = await cost_calculator.calculate_cost(
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens
        )
        
        # Record metrics
        await metrics_collector.record_token_usage(
            agent=self.name,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost
        )
        
        # Log performance
        performance_logger.log_llm_call(
            agent=self.name,
            model=self.model,
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens,
            duration_ms=duration * 1000,
            cost=cost,
            cache_hit=cache_hit,
            metadata=pricing_details
        )
    
    async def invoke(
        self,
        messages: Union[str, List[BaseMessage]],
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Union[str, AIMessage]:
        """
        Invoke the agent with messages.
        
        Args:
            messages: Input messages or string
            context: Optional context for the agent
            stream: Whether to stream the response
            
        Returns:
            Response string or AIMessage
        """
        # Convert string to messages if needed
        if isinstance(messages, str):
            messages = [HumanMessage(content=messages)]
        
        # Add system message if not present
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=self.system_prompt)] + messages
        
        # Estimate tokens
        estimated_input_tokens = self._estimate_tokens(messages)
        
        # Track request
        request_id = f"{self.name}_{uuid.uuid4().hex[:8]}"
        
        async with metrics_collector.track_request(
            agent=self.name,
            model=self.model,
            request_id=request_id
        ):
            try:
                # Acquire rate limit
                acquired = await self._acquire_rate_limit(estimated_input_tokens)
                if not acquired:
                    raise Exception("Rate limit exceeded")
                
                # Start timing
                start_time = time.time()
                
                # Invoke LLM
                if stream:
                    # Streaming not implemented yet
                    raise NotImplementedError("Streaming not yet implemented")
                else:
                    response = await self.llm.ainvoke(messages)
                
                # Calculate actual tokens and duration
                duration = time.time() - start_time
                
                # Extract token counts from response
                if hasattr(response, 'response_metadata'):
                    usage = response.response_metadata.get('token_usage', {})
                    actual_input_tokens = usage.get('prompt_tokens', estimated_input_tokens)
                    output_tokens = usage.get('completion_tokens', 0)
                else:
                    actual_input_tokens = estimated_input_tokens
                    output_tokens = self._count_tokens(response.content)
                
                # Track usage
                await self._track_usage(
                    input_tokens=actual_input_tokens,
                    output_tokens=output_tokens,
                    duration=duration,
                    cache_hit=False
                )
                
                return response
                
            except Exception as e:
                # Log error
                performance_logger.logger.error(
                    "agent_invocation_failed",
                    agent=self.name,
                    model=self.model,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise
                
            finally:
                # Release rate limit
                await self._release_rate_limit()
    
    async def invoke_with_tools(
        self,
        messages: Union[str, List[BaseMessage]],
        tools: Optional[List[Tool]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[AIMessage, List[Dict[str, Any]]]:
        """
        Invoke the agent with tool support.
        
        Args:
            messages: Input messages
            tools: Tools to use (defaults to agent's tools)
            context: Optional context
            
        Returns:
            Tuple of (response, tool_calls)
        """
        # Use provided tools or agent's tools
        tools_to_use = tools or self.tools
        
        if not tools_to_use:
            # No tools, just invoke normally
            response = await self.invoke(messages, context)
            return response, []
        
        # Bind tools to LLM
        llm_with_tools = self.llm.bind_tools(tools_to_use)
        
        # Convert string to messages if needed
        if isinstance(messages, str):
            messages = [HumanMessage(content=messages)]
        
        # Add system message
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=self.system_prompt)] + messages
        
        # Estimate tokens
        estimated_tokens = self._estimate_tokens(messages)
        
        async with performance_logger.log_operation(
            operation_type="agent_with_tools",
            agent=self.name,
            model=self.model
        ) as metrics:
            try:
                # Acquire rate limit
                acquired = await self._acquire_rate_limit(estimated_tokens)
                if not acquired:
                    raise Exception("Rate limit exceeded")
                
                # Invoke with tools
                response = await llm_with_tools.ainvoke(messages)
                
                # Extract tool calls
                tool_calls = []
                if hasattr(response, 'tool_calls'):
                    tool_calls = response.tool_calls
                
                # Update metrics
                metrics.metadata["tool_calls_count"] = len(tool_calls)
                metrics.metadata["tools_available"] = len(tools_to_use)
                
                return response, tool_calls
                
            finally:
                await self._release_rate_limit()
    
    def create_prompt(
        self,
        template: str,
        include_messages: bool = True
    ) -> ChatPromptTemplate:
        """
        Create a prompt template.
        
        Args:
            template: Template string
            include_messages: Whether to include messages placeholder
            
        Returns:
            ChatPromptTemplate
        """
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=template)
        ]
        
        if include_messages:
            messages.append(MessagesPlaceholder(variable_name="messages"))
        
        return ChatPromptTemplate.from_messages(messages)
    
    async def batch_invoke(
        self,
        message_batches: List[List[BaseMessage]],
        max_concurrency: int = 5
    ) -> List[Union[AIMessage, Exception]]:
        """
        Invoke the agent with multiple message batches.
        
        Args:
            message_batches: List of message batches
            max_concurrency: Maximum concurrent requests
            
        Returns:
            List of responses or exceptions
        """
        import asyncio
        
        async def invoke_single(messages):
            try:
                return await self.invoke(messages)
            except Exception as e:
                return e
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def invoke_with_semaphore(messages):
            async with semaphore:
                return await invoke_single(messages)
        
        # Track batch operation
        start_time = time.time()
        
        # Execute all invocations
        results = await asyncio.gather(
            *[invoke_with_semaphore(messages) for messages in message_batches],
            return_exceptions=True
        )
        
        # Log batch performance
        duration = time.time() - start_time
        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - successful
        
        performance_logger.log_batch_operation(
            operation_type=f"{self.name}_batch_invoke",
            batch_size=len(message_batches),
            successful=successful,
            failed=failed,
            duration_ms=duration * 1000,
            metadata={
                "max_concurrency": max_concurrency,
                "model": self.model
            }
        )
        
        return results