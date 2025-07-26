from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from app.core.auth import validate_ethereum_address, get_current_user, TokenData
from app.services.oneinch import oneinch_service
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
    _: Optional[TokenData] = Depends(get_current_user)  # Optional auth
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
        # Fetch portfolio data from 1inch
        async with oneinch_service as service:
            portfolio_data = await service.get_multi_chain_portfolio(
                wallet_address=address,
                chain_ids=chains
            )
        
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
    _: Optional[TokenData] = Depends(get_current_user)  # Optional auth
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