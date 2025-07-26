"""MCP (Model Context Protocol) API endpoints."""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.core.auth import get_current_user, TokenData
from app.mcp.server import mcp_server


router = APIRouter()


class MCPRequest(BaseModel):
    """MCP request model."""
    method: str
    params: Optional[Dict[str, Any]] = {}
    id: Optional[str] = None


class MCPResponse(BaseModel):
    """MCP response model."""
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    id: Optional[str] = None


@router.post("/", response_model=MCPResponse)
async def handle_mcp_request(
    request: MCPRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Handle MCP protocol requests.
    
    This endpoint processes Model Context Protocol requests for AI agents
    to interact with 1inch APIs and portfolio services.
    
    Args:
        request: MCP request with method and parameters
        current_user: Authenticated user
        
    Returns:
        MCP response with result or error
    """
    try:
        result = await mcp_server.handle_request(request.dict())
        
        # Add user context to certain operations
        if request.method == "tools/execute":
            tool_name = request.params.get("name")
            # For portfolio operations, default to user's address if not specified
            if tool_name in ["get_portfolio", "analyze_portfolio"]:
                if "arguments" in request.params:
                    if "address" not in request.params["arguments"]:
                        request.params["arguments"]["address"] = current_user.address
        
        return MCPResponse(
            result=result,
            id=request.id
        )
        
    except Exception as e:
        return MCPResponse(
            error=str(e),
            id=request.id
        )


@router.get("/tools")
async def list_tools(
    _: TokenData = Depends(get_current_user)
):
    """
    List available MCP tools.
    
    Returns:
        List of available tools with their descriptions and parameters
    """
    tools = await mcp_server.list_tools()
    return {"tools": tools}


@router.post("/tools/{tool_name}/execute")
async def execute_tool(
    tool_name: str,
    params: Dict[str, Any],
    current_user: TokenData = Depends(get_current_user)
):
    """
    Execute a specific MCP tool.
    
    Args:
        tool_name: Name of the tool to execute
        params: Tool parameters
        current_user: Authenticated user
        
    Returns:
        Tool execution result
    """
    # For portfolio tools, default to user's address if not specified
    if tool_name in ["get_portfolio", "analyze_portfolio"] and "address" not in params:
        params["address"] = current_user.address
    
    result = await mcp_server.execute_tool(tool_name, params)
    
    if "error" in result and not result.get("result", {}).get("success"):
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result