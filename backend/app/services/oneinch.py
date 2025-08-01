"""1inch API integration service."""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import aiohttp
from decimal import Decimal
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class OneInchAPIError(Exception):
    """Custom exception for 1inch API errors."""
    pass


class RateLimitError(OneInchAPIError):
    """Exception for rate limit errors."""
    pass


async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 30.0
):
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        backoff_factor: Factor to multiply delay by after each retry
        max_delay: Maximum delay between retries
        
    Returns:
        Result from the function
        
    Raises:
        Exception from the last retry attempt
    """
    delay = initial_delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except aiohttp.ClientError as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(
                    f"Request failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}. "
                    f"Retrying in {delay:.1f}s..."
                )
                await asyncio.sleep(delay)
                delay = min(delay * backoff_factor, max_delay)
            else:
                logger.error(f"Request failed after {max_retries + 1} attempts: {str(e)}")
        except Exception as e:
            # Don't retry on non-network errors
            logger.error(f"Non-retryable error: {str(e)}")
            raise
    
    raise last_exception


class OneInchService:
    """Service for interacting with 1inch APIs."""
    
    def __init__(self, max_retries: int = 3, initial_delay: float = 1.0):
        self.base_url = "https://api.1inch.dev"
        self.api_key = settings.ONEINCH_API_KEY
        self.session: Optional[aiohttp.ClientSession] = None
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        
        # Chain configurations - only mainnet chains supported by 1inch
        self.chain_configs = {
            1: {"name": "Ethereum", "native": "ETH"},
            137: {"name": "Polygon", "native": "MATIC"},
            10: {"name": "Optimism", "native": "ETH"},
            42161: {"name": "Arbitrum", "native": "ETH"},
            56: {"name": "BSC", "native": "BNB"},
            43114: {"name": "Avalanche", "native": "AVAX"},
            8453: {"name": "Base", "native": "ETH"},
        }
        
        # Testnet chain IDs (not supported by 1inch)
        self.testnet_chains = {11155111, 80001, 420, 421613}  # Sepolia, Mumbai, Optimism Goerli, Arbitrum Goerli
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        retry: bool = True
    ) -> Dict[str, Any]:
        """Make an API request to 1inch with retry logic."""
        if not self.session:
            raise OneInchAPIError("Session not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        
        async def _request():
            async with self.session.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                params=params,
                json=data
            ) as response:
                if response.status == 429:
                    # Rate limited
                    retry_after = response.headers.get('Retry-After', '60')
                    logger.warning(f"Rate limited. Retry after: {retry_after}s")
                    raise RateLimitError(f"Rate limited. Retry after: {retry_after}s")
                
                if response.status != 200:
                    error_text = await response.text()
                    error_msg = f"API request failed: {response.status} - {error_text}"
                    logger.error(f"{method} {endpoint}: {error_msg}")
                    
                    # Don't retry on client errors (4xx) except rate limiting
                    if 400 <= response.status < 500:
                        raise OneInchAPIError(error_msg)
                    
                    # Server errors (5xx) should be retried
                    raise aiohttp.ClientError(error_msg)
                
                return await response.json()
        
        if retry:
            try:
                return await retry_with_backoff(_request)
            except RateLimitError:
                # Don't retry rate limit errors
                raise
        else:
            return await _request()
    
    async def get_wallet_balances(
        self,
        wallet_address: str,
        chain_id: int
    ) -> Dict[str, Any]:
        """
        Get token balances for a wallet on a specific chain.
        
        Args:
            wallet_address: Ethereum wallet address
            chain_id: Chain ID (1, 137, 10, 42161, etc.)
            
        Returns:
            Dictionary of token balances
        """
        # Updated to use the Balance API v2 endpoint
        endpoint = f"/balance/v2/{chain_id}/balances/{wallet_address}"
        params = {}
        
        logger.info(f"Fetching balances for {wallet_address} on chain {chain_id}")
        logger.debug(f"API Key present: {bool(self.api_key)}")
        logger.debug(f"Endpoint: {endpoint}")
        
        try:
            result = await self._make_request("GET", endpoint, params=params)
            logger.debug(f"Balance result for chain {chain_id}: {len(result) if isinstance(result, (list, dict)) else result}")
            return result
        except OneInchAPIError as e:
            logger.error(f"API error fetching balances for chain {chain_id}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching balances for chain {chain_id}: {e}", exc_info=True)
            return {}
    
    async def get_token_prices(
        self,
        chain_id: int,
        token_addresses: List[str]
    ) -> Dict[str, Any]:
        """
        Get current prices for tokens.
        
        Args:
            chain_id: Chain ID
            token_addresses: List of token contract addresses
            
        Returns:
            Dictionary of token prices
        """
        if not token_addresses:
            return {}
        
        # Updated to use the Spot Price API endpoint
        endpoint = f"/price/v3/{chain_id}"
        params = {
            "tokens": ",".join(token_addresses),
            "currency": "USD"
        }
        
        try:
            result = await self._make_request("GET", endpoint, params=params)
            logger.debug(f"Price result for chain {chain_id}: {len(result) if isinstance(result, (list, dict)) else result} items")
            return result
        except OneInchAPIError as e:
            logger.error(f"API error fetching prices for chain {chain_id}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching prices for chain {chain_id}: {e}", exc_info=True)
            return {}
    
    async def get_tokens_info(
        self,
        chain_id: int
    ) -> Dict[str, Any]:
        """
        Get information about all tokens on a chain.
        
        Args:
            chain_id: Chain ID
            
        Returns:
            Dictionary of token information
        """
        # Updated to use the Token API v3 endpoint
        endpoint = f"/token/v1.2/{chain_id}"
        
        try:
            result = await self._make_request("GET", endpoint)
            logger.debug(f"Token info result for chain {chain_id}: {len(result) if isinstance(result, (list, dict)) else result} tokens")
            return result
        except OneInchAPIError as e:
            logger.error(f"API error fetching token info for chain {chain_id}: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error fetching token info for chain {chain_id}: {e}", exc_info=True)
            return {}
    
    async def get_multi_chain_portfolio(
        self,
        wallet_address: str,
        chain_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Get portfolio data across multiple chains.
        
        Args:
            wallet_address: Ethereum wallet address
            chain_ids: List of chain IDs to check
            
        Returns:
            Aggregated portfolio data
        """
        # Validate wallet address
        if not wallet_address or not wallet_address.startswith('0x') or len(wallet_address) != 42:
            raise OneInchAPIError(f"Invalid wallet address: {wallet_address}")
        
        if chain_ids is None:
            chain_ids = list(self.chain_configs.keys())
        
        # Filter to only supported mainnet chains (1inch doesn't support testnets)
        supported_chain_ids = [cid for cid in chain_ids if cid in self.chain_configs]
        testnet_chain_ids = [cid for cid in chain_ids if cid in self.testnet_chains]
        
        # Log if testnet chains were requested
        if testnet_chain_ids:
            logger.warning(f"Testnet chains requested but not supported by 1inch: {testnet_chain_ids}")
        
        # Only proceed with supported chains
        chain_ids = supported_chain_ids
        
        # Fetch balances for all chains in parallel
        balance_tasks = [
            self.get_wallet_balances(wallet_address, chain_id)
            for chain_id in chain_ids
        ]
        
        balance_results = await asyncio.gather(*balance_tasks, return_exceptions=True)
        
        # Process results
        portfolio_data = {
            "address": wallet_address,
            "chains": [],
            "total_value_usd": 0,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        for chain_id, balances in zip(chain_ids, balance_results):
            if isinstance(balances, Exception):
                logger.error(f"Error fetching balances for chain {chain_id}: {balances}")
                continue
            
            if not balances:
                continue
            
            # Get token addresses for price lookup
            token_addresses = list(balances.keys())
            
            # Fetch prices
            prices = await self.get_token_prices(chain_id, token_addresses)
            
            # Fetch token metadata
            tokens_info = await self.get_tokens_info(chain_id)
            
            # Calculate values
            chain_data = {
                "chain_id": chain_id,
                "chain_name": self.chain_configs[chain_id]["name"],
                "tokens": [],
                "total_value_usd": 0
            }
            
            # Handle different API response formats
            balance_items = balances if isinstance(balances, list) else balances.items()
            
            for item in balance_items:
                if isinstance(item, dict):
                    # New API format: response is a list of token objects
                    token_address = item.get("tokenAddress", item.get("token_address", ""))
                    balance = float(item.get("balance", 0))
                    token_info = item  # Info is included in balance response
                else:
                    # Old API format: response is a dict
                    token_address, balance_data = item
                    balance = float(balance_data.get("balance", 0))
                    token_info = tokens_info.get(token_address, {})
                
                # Skip if balance is too small
                if balance <= 0:
                    continue
                
                # Get token metadata
                decimals = int(token_info.get("decimals", 18))
                symbol = token_info.get("symbol", "UNKNOWN")
                name = token_info.get("name", symbol)
                
                # Calculate human-readable balance
                human_balance = balance / (10 ** decimals)
                
                # Get price - handle both old and new formats
                price_usd = 0.0
                if prices:
                    if isinstance(prices, dict):
                        price_data = prices.get(token_address, {})
                        price_usd = float(price_data.get("price", price_data.get("usd", 0)))
                    elif isinstance(prices, list):
                        # Find price in list format
                        for price_item in prices:
                            if price_item.get("tokenAddress") == token_address:
                                price_usd = float(price_item.get("price", price_item.get("usd", 0)))
                                break
                
                # Calculate value
                value_usd = human_balance * price_usd
                
                # Skip if value is too small
                if value_usd < 0.01:
                    continue
                
                token_data = {
                    "address": token_address,
                    "symbol": symbol,
                    "name": name,
                    "decimals": decimals,
                    "balance": str(balance),
                    "balance_human": human_balance,
                    "price_usd": price_usd,
                    "value_usd": value_usd,
                    "logo_url": token_info.get("logoURI", token_info.get("logo_uri", ""))
                }
                
                chain_data["tokens"].append(token_data)
                chain_data["total_value_usd"] += value_usd
            
            if chain_data["tokens"]:
                portfolio_data["chains"].append(chain_data)
                portfolio_data["total_value_usd"] += chain_data["total_value_usd"]
        
        return portfolio_data
    
    async def get_quote(
        self,
        chain_id: int,
        from_token: str,
        to_token: str,
        amount: str,
        from_address: str
    ) -> Dict[str, Any]:
        """
        Get a swap quote from 1inch.
        
        Args:
            chain_id: Chain ID
            from_token: Source token address
            to_token: Destination token address
            amount: Amount to swap (in smallest unit)
            from_address: User's wallet address
            
        Returns:
            Swap quote data
        """
        endpoint = f"/swap/v6.0/{chain_id}/quote"
        params = {
            "src": from_token,
            "dst": to_token,
            "amount": amount,
            "from": from_address,
            "slippage": "1"  # 1% slippage
        }
        
        try:
            logger.info(f"Getting quote for {from_token} -> {to_token} on chain {chain_id}")
            result = await self._make_request("GET", endpoint, params=params)
            logger.debug(f"Quote received: {result.get('toAmount', 'N/A')} {to_token}")
            return result
        except OneInchAPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting quote: {str(e)}", exc_info=True)
            raise OneInchAPIError(f"Failed to get quote: {str(e)}")
    
    async def build_swap_tx(
        self,
        chain_id: int,
        from_token: str,
        to_token: str,
        amount: str,
        from_address: str,
        slippage: float = 1.0
    ) -> Dict[str, Any]:
        """
        Build a swap transaction.
        
        Args:
            chain_id: Chain ID
            from_token: Source token address
            to_token: Destination token address
            amount: Amount to swap (in smallest unit)
            from_address: User's wallet address
            slippage: Slippage tolerance in percentage
            
        Returns:
            Transaction data ready to be signed and sent
        """
        endpoint = f"/swap/v6.0/{chain_id}/swap"
        params = {
            "src": from_token,
            "dst": to_token,
            "amount": amount,
            "from": from_address,
            "slippage": str(slippage),
            "disableEstimate": "false"
        }
        
        try:
            logger.info(f"Building swap transaction for {from_token} -> {to_token} on chain {chain_id}")
            result = await self._make_request("GET", endpoint, params=params)
            logger.debug(f"Swap transaction built successfully")
            return result
        except OneInchAPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error building swap transaction: {str(e)}", exc_info=True)
            raise OneInchAPIError(f"Failed to build swap transaction: {str(e)}")


# Singleton instance
oneinch_service = OneInchService()