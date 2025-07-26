"""LangChain wrappers for MCP tools."""

import json
from typing import Dict, Any, Optional, List, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, ToolException
from langchain_core.callbacks import CallbackManagerForToolRun

from app.mcp.server import mcp_server
from app.services.performance_logger import performance_logger


# Input schemas for tools
class GetPortfolioInput(BaseModel):
    """Input schema for get_portfolio tool."""
    wallet_address: str = Field(description="Ethereum wallet address")
    chain_ids: Optional[List[int]] = Field(
        default=None,
        description="List of chain IDs to query (defaults to all supported chains)"
    )


class AnalyzePortfolioInput(BaseModel):
    """Input schema for analyze_portfolio tool."""
    wallet_address: str = Field(description="Ethereum wallet address")
    analysis_type: Optional[str] = Field(
        default="comprehensive",
        description="Type of analysis: comprehensive, risk, performance"
    )


class GetTokenPriceInput(BaseModel):
    """Input schema for get_token_price tool."""
    token_symbol: str = Field(description="Token symbol (e.g., ETH, USDC)")
    chain_id: Optional[int] = Field(
        default=1,
        description="Chain ID (defaults to Ethereum mainnet)"
    )


class GetSwapQuoteInput(BaseModel):
    """Input schema for get_swap_quote tool."""
    from_token: str = Field(description="Source token symbol")
    to_token: str = Field(description="Destination token symbol")
    amount: float = Field(description="Amount to swap")
    chain_id: Optional[int] = Field(default=1, description="Chain ID")
    slippage: Optional[float] = Field(
        default=1.0,
        description="Maximum slippage tolerance in percentage"
    )


class GetSupportedTokensInput(BaseModel):
    """Input schema for get_supported_tokens tool."""
    chain_id: Optional[int] = Field(
        default=1,
        description="Chain ID to get tokens for"
    )


# LangChain tool wrappers
class GetPortfolioTool(BaseTool):
    """Tool for getting user's DeFi portfolio."""
    
    name: str = "get_portfolio"
    description: str = """Get a user's DeFi portfolio across multiple chains.
    Returns token balances, values, and total portfolio value."""
    args_schema: Type[BaseModel] = GetPortfolioInput
    
    def _run(
        self,
        wallet_address: str,
        chain_ids: Optional[List[int]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Sync implementation (not used, but required)."""
        raise NotImplementedError("Use async implementation")
    
    async def _arun(
        self,
        wallet_address: str,
        chain_ids: Optional[List[int]] = None,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Get portfolio data asynchronously."""
        try:
            # Log tool execution
            async with performance_logger.log_operation(
                operation_type="tool_execution",
                tool_name=self.name,
                wallet_address=wallet_address
            ) as metrics:
                # Get the MCP tool
                tool = next(
                    (t for t in mcp_server.tools if t.name == "get_portfolio"),
                    None
                )
                
                if not tool:
                    raise ToolException("Portfolio tool not available")
                
                # Execute tool
                result = await tool.run({
                    "wallet_address": wallet_address,
                    "chain_ids": chain_ids
                })
                
                metrics.metadata["success"] = True
                metrics.metadata["result_size"] = len(str(result))
                
                # Return JSON string for LangChain
                if isinstance(result, dict):
                    return json.dumps(result, indent=2)
                return str(result)
                
        except Exception as e:
            performance_logger.logger.error(
                "tool_execution_failed",
                tool_name=self.name,
                error=str(e)
            )
            raise ToolException(f"Failed to get portfolio: {str(e)}")


class AnalyzePortfolioTool(BaseTool):
    """Tool for analyzing a DeFi portfolio."""
    
    name: str = "analyze_portfolio"
    description: str = """Analyze a DeFi portfolio for risk, diversification, and opportunities.
    Provides insights and recommendations."""
    args_schema: Type[BaseModel] = AnalyzePortfolioInput
    
    def _run(
        self,
        wallet_address: str,
        analysis_type: Optional[str] = "comprehensive",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Sync implementation (not used)."""
        raise NotImplementedError("Use async implementation")
    
    async def _arun(
        self,
        wallet_address: str,
        analysis_type: Optional[str] = "comprehensive",
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Analyze portfolio asynchronously."""
        try:
            async with performance_logger.log_operation(
                operation_type="tool_execution",
                tool_name=self.name,
                analysis_type=analysis_type
            ):
                # Get the MCP tool
                tool = next(
                    (t for t in mcp_server.tools if t.name == "analyze_portfolio"),
                    None
                )
                
                if not tool:
                    raise ToolException("Analysis tool not available")
                
                # Execute tool
                result = await tool.run({
                    "wallet_address": wallet_address,
                    "analysis_type": analysis_type
                })
                
                if isinstance(result, dict):
                    return json.dumps(result, indent=2)
                return str(result)
                
        except Exception as e:
            raise ToolException(f"Failed to analyze portfolio: {str(e)}")


class GetTokenPriceTool(BaseTool):
    """Tool for getting token prices."""
    
    name: str = "get_token_price"
    description: str = """Get current price for a token on a specific chain.
    Returns price in USD and 24h change."""
    args_schema: Type[BaseModel] = GetTokenPriceInput
    
    def _run(
        self,
        token_symbol: str,
        chain_id: Optional[int] = 1,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Sync implementation (not used)."""
        raise NotImplementedError("Use async implementation")
    
    async def _arun(
        self,
        token_symbol: str,
        chain_id: Optional[int] = 1,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Get token price asynchronously."""
        try:
            async with performance_logger.log_operation(
                operation_type="tool_execution",
                tool_name=self.name,
                token_symbol=token_symbol
            ):
                # Get the MCP tool
                tool = next(
                    (t for t in mcp_server.tools if t.name == "get_token_price"),
                    None
                )
                
                if not tool:
                    raise ToolException("Price tool not available")
                
                # Execute tool
                result = await tool.run({
                    "token_symbol": token_symbol,
                    "chain_id": chain_id
                })
                
                if isinstance(result, dict):
                    return json.dumps(result, indent=2)
                return str(result)
                
        except Exception as e:
            raise ToolException(f"Failed to get token price: {str(e)}")


class GetSwapQuoteTool(BaseTool):
    """Tool for getting swap quotes."""
    
    name: str = "get_swap_quote"
    description: str = """Get a quote for swapping tokens using 1inch aggregator.
    Returns best route, expected output, and gas estimates."""
    args_schema: Type[BaseModel] = GetSwapQuoteInput
    
    def _run(
        self,
        from_token: str,
        to_token: str,
        amount: float,
        chain_id: Optional[int] = 1,
        slippage: Optional[float] = 1.0,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Sync implementation (not used)."""
        raise NotImplementedError("Use async implementation")
    
    async def _arun(
        self,
        from_token: str,
        to_token: str,
        amount: float,
        chain_id: Optional[int] = 1,
        slippage: Optional[float] = 1.0,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Get swap quote asynchronously."""
        try:
            async with performance_logger.log_operation(
                operation_type="tool_execution",
                tool_name=self.name,
                from_token=from_token,
                to_token=to_token,
                amount=amount
            ):
                # Get the MCP tool
                tool = next(
                    (t for t in mcp_server.tools if t.name == "get_swap_quote"),
                    None
                )
                
                if not tool:
                    raise ToolException("Swap tool not available")
                
                # Execute tool
                result = await tool.run({
                    "from_token": from_token,
                    "to_token": to_token,
                    "amount": amount,
                    "chain_id": chain_id,
                    "slippage": slippage
                })
                
                if isinstance(result, dict):
                    return json.dumps(result, indent=2)
                return str(result)
                
        except Exception as e:
            raise ToolException(f"Failed to get swap quote: {str(e)}")


class GetSupportedTokensTool(BaseTool):
    """Tool for getting supported tokens."""
    
    name: str = "get_supported_tokens"
    description: str = """Get list of supported tokens on a chain.
    Returns token addresses, symbols, and metadata."""
    args_schema: Type[BaseModel] = GetSupportedTokensInput
    
    def _run(
        self,
        chain_id: Optional[int] = 1,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Sync implementation (not used)."""
        raise NotImplementedError("Use async implementation")
    
    async def _arun(
        self,
        chain_id: Optional[int] = 1,
        run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Get supported tokens asynchronously."""
        try:
            async with performance_logger.log_operation(
                operation_type="tool_execution",
                tool_name=self.name,
                chain_id=chain_id
            ):
                # Get the MCP tool
                tool = next(
                    (t for t in mcp_server.tools if t.name == "get_supported_tokens"),
                    None
                )
                
                if not tool:
                    raise ToolException("Token list tool not available")
                
                # Execute tool
                result = await tool.run({
                    "chain_id": chain_id
                })
                
                if isinstance(result, dict):
                    return json.dumps(result, indent=2)
                return str(result)
                
        except Exception as e:
            raise ToolException(f"Failed to get supported tokens: {str(e)}")


# Tool registry
LANGCHAIN_TOOLS = [
    GetPortfolioTool(),
    AnalyzePortfolioTool(),
    GetTokenPriceTool(),
    GetSwapQuoteTool(),
    GetSupportedTokensTool(),
]


def get_tools_for_agent(agent_type: str) -> List[BaseTool]:
    """
    Get appropriate tools for an agent type.
    
    Args:
        agent_type: Type of agent
        
    Returns:
        List of LangChain tools
    """
    tool_mapping = {
        "portfolio": ["get_portfolio", "analyze_portfolio", "get_token_price"],
        "rebalancing": ["get_portfolio", "analyze_portfolio", "get_token_price", "get_swap_quote"],
        "swap": ["get_swap_quote", "get_supported_tokens", "get_token_price"],
        "general": ["get_token_price", "get_supported_tokens"],
    }
    
    agent_tool_names = tool_mapping.get(agent_type, [])
    
    return [
        tool for tool in LANGCHAIN_TOOLS
        if tool.name in agent_tool_names
    ]