"""Dynamic cost calculator for OpenRouter pricing."""

from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import asyncio
import httpx
import structlog

from app.core.config import settings

# Initialize structured logger
logger = structlog.get_logger(__name__)


class CostCalculator:
    """Calculate costs for OpenRouter model usage dynamically."""
    
    # Cache duration for pricing data
    CACHE_DURATION = timedelta(hours=1)
    
    # OpenRouter pricing endpoint
    PRICING_ENDPOINT = f"{settings.OPENROUTER_BASE_URL}/models"
    
    def __init__(self):
        """Initialize the cost calculator."""
        self._pricing_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_timestamp: Optional[datetime] = None
        self._lock = asyncio.Lock()
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "User-Agent": "OptimizeDeFi/1.0",
                },
                timeout=30.0
            )
        return self._http_client
    
    async def _fetch_pricing_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Fetch current pricing data from OpenRouter.
        
        Returns:
            Dictionary mapping model IDs to pricing info
        """
        try:
            client = await self._get_http_client()
            response = await client.get(self.PRICING_ENDPOINT)
            response.raise_for_status()
            
            data = response.json()
            pricing_data = {}
            
            # Parse model data
            for model in data.get("data", []):
                model_id = model.get("id")
                if model_id:
                    pricing_data[model_id] = {
                        "name": model.get("name", model_id),
                        "context_length": model.get("context_length", 0),
                        "pricing": model.get("pricing", {}),
                        "per_request_limits": model.get("per_request_limits", {}),
                        "architecture": model.get("architecture", {}),
                        "updated_at": datetime.utcnow().isoformat(),
                    }
            
            logger.info(
                "Fetched pricing data",
                models_count=len(pricing_data),
                timestamp=datetime.utcnow().isoformat()
            )
            
            return pricing_data
            
        except Exception as e:
            logger.error(
                "Failed to fetch pricing data",
                error=str(e),
                error_type=type(e).__name__
            )
            # Return empty dict on error
            return {}
    
    async def _ensure_pricing_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Ensure pricing data is available and fresh.
        
        Returns:
            Current pricing data
        """
        async with self._lock:
            # Check if cache is valid
            if (
                self._cache_timestamp and
                self._pricing_cache and
                datetime.utcnow() - self._cache_timestamp < self.CACHE_DURATION
            ):
                return self._pricing_cache
            
            # Fetch new pricing data
            pricing_data = await self._fetch_pricing_data()
            
            if pricing_data:
                # Update cache
                self._pricing_cache = pricing_data
                self._cache_timestamp = datetime.utcnow()
            elif not self._pricing_cache:
                # If fetch failed and no cache, use fallback
                self._pricing_cache = self._get_fallback_pricing()
                self._cache_timestamp = datetime.utcnow()
            
            return self._pricing_cache
    
    def _get_fallback_pricing(self) -> Dict[str, Dict[str, Any]]:
        """
        Get fallback pricing data for common models.
        
        Returns:
            Fallback pricing data
        """
        # Fallback pricing as of late 2024
        return {
            "google/gemini-2.0-flash": {
                "name": "Gemini 2.0 Flash",
                "context_length": 32768,
                "pricing": {
                    "prompt": "0.00000025",  # $0.25 per 1M tokens
                    "completion": "0.00000100",  # $1.00 per 1M tokens
                },
                "updated_at": datetime.utcnow().isoformat(),
            },
            "openai/gpt-4o": {
                "name": "GPT-4o",
                "context_length": 128000,
                "pricing": {
                    "prompt": "0.000005",  # $5.00 per 1M tokens
                    "completion": "0.000015",  # $15.00 per 1M tokens
                },
                "updated_at": datetime.utcnow().isoformat(),
            },
            "anthropic/claude-3.5-sonnet": {
                "name": "Claude 3.5 Sonnet",
                "context_length": 200000,
                "pricing": {
                    "prompt": "0.000003",  # $3.00 per 1M tokens
                    "completion": "0.000015",  # $15.00 per 1M tokens
                },
                "updated_at": datetime.utcnow().isoformat(),
            },
            "meta-llama/llama-3.3-70b": {
                "name": "Llama 3.3 70B",
                "context_length": 131072,
                "pricing": {
                    "prompt": "0.00000035",  # $0.35 per 1M tokens
                    "completion": "0.00000040",  # $0.40 per 1M tokens
                },
                "updated_at": datetime.utcnow().isoformat(),
            },
        }
    
    async def calculate_cost(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate cost for token usage.
        
        Args:
            model: Model ID
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Tuple of (total_cost, pricing_details)
        """
        # Get pricing data
        pricing_data = await self._ensure_pricing_data()
        
        # Get model pricing
        model_data = pricing_data.get(model, {})
        pricing = model_data.get("pricing", {})
        
        # Extract prices (handle different formats)
        prompt_price = float(pricing.get("prompt", 0))
        completion_price = float(pricing.get("completion", 0))
        
        # Calculate costs (prices are per token)
        input_cost = input_tokens * prompt_price
        output_cost = output_tokens * completion_price
        total_cost = input_cost + output_cost
        
        # Prepare pricing details
        pricing_details = {
            "model": model,
            "model_name": model_data.get("name", model),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6),
            "pricing": {
                "prompt_per_1k": round(prompt_price * 1000, 6),
                "completion_per_1k": round(completion_price * 1000, 6),
            },
            "context_length": model_data.get("context_length", 0),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Log if model pricing not found
        if not pricing:
            logger.warning(
                "Model pricing not found, using zero cost",
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
        
        return total_cost, pricing_details
    
    async def estimate_cost(
        self,
        model: str,
        estimated_input_tokens: int,
        estimated_output_tokens: int
    ) -> Dict[str, Any]:
        """
        Estimate cost before making a request.
        
        Args:
            model: Model ID
            estimated_input_tokens: Estimated input tokens
            estimated_output_tokens: Estimated output tokens
            
        Returns:
            Cost estimate details
        """
        total_cost, pricing_details = await self.calculate_cost(
            model,
            estimated_input_tokens,
            estimated_output_tokens
        )
        
        # Add estimate flag
        pricing_details["is_estimate"] = True
        
        return pricing_details
    
    async def get_model_info(self, model: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific model.
        
        Args:
            model: Model ID
            
        Returns:
            Model information or None if not found
        """
        pricing_data = await self._ensure_pricing_data()
        return pricing_data.get(model)
    
    async def get_all_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all available models.
        
        Returns:
            Dictionary of all models and their info
        """
        return await self._ensure_pricing_data()
    
    async def get_cheapest_model(
        self,
        min_context_length: Optional[int] = None
    ) -> Optional[str]:
        """
        Get the cheapest model that meets requirements.
        
        Args:
            min_context_length: Minimum required context length
            
        Returns:
            Model ID of cheapest model or None
        """
        pricing_data = await self._ensure_pricing_data()
        
        cheapest_model = None
        cheapest_avg_price = float('inf')
        
        for model_id, model_data in pricing_data.items():
            # Check context length requirement
            if min_context_length:
                context_length = model_data.get("context_length", 0)
                if context_length < min_context_length:
                    continue
            
            # Calculate average price
            pricing = model_data.get("pricing", {})
            prompt_price = float(pricing.get("prompt", 0))
            completion_price = float(pricing.get("completion", 0))
            
            # Average of input and output prices
            avg_price = (prompt_price + completion_price) / 2
            
            if avg_price < cheapest_avg_price and avg_price > 0:
                cheapest_avg_price = avg_price
                cheapest_model = model_id
        
        return cheapest_model
    
    async def cleanup(self):
        """Clean up resources."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None


# Global cost calculator instance
cost_calculator = CostCalculator()