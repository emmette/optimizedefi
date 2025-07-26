"""Batch tool executor for parallel processing."""

import asyncio
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import uuid
from langchain_core.tools import BaseTool, ToolException

from app.services.performance_logger import performance_logger


@dataclass
class BatchToolRequest:
    """Single tool request in a batch."""
    request_id: str
    tool: BaseTool
    inputs: Dict[str, Any]
    timeout: Optional[float] = None
    
    @classmethod
    def create(
        cls,
        tool: BaseTool,
        inputs: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> "BatchToolRequest":
        """Create a new batch request with auto-generated ID."""
        return cls(
            request_id=str(uuid.uuid4()),
            tool=tool,
            inputs=inputs,
            timeout=timeout
        )


@dataclass
class BatchToolResult:
    """Result from a batch tool execution."""
    request_id: str
    tool_name: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "request_id": self.request_id,
            "tool_name": self.tool_name,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms
        }


class BatchToolExecutor:
    """Execute multiple tools in parallel with optimizations."""
    
    def __init__(
        self,
        max_concurrency: int = 10,
        default_timeout: float = 30.0,
        enable_caching: bool = True
    ):
        """
        Initialize the batch executor.
        
        Args:
            max_concurrency: Maximum concurrent tool executions
            default_timeout: Default timeout for tool executions
            enable_caching: Whether to enable result caching
        """
        self.max_concurrency = max_concurrency
        self.default_timeout = default_timeout
        self.enable_caching = enable_caching
        self._cache: Dict[str, BatchToolResult] = {}
        self._semaphore = asyncio.Semaphore(max_concurrency)
    
    def _get_cache_key(self, tool_name: str, inputs: Dict[str, Any]) -> str:
        """Generate cache key for tool execution."""
        import hashlib
        import json
        
        # Create stable string representation
        input_str = json.dumps(inputs, sort_keys=True)
        key_str = f"{tool_name}:{input_str}"
        
        # Hash for consistent key
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    async def _execute_single(
        self,
        request: BatchToolRequest
    ) -> BatchToolResult:
        """Execute a single tool request."""
        start_time = asyncio.get_event_loop().time()
        
        # Check cache if enabled
        if self.enable_caching:
            cache_key = self._get_cache_key(request.tool.name, request.inputs)
            if cache_key in self._cache:
                cached_result = self._cache[cache_key]
                performance_logger.log_custom(
                    "batch_tool_cache_hit",
                    tool_name=request.tool.name,
                    request_id=request.request_id
                )
                return BatchToolResult(
                    request_id=request.request_id,
                    tool_name=cached_result.tool_name,
                    success=cached_result.success,
                    result=cached_result.result,
                    error=cached_result.error,
                    duration_ms=0  # Cached, no execution time
                )
        
        # Execute with semaphore for concurrency control
        async with self._semaphore:
            try:
                # Set timeout
                timeout = request.timeout or self.default_timeout
                
                # Execute tool with timeout
                result = await asyncio.wait_for(
                    request.tool.ainvoke(request.inputs),
                    timeout=timeout
                )
                
                # Calculate duration
                duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                
                # Create result
                batch_result = BatchToolResult(
                    request_id=request.request_id,
                    tool_name=request.tool.name,
                    success=True,
                    result=result,
                    duration_ms=duration_ms
                )
                
                # Cache if enabled
                if self.enable_caching:
                    self._cache[cache_key] = batch_result
                
                return batch_result
                
            except asyncio.TimeoutError:
                duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                return BatchToolResult(
                    request_id=request.request_id,
                    tool_name=request.tool.name,
                    success=False,
                    error=f"Timeout after {timeout} seconds",
                    duration_ms=duration_ms
                )
                
            except ToolException as e:
                duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                return BatchToolResult(
                    request_id=request.request_id,
                    tool_name=request.tool.name,
                    success=False,
                    error=str(e),
                    duration_ms=duration_ms
                )
                
            except Exception as e:
                duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                performance_logger.logger.error(
                    "batch_tool_execution_error",
                    tool_name=request.tool.name,
                    request_id=request.request_id,
                    error=str(e),
                    error_type=type(e).__name__
                )
                return BatchToolResult(
                    request_id=request.request_id,
                    tool_name=request.tool.name,
                    success=False,
                    error=f"Unexpected error: {str(e)}",
                    duration_ms=duration_ms
                )
    
    async def execute_batch(
        self,
        requests: List[BatchToolRequest],
        fail_fast: bool = False
    ) -> List[BatchToolResult]:
        """
        Execute multiple tool requests in parallel.
        
        Args:
            requests: List of tool requests
            fail_fast: Whether to cancel remaining on first failure
            
        Returns:
            List of results in the same order as requests
        """
        if not requests:
            return []
        
        # Track batch execution
        batch_id = str(uuid.uuid4())
        start_time = asyncio.get_event_loop().time()
        
        async with performance_logger.log_operation(
            operation_type="batch_tool_execution",
            batch_id=batch_id,
            batch_size=len(requests),
            tool_names=[r.tool.name for r in requests]
        ) as metrics:
            try:
                if fail_fast:
                    # Execute with fail-fast behavior
                    results = []
                    tasks = []
                    
                    for request in requests:
                        task = asyncio.create_task(self._execute_single(request))
                        tasks.append(task)
                    
                    # Wait for tasks and check results
                    for task in asyncio.as_completed(tasks):
                        result = await task
                        results.append(result)
                        
                        if not result.success:
                            # Cancel remaining tasks
                            for t in tasks:
                                if not t.done():
                                    t.cancel()
                            break
                    
                    # Wait for cancellations
                    await asyncio.gather(*tasks, return_exceptions=True)
                    
                else:
                    # Execute all regardless of failures
                    tasks = [
                        self._execute_single(request)
                        for request in requests
                    ]
                    
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Convert exceptions to results
                    final_results = []
                    for i, result in enumerate(results):
                        if isinstance(result, Exception):
                            final_results.append(BatchToolResult(
                                request_id=requests[i].request_id,
                                tool_name=requests[i].tool.name,
                                success=False,
                                error=str(result)
                            ))
                        else:
                            final_results.append(result)
                    
                    results = final_results
                
                # Calculate batch metrics
                duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
                successful = sum(1 for r in results if r.success)
                failed = len(results) - successful
                
                metrics.metadata["successful"] = successful
                metrics.metadata["failed"] = failed
                metrics.metadata["cache_hits"] = sum(
                    1 for r in results if r.duration_ms == 0
                )
                
                performance_logger.log_batch_operation(
                    operation_type="batch_tools",
                    batch_size=len(requests),
                    successful=successful,
                    failed=failed,
                    duration_ms=duration_ms,
                    metadata={
                        "batch_id": batch_id,
                        "fail_fast": fail_fast,
                        "tools": list(set(r.tool.name for r in requests))
                    }
                )
                
                return results
                
            except Exception as e:
                metrics.metadata["batch_error"] = str(e)
                raise
    
    async def execute_parallel_groups(
        self,
        groups: List[List[BatchToolRequest]],
        group_delay: float = 0.0
    ) -> List[List[BatchToolResult]]:
        """
        Execute groups of tools in sequence, with parallelism within groups.
        
        Args:
            groups: List of request groups
            group_delay: Delay between groups
            
        Returns:
            List of result groups
        """
        all_results = []
        
        for i, group in enumerate(groups):
            if i > 0 and group_delay > 0:
                await asyncio.sleep(group_delay)
            
            # Execute group in parallel
            group_results = await self.execute_batch(group)
            all_results.append(group_results)
        
        return all_results
    
    def clear_cache(self):
        """Clear the result cache."""
        self._cache.clear()
        performance_logger.log_custom(
            "batch_executor_cache_cleared",
            timestamp=datetime.utcnow().isoformat()
        )
    
    async def execute_with_dependencies(
        self,
        requests: List[BatchToolRequest],
        dependencies: Dict[str, List[str]]
    ) -> Dict[str, BatchToolResult]:
        """
        Execute tools respecting dependencies.
        
        Args:
            requests: List of tool requests
            dependencies: Map of request_id to list of dependency request_ids
            
        Returns:
            Dictionary mapping request_id to result
        """
        # Build request map
        request_map = {r.request_id: r for r in requests}
        results: Dict[str, BatchToolResult] = {}
        
        # Topological sort for execution order
        visited = set()
        temp_mark = set()
        order = []
        
        def visit(request_id: str):
            if request_id in temp_mark:
                raise ValueError(f"Circular dependency detected: {request_id}")
            if request_id in visited:
                return
            
            temp_mark.add(request_id)
            
            # Visit dependencies first
            for dep_id in dependencies.get(request_id, []):
                visit(dep_id)
            
            temp_mark.remove(request_id)
            visited.add(request_id)
            order.append(request_id)
        
        # Visit all nodes
        for request_id in request_map:
            if request_id not in visited:
                visit(request_id)
        
        # Execute in dependency order
        for request_id in order:
            request = request_map[request_id]
            
            # Check if dependencies succeeded
            deps_failed = False
            for dep_id in dependencies.get(request_id, []):
                if dep_id in results and not results[dep_id].success:
                    deps_failed = True
                    break
            
            if deps_failed:
                # Skip if dependencies failed
                results[request_id] = BatchToolResult(
                    request_id=request_id,
                    tool_name=request.tool.name,
                    success=False,
                    error="Dependencies failed"
                )
            else:
                # Execute tool
                result = await self._execute_single(request)
                results[request_id] = result
        
        return results


# Global batch executor instance
batch_executor = BatchToolExecutor()