"""Rate limit manager with monitoring and exponential backoff."""

import asyncio
import time
from typing import Dict, Optional, List, Tuple, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import structlog
import random

from app.services.metrics import metrics_collector

# Initialize structured logger
logger = structlog.get_logger(__name__)


class RateLimitType(str, Enum):
    """Types of rate limits."""
    REQUESTS_PER_MINUTE = "requests_per_minute"
    REQUESTS_PER_HOUR = "requests_per_hour"
    TOKENS_PER_MINUTE = "tokens_per_minute"
    TOKENS_PER_HOUR = "tokens_per_hour"
    CONCURRENT_REQUESTS = "concurrent_requests"


class RateLimitStatus:
    """Status of a rate limit."""
    
    def __init__(
        self,
        limit_type: RateLimitType,
        limit: int,
        used: int,
        reset_at: datetime,
        is_exceeded: bool = False,
        retry_after: Optional[float] = None
    ):
        self.limit_type = limit_type
        self.limit = limit
        self.used = used
        self.reset_at = reset_at
        self.is_exceeded = is_exceeded
        self.retry_after = retry_after
    
    @property
    def remaining(self) -> int:
        """Get remaining capacity."""
        return max(0, self.limit - self.used)
    
    @property
    def usage_percent(self) -> float:
        """Get usage percentage."""
        return (self.used / self.limit * 100) if self.limit > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "limit_type": self.limit_type.value,
            "limit": self.limit,
            "used": self.used,
            "remaining": self.remaining,
            "usage_percent": round(self.usage_percent, 2),
            "reset_at": self.reset_at.isoformat(),
            "is_exceeded": self.is_exceeded,
            "retry_after": self.retry_after,
        }


class RateLimitManager:
    """Manage rate limits with monitoring and backoff."""
    
    # Default rate limits per model (can be overridden)
    DEFAULT_LIMITS = {
        "google/gemini-2.0-flash": {
            RateLimitType.REQUESTS_PER_MINUTE: 300,
            RateLimitType.TOKENS_PER_MINUTE: 4000000,
            RateLimitType.CONCURRENT_REQUESTS: 50,
        },
        "openai/gpt-4o": {
            RateLimitType.REQUESTS_PER_MINUTE: 500,
            RateLimitType.TOKENS_PER_MINUTE: 800000,
            RateLimitType.CONCURRENT_REQUESTS: 100,
        },
        "anthropic/claude-3.5-sonnet": {
            RateLimitType.REQUESTS_PER_MINUTE: 50,
            RateLimitType.TOKENS_PER_MINUTE: 400000,
            RateLimitType.CONCURRENT_REQUESTS: 50,
        },
    }
    
    # Default fallback limits
    FALLBACK_LIMITS = {
        RateLimitType.REQUESTS_PER_MINUTE: 60,
        RateLimitType.TOKENS_PER_MINUTE: 100000,
        RateLimitType.CONCURRENT_REQUESTS: 10,
    }
    
    def __init__(self):
        """Initialize the rate limit manager."""
        # Track usage per model and limit type
        self._usage: Dict[str, Dict[RateLimitType, deque]] = defaultdict(
            lambda: defaultdict(lambda: deque(maxlen=10000))
        )
        
        # Track concurrent requests
        self._concurrent: Dict[str, int] = defaultdict(int)
        
        # Track backoff state
        self._backoff_until: Dict[str, datetime] = {}
        self._consecutive_failures: Dict[str, int] = defaultdict(int)
        
        # Model-specific rate limits
        self._model_limits: Dict[str, Dict[RateLimitType, int]] = {}
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    def set_model_limits(
        self,
        model: str,
        limits: Dict[RateLimitType, int]
    ):
        """
        Set custom rate limits for a model.
        
        Args:
            model: Model ID
            limits: Dictionary of rate limit types to limits
        """
        self._model_limits[model] = limits
        logger.info(
            "Set custom rate limits",
            model=model,
            limits={k.value: v for k, v in limits.items()}
        )
    
    def _get_limits(self, model: str) -> Dict[RateLimitType, int]:
        """Get rate limits for a model."""
        # Check custom limits first
        if model in self._model_limits:
            return self._model_limits[model]
        
        # Check default limits
        if model in self.DEFAULT_LIMITS:
            return self.DEFAULT_LIMITS[model]
        
        # Use fallback limits
        return self.FALLBACK_LIMITS
    
    def _clean_old_usage(
        self,
        usage_deque: deque,
        window: timedelta
    ):
        """Remove old usage entries outside the window."""
        cutoff = datetime.utcnow() - window
        while usage_deque and usage_deque[0][0] < cutoff:
            usage_deque.popleft()
    
    async def check_rate_limit(
        self,
        model: str,
        tokens: Optional[int] = None
    ) -> List[RateLimitStatus]:
        """
        Check if request would exceed rate limits.
        
        Args:
            model: Model ID
            tokens: Number of tokens (for token-based limits)
            
        Returns:
            List of rate limit statuses
        """
        async with self._lock:
            now = datetime.utcnow()
            limits = self._get_limits(model)
            statuses = []
            
            # Check if in backoff period
            if model in self._backoff_until and self._backoff_until[model] > now:
                retry_after = (self._backoff_until[model] - now).total_seconds()
                for limit_type in limits:
                    statuses.append(RateLimitStatus(
                        limit_type=limit_type,
                        limit=limits[limit_type],
                        used=0,
                        reset_at=self._backoff_until[model],
                        is_exceeded=True,
                        retry_after=retry_after
                    ))
                return statuses
            
            # Check requests per minute
            if RateLimitType.REQUESTS_PER_MINUTE in limits:
                limit = limits[RateLimitType.REQUESTS_PER_MINUTE]
                usage_deque = self._usage[model][RateLimitType.REQUESTS_PER_MINUTE]
                
                # Clean old entries
                self._clean_old_usage(usage_deque, timedelta(minutes=1))
                
                used = len(usage_deque)
                reset_at = now + timedelta(minutes=1)
                
                statuses.append(RateLimitStatus(
                    limit_type=RateLimitType.REQUESTS_PER_MINUTE,
                    limit=limit,
                    used=used,
                    reset_at=reset_at,
                    is_exceeded=used >= limit
                ))
            
            # Check tokens per minute
            if tokens and RateLimitType.TOKENS_PER_MINUTE in limits:
                limit = limits[RateLimitType.TOKENS_PER_MINUTE]
                usage_deque = self._usage[model][RateLimitType.TOKENS_PER_MINUTE]
                
                # Clean old entries
                self._clean_old_usage(usage_deque, timedelta(minutes=1))
                
                # Sum tokens in window
                used = sum(entry[1] for entry in usage_deque)
                reset_at = now + timedelta(minutes=1)
                
                statuses.append(RateLimitStatus(
                    limit_type=RateLimitType.TOKENS_PER_MINUTE,
                    limit=limit,
                    used=used,
                    reset_at=reset_at,
                    is_exceeded=(used + tokens) > limit
                ))
            
            # Check concurrent requests
            if RateLimitType.CONCURRENT_REQUESTS in limits:
                limit = limits[RateLimitType.CONCURRENT_REQUESTS]
                used = self._concurrent[model]
                
                statuses.append(RateLimitStatus(
                    limit_type=RateLimitType.CONCURRENT_REQUESTS,
                    limit=limit,
                    used=used,
                    reset_at=now,  # No reset time for concurrent
                    is_exceeded=used >= limit
                ))
            
            return statuses
    
    async def acquire(
        self,
        model: str,
        tokens: Optional[int] = None,
        wait: bool = True,
        max_wait: float = 60.0
    ) -> bool:
        """
        Acquire rate limit capacity.
        
        Args:
            model: Model ID
            tokens: Number of tokens
            wait: Whether to wait if rate limited
            max_wait: Maximum time to wait in seconds
            
        Returns:
            True if acquired, False if rate limited
        """
        start_time = time.time()
        
        while True:
            statuses = await self.check_rate_limit(model, tokens)
            
            # Check if any limit is exceeded
            exceeded_statuses = [s for s in statuses if s.is_exceeded]
            
            if not exceeded_statuses:
                # No limits exceeded, acquire capacity
                async with self._lock:
                    now = datetime.utcnow()
                    
                    # Record request
                    self._usage[model][RateLimitType.REQUESTS_PER_MINUTE].append(
                        (now, 1)
                    )
                    
                    # Record tokens if provided
                    if tokens:
                        self._usage[model][RateLimitType.TOKENS_PER_MINUTE].append(
                            (now, tokens)
                        )
                    
                    # Increment concurrent
                    self._concurrent[model] += 1
                
                # Reset consecutive failures on success
                self._consecutive_failures[model] = 0
                
                return True
            
            # Rate limited
            if not wait:
                # Record rate limit hit
                for status in exceeded_statuses:
                    await metrics_collector.record_rate_limit(
                        model=model,
                        limit_type=status.limit_type.value,
                        retry_after=status.retry_after
                    )
                
                return False
            
            # Calculate wait time
            wait_time = self._calculate_wait_time(model, exceeded_statuses)
            
            # Check if we've waited too long
            if time.time() - start_time + wait_time > max_wait:
                logger.warning(
                    "Rate limit wait exceeded maximum",
                    model=model,
                    max_wait=max_wait,
                    wait_time=wait_time
                )
                return False
            
            # Log and wait
            logger.info(
                "Rate limited, waiting",
                model=model,
                wait_time=wait_time,
                exceeded=[s.limit_type.value for s in exceeded_statuses]
            )
            
            await asyncio.sleep(wait_time)
    
    def _calculate_wait_time(
        self,
        model: str,
        exceeded_statuses: List[RateLimitStatus]
    ) -> float:
        """Calculate wait time with exponential backoff."""
        # Get the longest retry_after from statuses
        max_retry_after = max(
            (s.retry_after for s in exceeded_statuses if s.retry_after),
            default=1.0
        )
        
        # Apply exponential backoff based on consecutive failures
        failures = self._consecutive_failures[model]
        base_wait = max_retry_after
        
        # Exponential backoff: 2^failures * base_wait
        # Cap at 2^6 = 64x to prevent excessive waits
        backoff_multiplier = min(2 ** failures, 64)
        wait_time = base_wait * backoff_multiplier
        
        # Add jitter to prevent thundering herd
        jitter = random.uniform(0, 0.1 * wait_time)
        wait_time += jitter
        
        # Cap maximum wait time
        wait_time = min(wait_time, 300.0)  # 5 minutes max
        
        # Increment consecutive failures
        self._consecutive_failures[model] += 1
        
        return wait_time
    
    async def release(self, model: str):
        """
        Release concurrent request capacity.
        
        Args:
            model: Model ID
        """
        async with self._lock:
            if model in self._concurrent and self._concurrent[model] > 0:
                self._concurrent[model] -= 1
    
    async def report_rate_limit_error(
        self,
        model: str,
        retry_after: Optional[float] = None,
        limit_type: Optional[str] = None
    ):
        """
        Report a rate limit error from the API.
        
        Args:
            model: Model ID
            retry_after: Seconds to retry after
            limit_type: Type of limit hit
        """
        async with self._lock:
            now = datetime.utcnow()
            
            # Set backoff period
            if retry_after:
                self._backoff_until[model] = now + timedelta(seconds=retry_after)
            else:
                # Default backoff of 60 seconds
                self._backoff_until[model] = now + timedelta(seconds=60)
            
            # Increment consecutive failures
            self._consecutive_failures[model] += 1
        
        # Record metric
        await metrics_collector.record_rate_limit(
            model=model,
            limit_type=limit_type or "unknown",
            retry_after=retry_after
        )
        
        logger.warning(
            "Rate limit error reported",
            model=model,
            retry_after=retry_after,
            limit_type=limit_type,
            consecutive_failures=self._consecutive_failures[model]
        )
    
    async def get_status(
        self,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get current rate limit status.
        
        Args:
            model: Optional specific model to check
            
        Returns:
            Dictionary with rate limit status
        """
        async with self._lock:
            if model:
                models = [model]
            else:
                # Get all models with usage
                models = list(set(
                    list(self._usage.keys()) +
                    list(self._concurrent.keys()) +
                    list(self._backoff_until.keys())
                ))
            
            status = {}
            
            for m in models:
                statuses = await self.check_rate_limit(m)
                
                model_status = {
                    "limits": [s.to_dict() for s in statuses],
                    "concurrent_requests": self._concurrent.get(m, 0),
                    "consecutive_failures": self._consecutive_failures.get(m, 0),
                    "in_backoff": m in self._backoff_until and self._backoff_until[m] > datetime.utcnow(),
                }
                
                if model_status["in_backoff"]:
                    model_status["backoff_until"] = self._backoff_until[m].isoformat()
                    model_status["backoff_seconds_remaining"] = max(
                        0,
                        (self._backoff_until[m] - datetime.utcnow()).total_seconds()
                    )
                
                status[m] = model_status
            
            return status
    
    async def reset_model_limits(self, model: str):
        """
        Reset rate limits for a model (admin only).
        
        Args:
            model: Model ID
        """
        async with self._lock:
            # Clear usage history
            if model in self._usage:
                for limit_type in self._usage[model]:
                    self._usage[model][limit_type].clear()
            
            # Clear concurrent count
            self._concurrent[model] = 0
            
            # Clear backoff
            self._backoff_until.pop(model, None)
            self._consecutive_failures[model] = 0
        
        logger.info("Rate limits reset", model=model)


# Global rate limit manager instance
rate_limit_manager = RateLimitManager()