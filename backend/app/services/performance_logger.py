"""Structured performance logger for AI operations."""

import time
import json
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
import structlog
from structlog.contextvars import merge_contextvars

# Configure structured logging
structlog.configure(
    processors=[
        merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)


@dataclass
class PerformanceMetrics:
    """Performance metrics for an operation."""
    operation_id: str
    operation_type: str
    agent: Optional[str]
    model: Optional[str]
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None
    tokens_per_second: Optional[float] = None
    cost: Optional[float] = None
    cache_hit: bool = False
    error: Optional[str] = None
    error_type: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def complete(self, end_time: Optional[float] = None):
        """Mark operation as complete and calculate metrics."""
        if end_time is None:
            end_time = time.time()
        
        self.end_time = end_time
        self.duration_ms = (self.end_time - self.start_time) * 1000
        
        # Calculate tokens per second if we have token counts
        if self.duration_ms > 0 and self.tokens_output:
            self.tokens_per_second = self.tokens_output / (self.duration_ms / 1000)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        data = asdict(self)
        # Add calculated fields
        data["timestamp"] = datetime.fromtimestamp(self.start_time).isoformat()
        if self.end_time:
            data["end_timestamp"] = datetime.fromtimestamp(self.end_time).isoformat()
        return data


class PerformanceLogger:
    """Logger for AI operation performance metrics."""
    
    def __init__(self):
        """Initialize the performance logger."""
        self.logger = structlog.get_logger(__name__)
        self._active_operations: Dict[str, PerformanceMetrics] = {}
    
    @asynccontextmanager
    async def log_operation(
        self,
        operation_type: str,
        operation_id: Optional[str] = None,
        agent: Optional[str] = None,
        model: Optional[str] = None,
        **metadata
    ):
        """
        Context manager for logging operation performance.
        
        Args:
            operation_type: Type of operation (e.g., "llm_call", "tool_execution")
            operation_id: Optional operation ID
            agent: Optional agent name
            model: Optional model name
            **metadata: Additional metadata to log
            
        Yields:
            PerformanceMetrics instance
        """
        # Generate operation ID if not provided
        if operation_id is None:
            operation_id = f"{operation_type}_{int(time.time() * 1000000)}"
        
        # Create metrics instance
        metrics = PerformanceMetrics(
            operation_id=operation_id,
            operation_type=operation_type,
            agent=agent,
            model=model,
            start_time=time.time(),
            metadata=metadata
        )
        
        # Store active operation
        self._active_operations[operation_id] = metrics
        
        # Log operation start
        self.logger.info(
            "operation_started",
            **metrics.to_dict()
        )
        
        try:
            yield metrics
            
            # Complete metrics
            metrics.complete()
            
            # Log operation completion
            self.logger.info(
                "operation_completed",
                **metrics.to_dict()
            )
            
        except Exception as e:
            # Record error
            metrics.error = str(e)
            metrics.error_type = type(e).__name__
            metrics.complete()
            
            # Log operation failure
            self.logger.error(
                "operation_failed",
                **metrics.to_dict()
            )
            
            # Re-raise exception
            raise
            
        finally:
            # Remove from active operations
            self._active_operations.pop(operation_id, None)
    
    def log_llm_call(
        self,
        agent: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        duration_ms: float,
        cost: Optional[float] = None,
        cache_hit: bool = False,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log LLM call performance.
        
        Args:
            agent: Agent making the call
            model: Model used
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            duration_ms: Duration in milliseconds
            cost: Optional cost in dollars
            cache_hit: Whether response was from cache
            metadata: Additional metadata
        """
        self.logger.info(
            "llm_call",
            agent=agent,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            duration_ms=duration_ms,
            tokens_per_second=completion_tokens / (duration_ms / 1000) if duration_ms > 0 else 0,
            cost=cost,
            cache_hit=cache_hit,
            metadata=metadata or {}
        )
    
    def log_tool_execution(
        self,
        agent: str,
        tool_name: str,
        duration_ms: float,
        success: bool,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log tool execution performance.
        
        Args:
            agent: Agent executing the tool
            tool_name: Name of the tool
            duration_ms: Duration in milliseconds
            success: Whether execution was successful
            error: Error message if failed
            metadata: Additional metadata
        """
        self.logger.info(
            "tool_execution",
            agent=agent,
            tool_name=tool_name,
            duration_ms=duration_ms,
            success=success,
            error=error,
            metadata=metadata or {}
        )
    
    def log_agent_routing(
        self,
        query: str,
        selected_agent: str,
        confidence: float,
        routing_time_ms: float,
        alternatives: Optional[List[Dict[str, float]]] = None
    ):
        """
        Log agent routing decision.
        
        Args:
            query: User query
            selected_agent: Agent selected
            confidence: Confidence score
            routing_time_ms: Time taken to route
            alternatives: Alternative agents considered
        """
        self.logger.info(
            "agent_routing",
            query_preview=query[:100] + "..." if len(query) > 100 else query,
            selected_agent=selected_agent,
            confidence=confidence,
            routing_time_ms=routing_time_ms,
            alternatives=alternatives or []
        )
    
    def log_rate_limit(
        self,
        model: str,
        limit_type: str,
        wait_time_seconds: float,
        retry_attempt: int
    ):
        """
        Log rate limit event.
        
        Args:
            model: Model that hit rate limit
            limit_type: Type of limit
            wait_time_seconds: Time to wait
            retry_attempt: Current retry attempt
        """
        self.logger.warning(
            "rate_limit_hit",
            model=model,
            limit_type=limit_type,
            wait_time_seconds=wait_time_seconds,
            retry_attempt=retry_attempt
        )
    
    def log_memory_operation(
        self,
        operation: str,  # "save", "load", "search", "clear"
        memory_type: str,  # "conversation", "agent", "tool"
        size_bytes: Optional[int] = None,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log memory operation.
        
        Args:
            operation: Type of memory operation
            memory_type: Type of memory
            size_bytes: Size of data in bytes
            duration_ms: Duration in milliseconds
            metadata: Additional metadata
        """
        self.logger.info(
            "memory_operation",
            operation=operation,
            memory_type=memory_type,
            size_bytes=size_bytes,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
    
    def log_batch_operation(
        self,
        operation_type: str,
        batch_size: int,
        successful: int,
        failed: int,
        duration_ms: float,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log batch operation performance.
        
        Args:
            operation_type: Type of batch operation
            batch_size: Total batch size
            successful: Number of successful operations
            failed: Number of failed operations
            duration_ms: Total duration
            metadata: Additional metadata
        """
        self.logger.info(
            "batch_operation",
            operation_type=operation_type,
            batch_size=batch_size,
            successful=successful,
            failed=failed,
            success_rate=successful / batch_size if batch_size > 0 else 0,
            duration_ms=duration_ms,
            avg_duration_ms=duration_ms / batch_size if batch_size > 0 else 0,
            metadata=metadata or {}
        )
    
    def log_workflow_step(
        self,
        workflow_id: str,
        step_name: str,
        step_index: int,
        duration_ms: float,
        status: str,  # "started", "completed", "failed", "skipped"
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Log workflow step execution.
        
        Args:
            workflow_id: ID of the workflow
            step_name: Name of the step
            step_index: Index of step in workflow
            duration_ms: Duration of step
            status: Status of step
            metadata: Additional metadata
        """
        self.logger.info(
            "workflow_step",
            workflow_id=workflow_id,
            step_name=step_name,
            step_index=step_index,
            duration_ms=duration_ms,
            status=status,
            metadata=metadata or {}
        )
    
    def get_active_operations(self) -> List[Dict[str, Any]]:
        """
        Get currently active operations.
        
        Returns:
            List of active operation metrics
        """
        return [
            metrics.to_dict()
            for metrics in self._active_operations.values()
        ]
    
    def log_custom(
        self,
        event_type: str,
        level: str = "info",
        **kwargs
    ):
        """
        Log custom event with structured data.
        
        Args:
            event_type: Type of event
            level: Log level
            **kwargs: Event data
        """
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(event_type, **kwargs)


# Global performance logger instance
performance_logger = PerformanceLogger()