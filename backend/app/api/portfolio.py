from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.core.auth import validate_ethereum_address, get_current_user, get_current_user_optional, TokenData
from app.services.oneinch import oneinch_service
from app.services.alchemy import alchemy_service
from app.services.portfolio_metrics import portfolio_metrics_service
from app.services.cache import cached


router = APIRouter()


class Token(BaseModel):
    """Token model for API responses."""
    address: str
    symbol: str
    name: str
    decimals: int
    chain_id: int
    balance: str
    balance_human: float
    balance_usd: float
    price_usd: float
    logo_url: Optional[str] = None


class ChainData(BaseModel):
    """Chain data model."""
    chain_id: int
    chain_name: str
    total_value_usd: float
    tokens: List[Token]


class PortfolioResponse(BaseModel):
    """Portfolio response model."""
    address: str
    total_value_usd: float
    chains: List[ChainData]
    diversification_score: float
    risk_assessment: Dict[str, Any]
    performance: Dict[str, Any]
    last_updated: datetime


class PortfolioMetricsResponse(BaseModel):
    """Portfolio metrics response model."""
    diversification_score: float
    risk_assessment: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    rebalancing_suggestions: List[Dict[str, Any]]
    yield_metrics: Dict[str, Any]


@router.get("/{address}", response_model=PortfolioResponse)
async def get_portfolio(
    address: str,
    chains: Optional[List[int]] = Query(default=None),
    current_user: Optional[TokenData] = Depends(get_current_user_optional)
):
    """
    Get portfolio data for a wallet address across multiple chains.
    
    Args:
        address: Ethereum wallet address
        chains: List of chain IDs to query (defaults to all supported)
        
    Returns:
        Portfolio data with tokens, metrics, and analysis
    """
    # Validate address
    if not validate_ethereum_address(address):
        raise HTTPException(status_code=400, detail="Invalid Ethereum address")
    
    # Use default chains if not specified
    if chains is None:
        chains = [1, 137, 10, 42161]  # Ethereum, Polygon, Optimism, Arbitrum
    
    try:
        print(f"Fetching portfolio for address: {address}, chains: {chains}")
        
        # First, fetch actual token balances from Alchemy
        async with alchemy_service as alchemy:
            balance_data = await alchemy.get_portfolio_for_all_chains(
                wallet_address=address,
                chain_ids=chains
            )
        
        print(f"Balance data received from Alchemy: {len(balance_data.get('chains', []))} chains")
        
        # Then, fetch prices for discovered tokens from 1inch
        portfolio_data = {
            "address": address,
            "chains": [],
            "total_value_usd": 0,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Process each chain
        for chain_data in balance_data.get("chains", []):
            chain_id = chain_data["chain_id"]
            tokens = chain_data["tokens"]
            
            if not tokens:
                continue
            
            # Get token addresses for price lookup (excluding native tokens)
            token_addresses = [
                token["address"] for token in tokens 
                if not token.get("is_native", False) and token["address"] != "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
            ]
            
            # Fetch prices from 1inch
            prices = {}
            if token_addresses:
                async with oneinch_service as oneinch:
                    prices = await oneinch.get_token_prices(chain_id, token_addresses)
            
            # For native tokens, we need to get the price separately
            native_token_price = 0.0
            for token in tokens:
                if token.get("is_native", False):
                    # Get native token price (ETH, MATIC, etc.)
                    native_price_data = {}
                    async with oneinch_service as oneinch:
                        # Use wrapped token address for price lookup
                        wrapped_addresses = {
                            1: "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",  # WETH on Ethereum
                            137: "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",  # WMATIC on Polygon
                            10: "0x4200000000000000000000000000000000000006",  # WETH on Optimism
                            42161: "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",  # WETH on Arbitrum
                            8453: "0x4200000000000000000000000000000000000006",  # WETH on Base
                        }
                        wrapped_address = wrapped_addresses.get(chain_id)
                        if wrapped_address:
                            native_price_data = await oneinch.get_token_prices(chain_id, [wrapped_address])
                            if native_price_data and wrapped_address in native_price_data:
                                native_token_price = float(native_price_data[wrapped_address].get("price", 0))
                    break
            
            # Build chain portfolio with prices
            chain_portfolio = {
                "chain_id": chain_id,
                "chain_name": chain_data["chain_name"],
                "tokens": [],
                "total_value_usd": 0
            }
            
            for token in tokens:
                # Get price
                price_usd = 0.0
                if token.get("is_native", False):
                    price_usd = native_token_price
                else:
                    price_data = prices.get(token["address"], {})
                    price_usd = float(price_data.get("price", 0))
                
                # Calculate value
                value_usd = token["balance_human"] * price_usd
                
                # Add token to portfolio
                token_data = {
                    "address": token["address"],
                    "symbol": token["symbol"],
                    "name": token["name"],
                    "decimals": token["decimals"],
                    "balance": token["balance"],
                    "balance_human": token["balance_human"],
                    "price_usd": price_usd,
                    "value_usd": value_usd,
                    "logo_url": token.get("logo", "")
                }
                
                chain_portfolio["tokens"].append(token_data)
                chain_portfolio["total_value_usd"] += value_usd
            
            if chain_portfolio["tokens"]:
                portfolio_data["chains"].append(chain_portfolio)
                portfolio_data["total_value_usd"] += chain_portfolio["total_value_usd"]
        
        print(f"Portfolio data compiled: Total value ${portfolio_data['total_value_usd']:,.2f}")
        
        # Calculate metrics
        diversification_score = portfolio_metrics_service.calculate_diversification_score(
            portfolio_data
        )
        risk_assessment = portfolio_metrics_service.calculate_risk_score(
            portfolio_data
        )
        performance_metrics = portfolio_metrics_service.calculate_performance_metrics(
            portfolio_data
        )
        
        # Transform data for response
        chain_data_list = []
        for chain in portfolio_data.get("chains", []):
            tokens = [
                Token(
                    address=token["address"],
                    symbol=token["symbol"],
                    name=token["name"],
                    decimals=token["decimals"],
                    chain_id=chain["chain_id"],
                    balance=token["balance"],
                    balance_human=token["balance_human"],
                    balance_usd=token["value_usd"],
                    price_usd=token["price_usd"],
                    logo_url=token.get("logo_url")
                )
                for token in chain["tokens"]
            ]
            
            chain_data_list.append(
                ChainData(
                    chain_id=chain["chain_id"],
                    chain_name=chain["chain_name"],
                    total_value_usd=chain["total_value_usd"],
                    tokens=tokens
                )
            )
        
        return PortfolioResponse(
            address=address.lower(),
            total_value_usd=portfolio_data["total_value_usd"],
            chains=chain_data_list,
            diversification_score=diversification_score,
            risk_assessment=risk_assessment,
            performance=performance_metrics,
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        print(f"Error fetching portfolio: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch portfolio data. Please try again later."
        )


@router.get("/{address}/metrics", response_model=PortfolioMetricsResponse)
@cached(ttl=60)  # Cache for 1 minute
async def get_portfolio_metrics(
    address: str,
    chains: Optional[List[int]] = Query(default=None),
    current_user: Optional[TokenData] = Depends(get_current_user_optional)
):
    """
    Get detailed portfolio metrics and analysis.
    
    Args:
        address: Ethereum wallet address
        chains: List of chain IDs to query
        
    Returns:
        Detailed metrics including risk, diversification, and suggestions
    """
    # Validate address
    if not validate_ethereum_address(address):
        raise HTTPException(status_code=400, detail="Invalid Ethereum address")
    
    # Use default chains if not specified
    if chains is None:
        chains = [1, 137, 10, 42161]
    
    try:
        # Fetch portfolio data
        async with oneinch_service as service:
            portfolio_data = await service.get_multi_chain_portfolio(
                wallet_address=address,
                chain_ids=chains
            )
        
        # Calculate all metrics
        diversification_score = portfolio_metrics_service.calculate_diversification_score(
            portfolio_data
        )
        risk_assessment = portfolio_metrics_service.calculate_risk_score(
            portfolio_data
        )
        performance_metrics = portfolio_metrics_service.calculate_performance_metrics(
            portfolio_data
        )
        rebalancing_suggestions = portfolio_metrics_service.get_rebalancing_suggestions(
            portfolio_data
        )
        yield_metrics = portfolio_metrics_service.calculate_yield_metrics(
            portfolio_data
        )
        
        return PortfolioMetricsResponse(
            diversification_score=diversification_score,
            risk_assessment=risk_assessment,
            performance_metrics=performance_metrics,
            rebalancing_suggestions=rebalancing_suggestions,
            yield_metrics=yield_metrics
        )
        
    except Exception as e:
        print(f"Error calculating metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to calculate portfolio metrics."
        )


@router.get("/{address}/history")
async def get_portfolio_history(
    address: str,
    period: str = Query(default="7d", regex="^(24h|7d|30d|90d|1y|all)$"),
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get historical portfolio value (authenticated endpoint).
    
    Args:
        address: Ethereum wallet address
        period: Time period for history
        
    Returns:
        Historical portfolio data
    """
    # Ensure user can only access their own history
    if address.lower() != current_user.address.lower():
        raise HTTPException(
            status_code=403,
            detail="You can only access your own portfolio history"
        )
    
    # TODO: Implement historical data storage and retrieval
    # This would require a database to store snapshots
    return {
        "address": address,
        "period": period,
        "data": [],
        "message": "Historical data tracking not yet implemented"
    }


@router.post("/{address}/snapshot")
async def create_portfolio_snapshot(
    address: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Create a snapshot of the current portfolio (authenticated endpoint).
    
    Args:
        address: Ethereum wallet address
        
    Returns:
        Snapshot creation confirmation
    """
    # Ensure user can only snapshot their own portfolio
    if address.lower() != current_user.address.lower():
        raise HTTPException(
            status_code=403,
            detail="You can only snapshot your own portfolio"
        )
    
    # TODO: Implement snapshot storage
    # This would save current portfolio state to database
    return {
        "message": "Portfolio snapshot created",
        "address": address,
        "timestamp": datetime.utcnow()
    }