"""Alchemy API integration service for blockchain data."""

import asyncio
from typing import Dict, List, Optional, Any
from decimal import Decimal
import aiohttp
import logging
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class AlchemyError(Exception):
    """Custom exception for Alchemy API errors."""
    pass


class AlchemyService:
    """Service for interacting with Alchemy blockchain APIs."""
    
    # Chain configurations with Alchemy network names
    CHAIN_CONFIGS = {
        1: {"name": "Ethereum", "network": "eth-mainnet", "native_symbol": "ETH", "native_decimals": 18},
        137: {"name": "Polygon", "network": "polygon-mainnet", "native_symbol": "MATIC", "native_decimals": 18},
        42161: {"name": "Arbitrum One", "network": "arb-mainnet", "native_symbol": "ETH", "native_decimals": 18},
        42170: {"name": "Arbitrum Nova", "network": "arbnova-mainnet", "native_symbol": "ETH", "native_decimals": 18},
        10: {"name": "Optimism", "network": "opt-mainnet", "native_symbol": "ETH", "native_decimals": 18},
        8453: {"name": "Base", "network": "base-mainnet", "native_symbol": "ETH", "native_decimals": 18},
        1101: {"name": "Polygon zkEVM", "network": "polygonzkevm-mainnet", "native_symbol": "ETH", "native_decimals": 18},
        810180: {"name": "World Chain", "network": "worldchain-mainnet", "native_symbol": "ETH", "native_decimals": 18},
        7777777: {"name": "Zora", "network": "zora-mainnet", "native_symbol": "ETH", "native_decimals": 18},
    }
    
    def __init__(self):
        self.api_key = settings.ALCHEMY_API_KEY
        self.session: Optional[aiohttp.ClientSession] = None
        
        if not self.api_key or self.api_key == "your-alchemy-api-key-here":
            logger.warning("Alchemy API key not configured properly")
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    def _get_base_url(self, chain_id: int) -> str:
        """Get Alchemy base URL for a specific chain."""
        chain_config = self.CHAIN_CONFIGS.get(chain_id)
        if not chain_config:
            raise AlchemyError(f"Unsupported chain ID: {chain_id}")
        
        network = chain_config["network"]
        return f"https://{network}.g.alchemy.com/v2/{self.api_key}"
    
    async def _make_request(
        self,
        chain_id: int,
        method: str,
        params: List[Any]
    ) -> Any:
        """Make a JSON-RPC request to Alchemy."""
        if not self.session:
            raise AlchemyError("Session not initialized. Use async context manager.")
        
        url = self._get_base_url(chain_id)
        
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params
        }
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise AlchemyError(f"API request failed: {response.status} - {error_text}")
                
                data = await response.json()
                
                if "error" in data:
                    raise AlchemyError(f"RPC error: {data['error']}")
                
                return data.get("result")
                
        except aiohttp.ClientError as e:
            logger.error(f"Network error calling Alchemy: {e}")
            raise AlchemyError(f"Network error: {str(e)}")
    
    async def get_native_balance(
        self,
        wallet_address: str,
        chain_id: int
    ) -> Dict[str, Any]:
        """
        Get native token balance for a wallet on a specific chain.
        
        Args:
            wallet_address: Ethereum wallet address
            chain_id: Chain ID
            
        Returns:
            Dictionary with balance information
        """
        chain_config = self.CHAIN_CONFIGS.get(chain_id)
        if not chain_config:
            logger.warning(f"Unsupported chain ID: {chain_id}")
            return {}
        
        try:
            # Get balance in wei
            balance_hex = await self._make_request(
                chain_id,
                "eth_getBalance",
                [wallet_address, "latest"]
            )
            
            # Convert from hex to decimal
            balance_wei = int(balance_hex, 16)
            
            # Convert to human-readable format
            decimals = chain_config["native_decimals"]
            balance_human = balance_wei / (10 ** decimals)
            
            logger.info(f"Native balance for {wallet_address} on chain {chain_id}: {balance_human} {chain_config['native_symbol']}")
            
            return {
                "address": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",  # Special address for native tokens
                "symbol": chain_config["native_symbol"],
                "name": chain_config["native_symbol"],
                "decimals": decimals,
                "balance": str(balance_wei),
                "balance_human": balance_human,
                "is_native": True
            }
            
        except Exception as e:
            logger.error(f"Error fetching native balance for chain {chain_id}: {e}")
            return {}
    
    async def get_token_balances(
        self,
        wallet_address: str,
        chain_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get all ERC20 token balances for a wallet.
        
        Args:
            wallet_address: Ethereum wallet address
            chain_id: Chain ID
            
        Returns:
            List of token balances
        """
        try:
            # Use Alchemy's enhanced API to get token balances
            result = await self._make_request(
                chain_id,
                "alchemy_getTokenBalances",
                [wallet_address, "erc20"]
            )
            
            token_balances = []
            
            for token_data in result.get("tokenBalances", []):
                token_address = token_data["contractAddress"]
                balance_hex = token_data.get("tokenBalance")
                
                if not balance_hex or balance_hex == "0x0":
                    continue
                
                # Get token metadata
                metadata = await self.get_token_metadata(token_address, chain_id)
                
                if metadata:
                    balance_wei = int(balance_hex, 16)
                    decimals = metadata.get("decimals", 18)
                    balance_human = balance_wei / (10 ** decimals)
                    
                    token_balances.append({
                        "address": token_address,
                        "symbol": metadata.get("symbol", "UNKNOWN"),
                        "name": metadata.get("name", "Unknown Token"),
                        "decimals": decimals,
                        "balance": str(balance_wei),
                        "balance_human": balance_human,
                        "logo": metadata.get("logo"),
                        "is_native": False
                    })
            
            logger.info(f"Found {len(token_balances)} tokens for {wallet_address} on chain {chain_id}")
            return token_balances
            
        except Exception as e:
            logger.error(f"Error fetching token balances for chain {chain_id}: {e}")
            return []
    
    async def get_token_metadata(
        self,
        token_address: str,
        chain_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific token.
        
        Args:
            token_address: Token contract address
            chain_id: Chain ID
            
        Returns:
            Token metadata or None
        """
        try:
            result = await self._make_request(
                chain_id,
                "alchemy_getTokenMetadata",
                [token_address]
            )
            
            return {
                "symbol": result.get("symbol"),
                "name": result.get("name"),
                "decimals": result.get("decimals", 18),
                "logo": result.get("logo"),
            }
            
        except Exception as e:
            logger.error(f"Error fetching token metadata for {token_address}: {e}")
            return None
    
    async def get_portfolio_for_all_chains(
        self,
        wallet_address: str,
        chain_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Get complete portfolio across all supported chains.
        
        Args:
            wallet_address: Ethereum wallet address
            chain_ids: List of chain IDs to check (defaults to all supported)
            
        Returns:
            Aggregated portfolio data
        """
        if chain_ids is None:
            chain_ids = list(self.CHAIN_CONFIGS.keys())
        
        # Filter to only supported chains
        supported_chain_ids = [cid for cid in chain_ids if cid in self.CHAIN_CONFIGS]
        
        portfolio_data = {
            "address": wallet_address,
            "chains": [],
            "total_balance_count": 0,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Fetch balances for all chains in parallel
        tasks = []
        for chain_id in supported_chain_ids:
            tasks.append(self._get_chain_portfolio(wallet_address, chain_id))
        
        chain_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for chain_id, result in zip(supported_chain_ids, chain_results):
            if isinstance(result, Exception):
                logger.error(f"Error fetching portfolio for chain {chain_id}: {result}")
                continue
            
            if result and result.get("tokens"):
                portfolio_data["chains"].append(result)
                portfolio_data["total_balance_count"] += len(result["tokens"])
        
        return portfolio_data
    
    async def _get_chain_portfolio(
        self,
        wallet_address: str,
        chain_id: int
    ) -> Dict[str, Any]:
        """Get portfolio for a single chain."""
        chain_config = self.CHAIN_CONFIGS.get(chain_id)
        if not chain_config:
            return {}
        
        # Get native balance
        native_balance = await self.get_native_balance(wallet_address, chain_id)
        
        # Get token balances
        token_balances = await self.get_token_balances(wallet_address, chain_id)
        
        # Combine all balances
        all_tokens = []
        if native_balance and float(native_balance.get("balance_human", 0)) > 0:
            all_tokens.append(native_balance)
        
        all_tokens.extend(token_balances)
        
        return {
            "chain_id": chain_id,
            "chain_name": chain_config["name"],
            "tokens": all_tokens
        }


# Singleton instance
alchemy_service = AlchemyService()