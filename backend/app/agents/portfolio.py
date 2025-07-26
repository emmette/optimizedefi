"""Portfolio analysis agent."""

import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import Tool

from app.agents.base import BaseAgent
from app.agents.config import AgentType, agent_config_manager
from app.services.performance_logger import performance_logger


class PortfolioAgent(BaseAgent):
    """Agent specialized in portfolio analysis and insights."""
    
    def __init__(self, tools: Optional[List[Tool]] = None):
        """
        Initialize the portfolio agent.
        
        Args:
            tools: Optional list of tools (will be set by workflow)
        """
        config = agent_config_manager.get_config(AgentType.PORTFOLIO)
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
    
    async def analyze_portfolio(
        self,
        query: str,
        wallet_address: Optional[str] = None,
        chain_ids: Optional[List[int]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Analyze portfolio based on user query.
        
        Args:
            query: User query about portfolio
            wallet_address: Wallet address to analyze
            chain_ids: Chain IDs to include
            context: Additional context
            
        Returns:
            Analysis response
        """
        # Track operation
        async with performance_logger.log_operation(
            operation_type="portfolio_analysis",
            agent=self.name,
            model=self.model,
            wallet_address=wallet_address
        ) as metrics:
            try:
                # Build enhanced query
                enhanced_query = self._build_enhanced_query(
                    query, wallet_address, chain_ids, context
                )
                
                # Check if we have tools
                if self.tools:
                    # Use tools to get portfolio data
                    response, tool_calls = await self.invoke_with_tools(
                        enhanced_query,
                        context=context
                    )
                    
                    metrics.metadata["tools_used"] = len(tool_calls)
                    metrics.metadata["has_data"] = True
                else:
                    # No tools, provide general response
                    response = await self.invoke(enhanced_query, context=context)
                    metrics.metadata["tools_used"] = 0
                    metrics.metadata["has_data"] = False
                
                # Extract response text
                if hasattr(response, 'content'):
                    return response.content
                else:
                    return str(response)
                    
            except Exception as e:
                performance_logger.logger.error(
                    "portfolio_analysis_failed",
                    error=str(e),
                    wallet_address=wallet_address
                )
                raise
    
    def _build_enhanced_query(
        self,
        query: str,
        wallet_address: Optional[str] = None,
        chain_ids: Optional[List[int]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build enhanced query with context."""
        parts = [query]
        
        if wallet_address:
            parts.append(f"\nWallet address: {wallet_address}")
        
        if chain_ids:
            chain_names = self._get_chain_names(chain_ids)
            parts.append(f"Chains to analyze: {', '.join(chain_names)}")
        
        if context:
            if "current_prices" in context:
                parts.append(f"Current market data available: Yes")
            if "user_preferences" in context:
                parts.append(f"User preferences: {json.dumps(context['user_preferences'])}")
        
        return "\n".join(parts)
    
    def _get_chain_names(self, chain_ids: List[int]) -> List[str]:
        """Get chain names from IDs."""
        chain_map = {
            1: "Ethereum",
            137: "Polygon",
            10: "Optimism",
            42161: "Arbitrum",
            56: "BSC",
            43114: "Avalanche"
        }
        return [chain_map.get(cid, f"Chain {cid}") for cid in chain_ids]
    
    async def get_portfolio_summary(
        self,
        wallet_address: str,
        chain_ids: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Get a structured portfolio summary.
        
        Args:
            wallet_address: Wallet to analyze
            chain_ids: Chains to include
            
        Returns:
            Portfolio summary data
        """
        if not self.tools:
            return {
                "error": "No tools available for portfolio data",
                "wallet_address": wallet_address
            }
        
        # Use get_portfolio tool
        get_portfolio_tool = next(
            (t for t in self.tools if t.name == "get_portfolio"),
            None
        )
        
        if not get_portfolio_tool:
            return {
                "error": "Portfolio tool not available",
                "wallet_address": wallet_address
            }
        
        try:
            # Call tool directly
            portfolio_data = await get_portfolio_tool.ainvoke({
                "wallet_address": wallet_address,
                "chain_ids": chain_ids
            })
            
            # Process and return
            return self._process_portfolio_data(portfolio_data)
            
        except Exception as e:
            performance_logger.logger.error(
                "portfolio_summary_failed",
                error=str(e),
                wallet_address=wallet_address
            )
            return {
                "error": str(e),
                "wallet_address": wallet_address
            }
    
    def _process_portfolio_data(self, raw_data: Any) -> Dict[str, Any]:
        """Process raw portfolio data into structured format."""
        if isinstance(raw_data, str):
            try:
                data = json.loads(raw_data)
            except:
                return {"error": "Invalid portfolio data format"}
        else:
            data = raw_data
        
        # Structure the response
        summary = {
            "total_value_usd": data.get("total_value_usd", 0),
            "chain_breakdown": data.get("chain_breakdown", {}),
            "top_holdings": data.get("top_holdings", []),
            "token_count": len(data.get("tokens", [])),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        return summary
    
    async def analyze_holdings(
        self,
        query: str,
        portfolio_data: Dict[str, Any],
        focus: Optional[str] = None
    ) -> str:
        """
        Analyze specific aspects of holdings.
        
        Args:
            query: Analysis query
            portfolio_data: Portfolio data
            focus: Focus area (e.g., "risk", "performance", "concentration")
            
        Returns:
            Analysis response
        """
        # Build analysis prompt
        prompt = f"""Analyze the following portfolio data based on the user's query.

User Query: {query}
Focus Area: {focus or "general analysis"}

Portfolio Data:
{json.dumps(portfolio_data, indent=2)}

Provide insights on:
1. Portfolio composition and diversification
2. Risk factors and concentration
3. Notable holdings and their significance
4. Recommendations based on the data

Keep the analysis concise and actionable."""
        
        response = await self.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    
    async def compare_portfolios(
        self,
        wallet1: str,
        wallet2: str,
        chain_ids: Optional[List[int]] = None
    ) -> str:
        """
        Compare two portfolios.
        
        Args:
            wallet1: First wallet address
            wallet2: Second wallet address
            chain_ids: Chains to compare
            
        Returns:
            Comparison analysis
        """
        if not self.tools:
            return "Portfolio comparison requires access to portfolio data tools."
        
        try:
            # Get both portfolios
            portfolio1 = await self.get_portfolio_summary(wallet1, chain_ids)
            portfolio2 = await self.get_portfolio_summary(wallet2, chain_ids)
            
            # Build comparison prompt
            prompt = f"""Compare these two DeFi portfolios:

Portfolio 1 ({wallet1[:8]}...{wallet1[-6:]}):
{json.dumps(portfolio1, indent=2)}

Portfolio 2 ({wallet2[:8]}...{wallet2[-6:]}):
{json.dumps(portfolio2, indent=2)}

Provide a comparison including:
1. Total value differences
2. Asset allocation strategies
3. Risk profiles
4. Diversification levels
5. Key differences in holdings"""
            
            response = await self.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
            
        except Exception as e:
            return f"Failed to compare portfolios: {str(e)}"
    
    async def suggest_improvements(
        self,
        portfolio_data: Dict[str, Any],
        risk_tolerance: str = "medium",
        goals: Optional[List[str]] = None
    ) -> str:
        """
        Suggest portfolio improvements.
        
        Args:
            portfolio_data: Current portfolio data
            risk_tolerance: User's risk tolerance
            goals: Investment goals
            
        Returns:
            Improvement suggestions
        """
        goals_str = ", ".join(goals) if goals else "general portfolio optimization"
        
        prompt = f"""Based on this portfolio data, suggest improvements:

Portfolio Data:
{json.dumps(portfolio_data, indent=2)}

User Profile:
- Risk Tolerance: {risk_tolerance}
- Goals: {goals_str}

Provide specific, actionable suggestions for:
1. Improving diversification
2. Optimizing for the stated goals
3. Managing risk appropriately
4. Potential rebalancing opportunities

Consider gas costs and practical implementation."""
        
        response = await self.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    
    async def explain_token(
        self,
        token_symbol: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Explain a specific token in the portfolio.
        
        Args:
            token_symbol: Token to explain
            context: Additional context
            
        Returns:
            Token explanation
        """
        prompt = f"""Explain the {token_symbol} token for a DeFi investor:

1. What is {token_symbol} and its primary use case?
2. Key risks associated with holding {token_symbol}
3. Historical performance and volatility
4. Role in a DeFi portfolio
5. Any important considerations

Keep the explanation clear and focused on practical information."""
        
        if context and "token_data" in context:
            prompt += f"\n\nAdditional token data:\n{json.dumps(context['token_data'], indent=2)}"
        
        response = await self.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)