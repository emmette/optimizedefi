"""Swap execution agent."""

import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from langchain_core.tools import Tool

from app.agents.base import BaseAgent
from app.agents.config import AgentType, agent_config_manager
from app.services.performance_logger import performance_logger


class SwapAgent(BaseAgent):
    """Agent specialized in token swaps and DEX operations."""
    
    # Common DEX names for reference
    SUPPORTED_DEXS = [
        "Uniswap", "SushiSwap", "Curve", "Balancer",
        "PancakeSwap", "QuickSwap", "1inch", "0x"
    ]
    
    def __init__(self, tools: Optional[List[Tool]] = None):
        """
        Initialize the swap agent.
        
        Args:
            tools: Optional list of tools
        """
        config = agent_config_manager.get_config(AgentType.SWAP)
        super().__init__(
            name=config.name,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            system_prompt=config.system_prompt,
            tools=tools
        )
        self.config = config
    
    def _get_default_system_prompt(self) -> str:
        """Get the default system prompt."""
        return self.config.system_prompt
    
    async def get_swap_quote(
        self,
        query: str,
        from_token: str,
        to_token: str,
        amount: Optional[float] = None,
        wallet_address: Optional[str] = None,
        slippage_tolerance: float = 1.0,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Get swap quote and recommendations.
        
        Args:
            query: User query about swap
            from_token: Source token symbol
            to_token: Destination token symbol
            amount: Amount to swap
            wallet_address: User's wallet address
            slippage_tolerance: Max slippage percentage
            context: Additional context
            
        Returns:
            Swap quote and analysis
        """
        async with performance_logger.log_operation(
            operation_type="swap_quote",
            agent=self.name,
            model=self.model,
            from_token=from_token,
            to_token=to_token
        ) as metrics:
            try:
                # Build swap query
                enhanced_query = self._build_swap_query(
                    query, from_token, to_token, amount, 
                    wallet_address, slippage_tolerance, context
                )
                
                # Get quote using tools if available
                if self.tools:
                    response, tool_calls = await self.invoke_with_tools(
                        enhanced_query,
                        context=context
                    )
                    metrics.metadata["tools_used"] = len(tool_calls)
                    metrics.metadata["has_quote"] = True
                else:
                    response = await self.invoke(enhanced_query, context=context)
                    metrics.metadata["tools_used"] = 0
                    metrics.metadata["has_quote"] = False
                
                return response.content if hasattr(response, 'content') else str(response)
                
            except Exception as e:
                performance_logger.logger.error(
                    "swap_quote_failed",
                    error=str(e),
                    from_token=from_token,
                    to_token=to_token
                )
                raise
    
    def _build_swap_query(
        self,
        query: str,
        from_token: str,
        to_token: str,
        amount: Optional[float],
        wallet_address: Optional[str],
        slippage_tolerance: float,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Build enhanced swap query."""
        parts = [query]
        
        parts.append(f"\nSwap Details:")
        parts.append(f"- From: {from_token}")
        parts.append(f"- To: {to_token}")
        
        if amount:
            parts.append(f"- Amount: {amount} {from_token}")
        
        if wallet_address:
            parts.append(f"- Wallet: {wallet_address}")
        
        parts.append(f"- Max Slippage: {slippage_tolerance}%")
        
        if context:
            if "gas_price" in context:
                parts.append(f"- Current Gas Price: {context['gas_price']} gwei")
            if "urgency" in context:
                parts.append(f"- Urgency: {context['urgency']}")
        
        parts.append("\nPlease provide quote details including rates, fees, and recommendations.")
        
        return "\n".join(parts)
    
    async def analyze_swap_route(
        self,
        from_token: str,
        to_token: str,
        amount: float,
        chain_id: int = 1
    ) -> Dict[str, Any]:
        """
        Analyze the best swap route.
        
        Args:
            from_token: Source token
            to_token: Destination token
            amount: Amount to swap
            chain_id: Chain ID
            
        Returns:
            Route analysis
        """
        prompt = f"""Analyze the best swap route for:
- From: {amount} {from_token}
- To: {to_token}
- Chain: {self._get_chain_name(chain_id)}

Consider:
1. Direct pairs vs multi-hop routes
2. Liquidity depth on different DEXs
3. Gas costs for different routes
4. Historical slippage data
5. MEV protection needs

Provide detailed route analysis and recommendations."""
        
        response = await self.invoke(prompt)
        
        # Structure the analysis
        analysis = {
            "from_token": from_token,
            "to_token": to_token,
            "amount": amount,
            "chain_id": chain_id,
            "analysis": response.content if hasattr(response, 'content') else str(response),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return analysis
    
    def _get_chain_name(self, chain_id: int) -> str:
        """Get chain name from ID."""
        chains = {
            1: "Ethereum", 137: "Polygon", 10: "Optimism",
            42161: "Arbitrum", 56: "BSC", 43114: "Avalanche"
        }
        return chains.get(chain_id, f"Chain {chain_id}")
    
    async def compare_dex_quotes(
        self,
        from_token: str,
        to_token: str,
        amount: float,
        dexs_to_compare: Optional[List[str]] = None
    ) -> str:
        """
        Compare quotes across multiple DEXs.
        
        Args:
            from_token: Source token
            to_token: Destination token
            amount: Amount to swap
            dexs_to_compare: Specific DEXs to compare
            
        Returns:
            Comparison analysis
        """
        if not dexs_to_compare:
            dexs_to_compare = ["Uniswap", "SushiSwap", "Curve", "1inch"]
        
        prompt = f"""Compare swap quotes across DEXs for:
- Swap: {amount} {from_token} → {to_token}
- DEXs to compare: {', '.join(dexs_to_compare)}

For each DEX, analyze:
1. Exchange rate
2. Price impact
3. Gas costs
4. Liquidity available
5. Total cost (including fees)

Provide a comparison table and recommendation for the best option."""
        
        response = await self.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    
    async def calculate_price_impact(
        self,
        from_token: str,
        to_token: str,
        amounts: List[float]
    ) -> str:
        """
        Calculate price impact for different swap amounts.
        
        Args:
            from_token: Source token
            to_token: Destination token
            amounts: List of amounts to analyze
            
        Returns:
            Price impact analysis
        """
        prompt = f"""Calculate price impact for swapping {from_token} to {to_token}:

Amounts to analyze: {amounts}

For each amount, estimate:
1. Expected exchange rate
2. Price impact percentage
3. Effective slippage
4. Whether to split the trade
5. Recommended execution strategy

Consider current market liquidity and typical trading patterns."""
        
        response = await self.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    
    async def suggest_swap_timing(
        self,
        from_token: str,
        to_token: str,
        amount: float,
        time_preference: str = "immediate"
    ) -> str:
        """
        Suggest optimal timing for swap execution.
        
        Args:
            from_token: Source token
            to_token: Destination token
            amount: Amount to swap
            time_preference: User's time preference
            
        Returns:
            Timing suggestions
        """
        prompt = f"""Suggest optimal timing for swapping {amount} {from_token} to {to_token}:

Time preference: {time_preference}

Consider:
1. Gas price patterns (time of day/week)
2. Market volatility windows
3. Liquidity variations
4. MEV risk periods
5. Historical best execution times

Provide specific recommendations with rationale."""
        
        response = await self.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    
    async def explain_swap_fees(
        self,
        swap_data: Dict[str, Any],
        breakdown_detail: str = "standard"
    ) -> str:
        """
        Explain all fees involved in a swap.
        
        Args:
            swap_data: Swap quote data
            breakdown_detail: Level of detail
            
        Returns:
            Fee explanation
        """
        prompt = f"""Explain the fees for this swap:

Swap Data:
{json.dumps(swap_data, indent=2)}

Detail Level: {breakdown_detail}

Break down:
1. DEX trading fees (LP fees)
2. Protocol fees (if any)
3. Gas costs (in USD)
4. Price impact costs
5. MEV protection costs (if applicable)
6. Total all-in cost

Explain each component clearly and show total cost calculation."""
        
        response = await self.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    
    async def check_token_safety(
        self,
        token_address: str,
        chain_id: int = 1
    ) -> Dict[str, Any]:
        """
        Check token safety before swapping.
        
        Args:
            token_address: Token contract address
            chain_id: Chain ID
            
        Returns:
            Safety analysis
        """
        prompt = f"""Analyze the safety of this token for swapping:

Token Address: {token_address}
Chain: {self._get_chain_name(chain_id)}

Check for:
1. Known scam patterns
2. Honeypot characteristics
3. Unusual token mechanics
4. Liquidity concerns
5. Contract verification status

Provide a safety score (0-10) and detailed warnings if any."""
        
        response = await self.invoke(prompt)
        
        # Structure safety check
        return {
            "token_address": token_address,
            "chain_id": chain_id,
            "safety_analysis": response.content if hasattr(response, 'content') else str(response),
            "checked_at": datetime.utcnow().isoformat()
        }
    
    async def optimize_gas_for_swap(
        self,
        swap_params: Dict[str, Any],
        gas_price_gwei: float
    ) -> str:
        """
        Optimize gas usage for swap execution.
        
        Args:
            swap_params: Swap parameters
            gas_price_gwei: Current gas price
            
        Returns:
            Gas optimization suggestions
        """
        prompt = f"""Optimize gas usage for this swap:

Swap Parameters:
{json.dumps(swap_params, indent=2)}

Current Gas Price: {gas_price_gwei} gwei

Provide optimization strategies:
1. Best time to execute
2. Whether to use flashloan
3. Batching opportunities
4. Gas token usage
5. Transaction settings (gas limit, priority fee)

Calculate potential savings for each strategy."""
        
        response = await self.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)