"""Rebalancing suggestion agent."""

import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from langchain_core.tools import Tool

from app.agents.base import BaseAgent
from app.agents.config import AgentType, agent_config_manager
from app.services.performance_logger import performance_logger


@dataclass
class RebalanceStrategy:
    """Rebalancing strategy details."""
    name: str
    target_allocations: Dict[str, float]
    required_swaps: List[Dict[str, Any]]
    estimated_cost_usd: float
    risk_score: float
    rationale: str


class RebalancingAgent(BaseAgent):
    """Agent specialized in portfolio rebalancing strategies."""
    
    # Predefined rebalancing strategies
    STRATEGIES = {
        "equal_weight": "Distribute portfolio equally across all tokens",
        "market_cap": "Weight tokens by market capitalization",
        "risk_parity": "Balance risk contribution across tokens",
        "conservative": "Focus on stable assets with minimal volatility",
        "aggressive": "Maximize growth potential with higher risk",
        "defi_blue_chip": "Focus on established DeFi protocols",
        "yield_optimized": "Maximize yield farming opportunities"
    }
    
    def __init__(self, tools: Optional[List[Tool]] = None):
        """
        Initialize the rebalancing agent.
        
        Args:
            tools: Optional list of tools
        """
        config = agent_config_manager.get_config(AgentType.REBALANCING)
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
    
    async def suggest_rebalancing(
        self,
        query: str,
        portfolio_data: Dict[str, Any],
        strategy: Optional[str] = None,
        risk_tolerance: str = "medium",
        constraints: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Suggest portfolio rebalancing based on strategy.
        
        Args:
            query: User query about rebalancing
            portfolio_data: Current portfolio data
            strategy: Rebalancing strategy to use
            risk_tolerance: User's risk tolerance
            constraints: Optional constraints (min/max allocations, etc.)
            
        Returns:
            Rebalancing suggestions
        """
        async with performance_logger.log_operation(
            operation_type="rebalancing_suggestion",
            agent=self.name,
            model=self.model,
            strategy=strategy
        ) as metrics:
            try:
                # Build rebalancing prompt
                prompt = self._build_rebalancing_prompt(
                    query, portfolio_data, strategy, risk_tolerance, constraints
                )
                
                # Get suggestions
                if self.tools:
                    response, tool_calls = await self.invoke_with_tools(prompt)
                    metrics.metadata["tools_used"] = len(tool_calls)
                else:
                    response = await self.invoke(prompt)
                    metrics.metadata["tools_used"] = 0
                
                return response.content if hasattr(response, 'content') else str(response)
                
            except Exception as e:
                performance_logger.logger.error(
                    "rebalancing_suggestion_failed",
                    error=str(e),
                    strategy=strategy
                )
                raise
    
    def _build_rebalancing_prompt(
        self,
        query: str,
        portfolio_data: Dict[str, Any],
        strategy: Optional[str],
        risk_tolerance: str,
        constraints: Optional[Dict[str, Any]]
    ) -> str:
        """Build comprehensive rebalancing prompt."""
        parts = [query, "\nCurrent Portfolio:"]
        
        # Add portfolio summary
        if "total_value_usd" in portfolio_data:
            parts.append(f"Total Value: ${portfolio_data['total_value_usd']:,.2f}")
        
        if "tokens" in portfolio_data:
            parts.append(f"Tokens: {len(portfolio_data['tokens'])}")
            
            # Show current allocations
            parts.append("\nCurrent Allocations:")
            for token in portfolio_data.get("tokens", [])[:10]:  # Top 10
                if "value_usd" in token and portfolio_data.get("total_value_usd", 0) > 0:
                    allocation = (token["value_usd"] / portfolio_data["total_value_usd"]) * 100
                    parts.append(f"- {token['symbol']}: {allocation:.1f}%")
        
        # Add strategy and constraints
        parts.append(f"\nRisk Tolerance: {risk_tolerance}")
        
        if strategy:
            parts.append(f"Requested Strategy: {strategy}")
            if strategy in self.STRATEGIES:
                parts.append(f"Strategy Description: {self.STRATEGIES[strategy]}")
        
        if constraints:
            parts.append(f"\nConstraints: {json.dumps(constraints, indent=2)}")
        
        # Add specific instructions
        parts.append("""
Please provide:
1. Recommended target allocations
2. Required swaps to achieve targets
3. Estimated costs (gas + slippage)
4. Risk assessment of the rebalancing
5. Step-by-step execution plan
6. Alternative strategies if applicable""")
        
        return "\n".join(parts)
    
    async def analyze_rebalancing_strategies(
        self,
        portfolio_data: Dict[str, Any],
        compare_strategies: Optional[List[str]] = None
    ) -> List[RebalanceStrategy]:
        """
        Analyze multiple rebalancing strategies.
        
        Args:
            portfolio_data: Current portfolio
            compare_strategies: Strategies to compare
            
        Returns:
            List of analyzed strategies
        """
        if not compare_strategies:
            compare_strategies = ["equal_weight", "risk_parity", "defi_blue_chip"]
        
        strategies = []
        
        for strategy_name in compare_strategies:
            if strategy_name not in self.STRATEGIES:
                continue
            
            # Analyze each strategy
            prompt = f"""Analyze the {strategy_name} rebalancing strategy for this portfolio:

Portfolio Data:
{json.dumps(portfolio_data, indent=2)}

Strategy: {strategy_name} - {self.STRATEGIES[strategy_name]}

Provide a JSON response with:
{{
    "target_allocations": {{"TOKEN": percentage}},
    "required_swaps": [{{"from": "TOKEN", "to": "TOKEN", "amount_usd": value}}],
    "estimated_cost_usd": value,
    "risk_score": 0-10,
    "rationale": "explanation"
}}"""
            
            try:
                response = await self.invoke(prompt)
                
                # Parse response
                json_match = json.loads(self._extract_json(response.content))
                
                strategy = RebalanceStrategy(
                    name=strategy_name,
                    target_allocations=json_match.get("target_allocations", {}),
                    required_swaps=json_match.get("required_swaps", []),
                    estimated_cost_usd=json_match.get("estimated_cost_usd", 0),
                    risk_score=json_match.get("risk_score", 5),
                    rationale=json_match.get("rationale", "")
                )
                strategies.append(strategy)
                
            except Exception as e:
                performance_logger.logger.error(
                    "strategy_analysis_failed",
                    strategy=strategy_name,
                    error=str(e)
                )
        
        return strategies
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from text response."""
        import re
        json_match = re.search(r'\{[^{}]*\}', text, re.DOTALL)
        if json_match:
            return json_match.group()
        return "{}"
    
    async def calculate_rebalancing_impact(
        self,
        current_portfolio: Dict[str, Any],
        target_allocations: Dict[str, float],
        include_tax: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate the impact of rebalancing.
        
        Args:
            current_portfolio: Current portfolio state
            target_allocations: Target allocation percentages
            include_tax: Whether to include tax considerations
            
        Returns:
            Impact analysis
        """
        prompt = f"""Calculate the impact of rebalancing this portfolio:

Current Portfolio:
{json.dumps(current_portfolio, indent=2)}

Target Allocations:
{json.dumps(target_allocations, indent=2)}

Include Tax Considerations: {include_tax}

Analyze:
1. Number and size of required trades
2. Total transaction costs (gas + DEX fees)
3. Expected slippage impact
4. Tax implications (if applicable)
5. Time to execute all trades
6. Risk during rebalancing period

Provide specific numbers and estimates."""
        
        response = await self.invoke(prompt)
        
        # Structure the impact analysis
        impact = {
            "summary": response.content if hasattr(response, 'content') else str(response),
            "current_value": current_portfolio.get("total_value_usd", 0),
            "target_allocations": target_allocations,
            "include_tax": include_tax,
            "timestamp": performance_logger.logger.info("impact_calculated").get("timestamp")
        }
        
        return impact
    
    async def generate_execution_plan(
        self,
        portfolio_data: Dict[str, Any],
        target_allocations: Dict[str, float],
        max_slippage: float = 2.0,
        time_horizon: str = "immediate"
    ) -> str:
        """
        Generate detailed execution plan for rebalancing.
        
        Args:
            portfolio_data: Current portfolio
            target_allocations: Target allocations
            max_slippage: Maximum acceptable slippage percentage
            time_horizon: When to execute ("immediate", "1_day", "1_week")
            
        Returns:
            Execution plan
        """
        # Get swap quotes if tools available
        swap_quotes = []
        if self.tools:
            swap_tool = next((t for t in self.tools if t.name == "get_swap_quote"), None)
            if swap_tool:
                # Calculate required swaps
                # This is simplified - real implementation would be more complex
                swap_quotes.append("Swap quotes available via tools")
        
        prompt = f"""Create a detailed execution plan for rebalancing:

Current Portfolio:
{json.dumps(portfolio_data, indent=2)}

Target Allocations:
{json.dumps(target_allocations, indent=2)}

Parameters:
- Maximum Slippage: {max_slippage}%
- Time Horizon: {time_horizon}
- Available Tools: {len(self.tools) if self.tools else 0}

Create a step-by-step plan including:
1. Exact trades to execute (with amounts)
2. Optimal execution order
3. DEX recommendations for each trade
4. Gas optimization strategies
5. Risk mitigation steps
6. Monitoring requirements

Be specific and actionable."""
        
        response = await self.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    
    async def monitor_rebalancing(
        self,
        execution_id: str,
        current_state: Dict[str, Any],
        target_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Monitor ongoing rebalancing execution.
        
        Args:
            execution_id: ID of the rebalancing execution
            current_state: Current portfolio state
            target_state: Target portfolio state
            
        Returns:
            Monitoring status
        """
        # Calculate progress
        progress = self._calculate_rebalancing_progress(current_state, target_state)
        
        status = {
            "execution_id": execution_id,
            "progress_percentage": progress,
            "current_state": current_state,
            "target_state": target_state,
            "status": "in_progress" if progress < 95 else "completed",
            "recommendations": []
        }
        
        # Get AI recommendations if needed
        if progress < 95:
            prompt = f"""Monitor this rebalancing execution:

Progress: {progress}%
Current State: {json.dumps(current_state, indent=2)}
Target State: {json.dumps(target_state, indent=2)}

Provide:
1. Assessment of progress
2. Any concerns or risks
3. Recommendations for next steps"""
            
            response = await self.invoke(prompt)
            status["ai_assessment"] = response.content if hasattr(response, 'content') else str(response)
        
        return status
    
    def _calculate_rebalancing_progress(
        self,
        current: Dict[str, Any],
        target: Dict[str, Any]
    ) -> float:
        """Calculate rebalancing progress percentage."""
        # Simplified progress calculation
        # Real implementation would compare actual vs target allocations
        return 50.0  # Placeholder