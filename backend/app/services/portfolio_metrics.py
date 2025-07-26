"""Portfolio metrics calculation service."""

import math
from typing import Dict, List, Any, Optional
from collections import defaultdict
import numpy as np


class PortfolioMetricsService:
    """Service for calculating portfolio metrics and analytics."""
    
    @staticmethod
    def calculate_diversification_score(portfolio_data: Dict[str, Any]) -> float:
        """
        Calculate portfolio diversification score (0-100).
        
        Based on:
        - Number of tokens
        - Distribution across chains
        - Concentration risk (HHI)
        
        Args:
            portfolio_data: Portfolio data from 1inch service
            
        Returns:
            Diversification score (0-100)
        """
        if not portfolio_data.get("chains"):
            return 0.0
        
        total_value = portfolio_data.get("total_value_usd", 0)
        if total_value == 0:
            return 0.0
        
        # Get all tokens across all chains
        all_tokens = []
        chain_values = {}
        
        for chain in portfolio_data["chains"]:
            chain_id = chain["chain_id"]
            chain_values[chain_id] = chain["total_value_usd"]
            
            for token in chain["tokens"]:
                all_tokens.append({
                    "symbol": token["symbol"],
                    "value": token["value_usd"],
                    "chain_id": chain_id
                })
        
        # Calculate metrics
        num_tokens = len(all_tokens)
        num_chains = len(chain_values)
        
        # 1. Token count score (max at 20+ tokens)
        token_score = min(num_tokens / 20, 1.0) * 30
        
        # 2. Chain distribution score (max at 4+ chains)
        chain_score = min(num_chains / 4, 1.0) * 30
        
        # 3. Concentration score using HHI (Herfindahl-Hirschman Index)
        token_shares = [token["value"] / total_value for token in all_tokens]
        hhi = sum(share ** 2 for share in token_shares)
        # HHI ranges from 0 to 1, where lower is more diversified
        concentration_score = (1 - hhi) * 40
        
        return round(token_score + chain_score + concentration_score, 2)
    
    @staticmethod
    def calculate_risk_score(portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate portfolio risk metrics.
        
        Args:
            portfolio_data: Portfolio data from 1inch service
            
        Returns:
            Risk assessment with score and factors
        """
        if not portfolio_data.get("chains"):
            return {
                "score": 0,
                "level": "Unknown",
                "factors": []
            }
        
        risk_factors = []
        risk_points = 0
        
        # Analyze token distribution
        all_tokens = []
        stablecoin_value = 0
        major_tokens_value = 0  # ETH, BTC, BNB, MATIC
        
        major_symbols = {"ETH", "WETH", "WBTC", "BTC", "BNB", "MATIC", "AVAX", "SOL"}
        stable_symbols = {"USDT", "USDC", "DAI", "BUSD", "TUSD", "FRAX"}
        
        for chain in portfolio_data["chains"]:
            for token in chain["tokens"]:
                symbol = token["symbol"].upper()
                value = token["value_usd"]
                
                if symbol in stable_symbols:
                    stablecoin_value += value
                elif symbol in major_symbols:
                    major_tokens_value += value
                
                all_tokens.append(token)
        
        total_value = portfolio_data["total_value_usd"]
        if total_value == 0:
            return {
                "score": 0,
                "level": "Unknown",
                "factors": []
            }
        
        # Calculate risk factors
        stable_percentage = (stablecoin_value / total_value) * 100
        major_percentage = (major_tokens_value / total_value) * 100
        
        # 1. Stablecoin allocation (lower risk with more stables)
        if stable_percentage < 10:
            risk_points += 30
            risk_factors.append("Low stablecoin allocation (<10%)")
        elif stable_percentage < 20:
            risk_points += 20
            risk_factors.append("Moderate stablecoin allocation (10-20%)")
        else:
            risk_points += 10
        
        # 2. Major token allocation
        if major_percentage < 30:
            risk_points += 25
            risk_factors.append("Low allocation to major tokens")
        elif major_percentage < 50:
            risk_points += 15
        else:
            risk_points += 5
        
        # 3. Concentration risk
        top_5_value = sum(
            sorted([t["value_usd"] for t in all_tokens], reverse=True)[:5]
        )
        concentration = (top_5_value / total_value) * 100
        
        if concentration > 90:
            risk_points += 30
            risk_factors.append("High concentration in top 5 tokens (>90%)")
        elif concentration > 80:
            risk_points += 20
            risk_factors.append("Moderate concentration in top 5 tokens (80-90%)")
        else:
            risk_points += 10
        
        # 4. Number of positions
        num_tokens = len(all_tokens)
        if num_tokens < 5:
            risk_points += 15
            risk_factors.append("Low number of positions (<5)")
        elif num_tokens < 10:
            risk_points += 10
        
        # Determine risk level
        if risk_points >= 70:
            level = "High"
        elif risk_points >= 40:
            level = "Medium"
        else:
            level = "Low"
        
        return {
            "score": min(risk_points, 100),
            "level": level,
            "factors": risk_factors,
            "metrics": {
                "stablecoin_percentage": round(stable_percentage, 2),
                "major_tokens_percentage": round(major_percentage, 2),
                "concentration_top5": round(concentration, 2),
                "num_tokens": num_tokens
            }
        }
    
    @staticmethod
    def calculate_performance_metrics(
        portfolio_data: Dict[str, Any],
        historical_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Calculate performance metrics.
        
        Args:
            portfolio_data: Current portfolio data
            historical_data: Historical portfolio snapshots
            
        Returns:
            Performance metrics
        """
        current_value = portfolio_data.get("total_value_usd", 0)
        
        # Without historical data, return basic metrics
        if not historical_data or len(historical_data) < 2:
            return {
                "current_value": current_value,
                "change_24h": 0,
                "change_24h_percent": 0,
                "change_7d": 0,
                "change_7d_percent": 0,
                "change_30d": 0,
                "change_30d_percent": 0,
                "all_time_high": current_value,
                "all_time_low": current_value
            }
        
        # Calculate changes over different periods
        # (This would require actual historical data implementation)
        return {
            "current_value": current_value,
            "change_24h": 0,  # Placeholder
            "change_24h_percent": 0,
            "change_7d": 0,
            "change_7d_percent": 0,
            "change_30d": 0,
            "change_30d_percent": 0,
            "all_time_high": current_value,
            "all_time_low": current_value
        }
    
    @staticmethod
    def get_rebalancing_suggestions(
        portfolio_data: Dict[str, Any],
        target_allocation: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate rebalancing suggestions.
        
        Args:
            portfolio_data: Current portfolio data
            target_allocation: Target allocation percentages by symbol
            
        Returns:
            List of rebalancing suggestions
        """
        if not portfolio_data.get("chains"):
            return []
        
        # Default target allocation if not provided
        if target_allocation is None:
            target_allocation = {
                "ETH": 30.0,
                "WETH": 30.0,
                "USDC": 20.0,
                "USDT": 20.0,
                "WBTC": 10.0,
                "OTHER": 10.0
            }
        
        # Aggregate current holdings by symbol
        current_holdings = defaultdict(float)
        total_value = portfolio_data["total_value_usd"]
        
        for chain in portfolio_data["chains"]:
            for token in chain["tokens"]:
                symbol = token["symbol"].upper()
                current_holdings[symbol] += token["value_usd"]
        
        # Calculate current percentages
        current_percentages = {
            symbol: (value / total_value) * 100
            for symbol, value in current_holdings.items()
        }
        
        suggestions = []
        
        # Check each target allocation
        for symbol, target_pct in target_allocation.items():
            current_pct = current_percentages.get(symbol, 0)
            diff_pct = target_pct - current_pct
            
            if abs(diff_pct) > 2:  # Only suggest if difference > 2%
                diff_value = (diff_pct / 100) * total_value
                
                suggestions.append({
                    "symbol": symbol,
                    "action": "buy" if diff_pct > 0 else "sell",
                    "current_percentage": round(current_pct, 2),
                    "target_percentage": target_pct,
                    "difference_percentage": round(diff_pct, 2),
                    "difference_value": round(abs(diff_value), 2),
                    "priority": "high" if abs(diff_pct) > 10 else "medium"
                })
        
        # Sort by priority and difference
        suggestions.sort(
            key=lambda x: (
                0 if x["priority"] == "high" else 1,
                -abs(x["difference_percentage"])
            )
        )
        
        return suggestions
    
    @staticmethod
    def calculate_yield_metrics(portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate yield/APY metrics for yield-bearing tokens.
        
        Args:
            portfolio_data: Portfolio data
            
        Returns:
            Yield metrics
        """
        # This would require integration with DeFi protocols
        # For now, return placeholder data
        return {
            "total_yield_usd": 0,
            "average_apy": 0,
            "yield_bearing_percentage": 0,
            "opportunities": []
        }


# Singleton instance
portfolio_metrics_service = PortfolioMetricsService()