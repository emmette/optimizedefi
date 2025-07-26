"""1inch API integration service."""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp
from decimal import Decimal

from app.core.config import settings


class OneInchAPIError(Exception):
    """Custom exception for 1inch API errors."""
    pass


class OneInchService:
    """Service for interacting with 1inch APIs."""
    
    def __init__(self):
        self.base_url = "https://api.1inch.dev"
        self.api_key = settings.ONEINCH_API_KEY
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Chain configurations
        self.chain_configs = {
            1: {"name": "Ethereum", "native": "ETH"},
            137: {"name": "Polygon", "native": "MATIC"},
            10: {"name": "Optimism", "native": "ETH"},
            42161: {"name": "Arbitrum", "native": "ETH"},
            56: {"name": "BSC", "native": "BNB"},
            43114: {"name": "Avalanche", "native": "AVAX"},
            8453: {"name": "Base", "native": "ETH"},
        }
    
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
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an API request to 1inch."""
        if not self.session:
            raise OneInchAPIError("Session not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                headers=self._get_headers(),
                params=params,
                json=data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise OneInchAPIError(
                        f"API request failed: {response.status} - {error_text}"
                    )
                
                return await response.json()
                
        except aiohttp.ClientError as e:
            raise OneInchAPIError(f"Network error: {str(e)}")
    
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
        endpoint = f"/portfolio/api/v4/general/balances/{chain_id}"
        params = {"wallet_address": wallet_address}
        
        try:
            result = await self._make_request("GET", endpoint, params=params)
            return result
        except Exception as e:
            print(f"Error fetching balances for chain {chain_id}: {e}")
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
        
        endpoint = f"/price/v1.1/{chain_id}"
        params = {
            "addresses": ",".join(token_addresses),
            "currency": "USD"
        }
        
        try:
            result = await self._make_request("GET", endpoint, params=params)
            return result
        except Exception as e:
            print(f"Error fetching prices for chain {chain_id}: {e}")
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
        endpoint = f"/swap/v6.0/{chain_id}/tokens"
        
        try:
            result = await self._make_request("GET", endpoint)
            return result.get("tokens", {})
        except Exception as e:
            print(f"Error fetching token info for chain {chain_id}: {e}")
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
        if chain_ids is None:
            chain_ids = list(self.chain_configs.keys())
        
        # Filter to only supported chains
        chain_ids = [cid for cid in chain_ids if cid in self.chain_configs]
        
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
                print(f"Error for chain {chain_id}: {balances}")
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
            
            for token_address, balance_data in balances.items():
                # Skip if balance is too small
                balance = float(balance_data.get("balance", 0))
                if balance <= 0:
                    continue
                
                # Get token info
                token_info = tokens_info.get(token_address, {})
                decimals = token_info.get("decimals", 18)
                
                # Calculate human-readable balance
                human_balance = balance / (10 ** decimals)
                
                # Get price
                price_data = prices.get(token_address, {})
                price_usd = float(price_data.get("price", 0))
                
                # Calculate value
                value_usd = human_balance * price_usd
                
                # Skip if value is too small
                if value_usd < 0.01:
                    continue
                
                token_data = {
                    "address": token_address,
                    "symbol": token_info.get("symbol", "UNKNOWN"),
                    "name": token_info.get("name", "Unknown Token"),
                    "decimals": decimals,
                    "balance": str(balance),
                    "balance_human": human_balance,
                    "price_usd": price_usd,
                    "value_usd": value_usd,
                    "logo_url": token_info.get("logoURI", "")
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
            result = await self._make_request("GET", endpoint, params=params)
            return result
        except Exception as e:
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
            result = await self._make_request("GET", endpoint, params=params)
            return result
        except Exception as e:
            raise OneInchAPIError(f"Failed to build swap transaction: {str(e)}")


# Singleton instance
oneinch_service = OneInchService()