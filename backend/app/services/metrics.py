"""AI metrics collection service for performance tracking and monitoring."""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from contextlib import asynccontextmanager

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import structlog

from app.core.config import settings

# Initialize structured logger
logger = structlog.get_logger(__name__)

# Prometheus metrics registry
registry = CollectorRegistry()

# Metrics definitions
ai_request_count = Counter(
    "ai_request_total",
    "Total number of AI requests",
    ["agent", "model", "status"],
    registry=registry
)

ai_request_duration = Histogram(
    "ai_request_duration_seconds",
    "AI request duration in seconds",
    ["agent", "model"],
    registry=registry
)

ai_token_usage = Counter(
    "ai_token_usage_total",
    "Total token usage",
    ["agent", "model", "token_type"],  # token_type: input, output
    registry=registry
)

ai_cost_total = Counter(
    "ai_cost_total_dollars",
    "Total cost in dollars",
    ["agent", "model"],
    registry=registry
)

ai_error_count = Counter(
    "ai_error_total",
    "Total number of AI errors",
    ["agent", "model", "error_type"],
    registry=registry
)

ai_rate_limit_hits = Counter(
    "ai_rate_limit_hits_total",
    "Number of rate limit hits",
    ["model", "limit_type"],  # limit_type: requests_per_minute, tokens_per_minute
    registry=registry
)

ai_active_requests = Gauge(
    "ai_active_requests",
    "Number of active AI requests",
    ["agent", "model"],
    registry=registry
)

ai_cache_hits = Counter(
    "ai_cache_hits_total",
    "Number of cache hits",
    ["agent", "query_type"],
    registry=registry
)

ai_cache_misses = Counter(
    "ai_cache_misses_total",
    "Number of cache misses",
    ["agent", "query_type"],
    registry=registry
)


class AIMetricsCollector:
    """Collector for AI-related metrics."""
    
    def __init__(self):
        """Initialize the metrics collector."""
        self.enabled = settings.ENABLE_METRICS
        self._request_times: Dict[str, float] = {}
        self._rate_limit_tracker: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()
        
        # In-memory metrics storage for quick access
        self._metrics_buffer = {
            "requests": defaultdict(lambda: defaultdict(int)),
            "tokens": defaultdict(lambda: defaultdict(int)),
            "costs": defaultdict(lambda: defaultdict(float)),
            "errors": defaultdict(lambda: defaultdict(int)),
            "rate_limits": defaultdict(lambda: defaultdict(int)),
            "durations": defaultdict(list),
        }
    
    @asynccontextmanager
    async def track_request(
        self,
        agent: str,
        model: str,
        request_id: Optional[str] = None
    ):
        """
        Context manager to track AI request metrics.
        
        Args:
            agent: Name of the agent making the request
            model: Model being used
            request_id: Optional request ID for tracking
            
        Yields:
            Request tracking context
        """
        if not self.enabled:
            yield
            return
        
        # Generate request ID if not provided
        if request_id is None:
            request_id = f"{agent}_{model}_{int(time.time() * 1000)}"
        
        # Track active requests
        ai_active_requests.labels(agent=agent, model=model).inc()
        
        # Record start time
        start_time = time.time()
        self._request_times[request_id] = start_time
        
        try:
            yield request_id
            
            # Record successful request
            ai_request_count.labels(agent=agent, model=model, status="success").inc()
            
        except Exception as e:
            # Record failed request
            ai_request_count.labels(agent=agent, model=model, status="error").inc()
            
            # Track error type
            error_type = type(e).__name__
            ai_error_count.labels(agent=agent, model=model, error_type=error_type).inc()
            
            # Log error
            logger.error(
                "AI request failed",
                agent=agent,
                model=model,
                error_type=error_type,
                error=str(e),
                request_id=request_id
            )
            
            # Re-raise the exception
            raise
            
        finally:
            # Calculate duration
            duration = time.time() - start_time
            ai_request_duration.labels(agent=agent, model=model).observe(duration)
            
            # Update active requests
            ai_active_requests.labels(agent=agent, model=model).dec()
            
            # Store in buffer
            async with self._lock:
                self._metrics_buffer["durations"][f"{agent}_{model}"].append(duration)
                
                # Keep only last 1000 durations per agent/model
                if len(self._metrics_buffer["durations"][f"{agent}_{model}"]) > 1000:
                    self._metrics_buffer["durations"][f"{agent}_{model}"] = \
                        self._metrics_buffer["durations"][f"{agent}_{model}"][-1000:]
            
            # Clean up request time
            self._request_times.pop(request_id, None)
    
    async def record_token_usage(
        self,
        agent: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: Optional[float] = None
    ):
        """
        Record token usage and cost.
        
        Args:
            agent: Name of the agent
            model: Model being used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost: Optional cost in dollars
        """
        if not self.enabled:
            return
        
        # Record token usage
        ai_token_usage.labels(agent=agent, model=model, token_type="input").inc(input_tokens)
        ai_token_usage.labels(agent=agent, model=model, token_type="output").inc(output_tokens)
        
        # Record cost if provided
        if cost is not None:
            ai_cost_total.labels(agent=agent, model=model).inc(cost)
        
        # Update buffer
        async with self._lock:
            key = f"{agent}_{model}"
            self._metrics_buffer["tokens"][key]["input"] += input_tokens
            self._metrics_buffer["tokens"][key]["output"] += output_tokens
            if cost is not None:
                self._metrics_buffer["costs"][key]["total"] += cost
        
        # Log metrics
        logger.info(
            "Token usage recorded",
            agent=agent,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost=cost
        )
    
    async def record_rate_limit(
        self,
        model: str,
        limit_type: str = "requests_per_minute",
        retry_after: Optional[int] = None
    ):
        """
        Record rate limit hit.
        
        Args:
            model: Model that hit rate limit
            limit_type: Type of limit hit
            retry_after: Seconds to retry after
        """
        if not self.enabled:
            return
        
        # Record rate limit hit
        ai_rate_limit_hits.labels(model=model, limit_type=limit_type).inc()
        
        # Track rate limit occurrence
        async with self._lock:
            self._rate_limit_tracker[model].append(time.time())
            
            # Keep only last hour of rate limit hits
            cutoff = time.time() - 3600
            self._rate_limit_tracker[model] = [
                t for t in self._rate_limit_tracker[model] if t > cutoff
            ]
            
            self._metrics_buffer["rate_limits"][model][limit_type] += 1
        
        # Log rate limit
        logger.warning(
            "Rate limit hit",
            model=model,
            limit_type=limit_type,
            retry_after=retry_after,
            recent_hits=len(self._rate_limit_tracker[model])
        )
    
    async def record_cache_access(
        self,
        agent: str,
        query_type: str,
        hit: bool
    ):
        """
        Record cache access.
        
        Args:
            agent: Name of the agent
            query_type: Type of query
            hit: Whether it was a cache hit
        """
        if not self.enabled:
            return
        
        if hit:
            ai_cache_hits.labels(agent=agent, query_type=query_type).inc()
        else:
            ai_cache_misses.labels(agent=agent, query_type=query_type).inc()
    
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of collected metrics.
        
        Returns:
            Dictionary containing metrics summary
        """
        async with self._lock:
            summary = {
                "timestamp": datetime.utcnow().isoformat(),
                "agents": {},
                "models": {},
                "rate_limits": {},
                "overall": {
                    "total_requests": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "total_errors": 0,
                    "average_duration": 0.0,
                }
            }
            
            # Process metrics by agent
            for key, durations in self._metrics_buffer["durations"].items():
                agent, model = key.rsplit("_", 1)
                
                if agent not in summary["agents"]:
                    summary["agents"][agent] = {
                        "requests": 0,
                        "tokens": {"input": 0, "output": 0},
                        "cost": 0.0,
                        "errors": 0,
                        "average_duration": 0.0,
                    }
                
                if model not in summary["models"]:
                    summary["models"][model] = {
                        "requests": 0,
                        "tokens": {"input": 0, "output": 0},
                        "cost": 0.0,
                        "errors": 0,
                        "average_duration": 0.0,
                        "rate_limit_hits": 0,
                    }
                
                # Calculate average duration
                avg_duration = sum(durations) / len(durations) if durations else 0.0
                
                # Update agent metrics
                summary["agents"][agent]["requests"] = len(durations)
                summary["agents"][agent]["average_duration"] = avg_duration
                
                # Update model metrics
                summary["models"][model]["requests"] += len(durations)
                if summary["models"][model]["average_duration"] == 0:
                    summary["models"][model]["average_duration"] = avg_duration
                else:
                    # Running average
                    summary["models"][model]["average_duration"] = \
                        (summary["models"][model]["average_duration"] + avg_duration) / 2
            
            # Add token and cost data
            for key, tokens in self._metrics_buffer["tokens"].items():
                agent, model = key.rsplit("_", 1)
                
                if agent in summary["agents"]:
                    summary["agents"][agent]["tokens"]["input"] = tokens.get("input", 0)
                    summary["agents"][agent]["tokens"]["output"] = tokens.get("output", 0)
                
                if model in summary["models"]:
                    summary["models"][model]["tokens"]["input"] += tokens.get("input", 0)
                    summary["models"][model]["tokens"]["output"] += tokens.get("output", 0)
                
                # Update overall metrics
                summary["overall"]["total_tokens"] += tokens.get("input", 0) + tokens.get("output", 0)
            
            # Add cost data
            for key, costs in self._metrics_buffer["costs"].items():
                agent, model = key.rsplit("_", 1)
                
                cost = costs.get("total", 0.0)
                if agent in summary["agents"]:
                    summary["agents"][agent]["cost"] = cost
                
                if model in summary["models"]:
                    summary["models"][model]["cost"] += cost
                
                summary["overall"]["total_cost"] += cost
            
            # Add rate limit data
            for model, limits in self._metrics_buffer["rate_limits"].items():
                total_hits = sum(limits.values())
                if model in summary["models"]:
                    summary["models"][model]["rate_limit_hits"] = total_hits
                
                summary["rate_limits"][model] = {
                    "total_hits": total_hits,
                    "by_type": dict(limits),
                    "recent_hits": len(self._rate_limit_tracker.get(model, [])),
                }
            
            # Calculate overall metrics
            all_durations = []
            for durations in self._metrics_buffer["durations"].values():
                all_durations.extend(durations)
            
            if all_durations:
                summary["overall"]["average_duration"] = sum(all_durations) / len(all_durations)
                summary["overall"]["total_requests"] = len(all_durations)
            
            return summary
    
    async def get_agent_metrics(self, agent: str) -> Dict[str, Any]:
        """
        Get metrics for a specific agent.
        
        Args:
            agent: Name of the agent
            
        Returns:
            Dictionary containing agent metrics
        """
        summary = await self.get_metrics_summary()
        return summary["agents"].get(agent, {})
    
    async def get_model_metrics(self, model: str) -> Dict[str, Any]:
        """
        Get metrics for a specific model.
        
        Args:
            model: Name of the model
            
        Returns:
            Dictionary containing model metrics
        """
        summary = await self.get_metrics_summary()
        return summary["models"].get(model, {})
    
    async def reset_metrics(self):
        """Reset all metrics (admin only)."""
        async with self._lock:
            self._metrics_buffer = {
                "requests": defaultdict(lambda: defaultdict(int)),
                "tokens": defaultdict(lambda: defaultdict(int)),
                "costs": defaultdict(lambda: defaultdict(float)),
                "errors": defaultdict(lambda: defaultdict(int)),
                "rate_limits": defaultdict(lambda: defaultdict(int)),
                "durations": defaultdict(list),
            }
            self._rate_limit_tracker.clear()
        
        logger.info("Metrics reset")


# Global metrics collector instance
metrics_collector = AIMetricsCollector()