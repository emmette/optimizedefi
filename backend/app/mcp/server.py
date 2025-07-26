"""MCP (Model Context Protocol) Server for 1inch integration."""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from app.services.oneinch import oneinch_service
from app.services.portfolio_metrics import portfolio_metrics_service
from app.core.auth import validate_ethereum_address


class MCPTool:
    """Base class for MCP tools."""
    
    def __init__(self, name: str, description: str, parameters: Dict[str, Any]):
        self.name = name
        self.description = description
        self.parameters = parameters
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        raise NotImplementedError
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary for API response."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class GetPortfolioTool(MCPTool):
    """Tool for fetching portfolio data."""
    
    def __init__(self):
        super().__init__(
            name="get_portfolio",
            description="Fetch portfolio data for a wallet address across multiple chains",
            parameters={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Ethereum wallet address"
                    },
                    "chains": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Chain IDs to query (default: [1, 137, 10, 42161])"
                    }
                },
                "required": ["address"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute portfolio fetch."""
        address = params.get("address")
        chains = params.get("chains", [1, 137, 10, 42161])
        
        if not validate_ethereum_address(address):
            return {"error": "Invalid Ethereum address"}
        
        try:
            async with oneinch_service as service:
                portfolio_data = await service.get_multi_chain_portfolio(address, chains)
            
            # Add metrics
            portfolio_data["metrics"] = {
                "diversification_score": portfolio_metrics_service.calculate_diversification_score(portfolio_data),
                "risk_assessment": portfolio_metrics_service.calculate_risk_score(portfolio_data)
            }
            
            return {"success": True, "data": portfolio_data}
        except Exception as e:
            return {"error": str(e)}


class GetTokenPriceTool(MCPTool):
    """Tool for fetching token prices."""
    
    def __init__(self):
        super().__init__(
            name="get_token_price",
            description="Get current price for tokens on a specific chain",
            parameters={
                "type": "object",
                "properties": {
                    "chain_id": {
                        "type": "integer",
                        "description": "Chain ID (1=Ethereum, 137=Polygon, etc.)"
                    },
                    "token_addresses": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Token contract addresses"
                    }
                },
                "required": ["chain_id", "token_addresses"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute price fetch."""
        chain_id = params.get("chain_id")
        token_addresses = params.get("token_addresses", [])
        
        try:
            async with oneinch_service as service:
                prices = await service.get_token_prices(chain_id, token_addresses)
            
            return {"success": True, "data": prices}
        except Exception as e:
            return {"error": str(e)}


class GetSwapQuoteTool(MCPTool):
    """Tool for getting swap quotes."""
    
    def __init__(self):
        super().__init__(
            name="get_swap_quote",
            description="Get a swap quote from 1inch",
            parameters={
                "type": "object",
                "properties": {
                    "chain_id": {
                        "type": "integer",
                        "description": "Chain ID"
                    },
                    "from_token": {
                        "type": "string",
                        "description": "Source token address"
                    },
                    "to_token": {
                        "type": "string",
                        "description": "Destination token address"
                    },
                    "amount": {
                        "type": "string",
                        "description": "Amount to swap (in smallest unit)"
                    },
                    "from_address": {
                        "type": "string",
                        "description": "User's wallet address"
                    }
                },
                "required": ["chain_id", "from_token", "to_token", "amount", "from_address"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute swap quote."""
        try:
            async with oneinch_service as service:
                quote = await service.get_quote(**params)
            
            return {"success": True, "data": quote}
        except Exception as e:
            return {"error": str(e)}


class AnalyzePortfolioTool(MCPTool):
    """Tool for analyzing portfolio metrics."""
    
    def __init__(self):
        super().__init__(
            name="analyze_portfolio",
            description="Analyze portfolio and get recommendations",
            parameters={
                "type": "object",
                "properties": {
                    "address": {
                        "type": "string",
                        "description": "Ethereum wallet address"
                    },
                    "target_allocation": {
                        "type": "object",
                        "description": "Target allocation percentages by symbol",
                        "additionalProperties": {"type": "number"}
                    }
                },
                "required": ["address"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute portfolio analysis."""
        address = params.get("address")
        target_allocation = params.get("target_allocation")
        
        if not validate_ethereum_address(address):
            return {"error": "Invalid Ethereum address"}
        
        try:
            # Fetch portfolio data
            async with oneinch_service as service:
                portfolio_data = await service.get_multi_chain_portfolio(address)
            
            # Calculate all metrics
            analysis = {
                "diversification_score": portfolio_metrics_service.calculate_diversification_score(portfolio_data),
                "risk_assessment": portfolio_metrics_service.calculate_risk_score(portfolio_data),
                "performance": portfolio_metrics_service.calculate_performance_metrics(portfolio_data),
                "rebalancing_suggestions": portfolio_metrics_service.get_rebalancing_suggestions(
                    portfolio_data, target_allocation
                ),
                "yield_metrics": portfolio_metrics_service.calculate_yield_metrics(portfolio_data)
            }
            
            return {"success": True, "data": analysis}
        except Exception as e:
            return {"error": str(e)}


class SearchTokensTool(MCPTool):
    """Tool for searching tokens on a chain."""
    
    def __init__(self):
        super().__init__(
            name="search_tokens",
            description="Search for tokens by symbol or name on a specific chain",
            parameters={
                "type": "object",
                "properties": {
                    "chain_id": {
                        "type": "integer",
                        "description": "Chain ID"
                    },
                    "query": {
                        "type": "string",
                        "description": "Search query (symbol or name)"
                    }
                },
                "required": ["chain_id", "query"]
            }
        )
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute token search."""
        chain_id = params.get("chain_id")
        query = params.get("query", "").lower()
        
        try:
            async with oneinch_service as service:
                tokens = await service.get_tokens_info(chain_id)
            
            # Filter tokens by query
            results = []
            for address, token in tokens.items():
                if (query in token.get("symbol", "").lower() or 
                    query in token.get("name", "").lower()):
                    results.append({
                        "address": address,
                        "symbol": token.get("symbol"),
                        "name": token.get("name"),
                        "decimals": token.get("decimals"),
                        "logoURI": token.get("logoURI")
                    })
            
            # Sort by symbol
            results.sort(key=lambda x: x["symbol"])
            
            return {"success": True, "data": results[:20]}  # Limit to 20 results
        except Exception as e:
            return {"error": str(e)}


class MCPServer:
    """MCP Server for 1inch integration."""
    
    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}
        self._register_tools()
    
    def _register_tools(self):
        """Register all available tools."""
        tools = [
            GetPortfolioTool(),
            GetTokenPriceTool(),
            GetSwapQuoteTool(),
            AnalyzePortfolioTool(),
            SearchTokensTool()
        ]
        
        for tool in tools:
            self.tools[tool.name] = tool
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools."""
        return [tool.to_dict() for tool in self.tools.values()]
    
    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool."""
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found"}
        
        tool = self.tools[tool_name]
        
        try:
            result = await tool.execute(params)
            return {
                "tool": tool_name,
                "timestamp": datetime.utcnow().isoformat(),
                "result": result
            }
        except Exception as e:
            return {
                "tool": tool_name,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP protocol request."""
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "tools/list":
            tools = await self.list_tools()
            return {"tools": tools}
        
        elif method == "tools/execute":
            tool_name = params.get("name")
            tool_params = params.get("arguments", {})
            return await self.execute_tool(tool_name, tool_params)
        
        else:
            return {"error": f"Unknown method: {method}"}


# Global MCP server instance
mcp_server = MCPServer()