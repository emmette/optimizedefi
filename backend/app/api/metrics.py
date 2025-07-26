"""Protected metrics API endpoints for admin users."""

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from app.core.auth import get_current_user, TokenData
from app.core.admin import require_admin
from app.services.metrics import metrics_collector
from app.services.cost_calculator import cost_calculator
from app.services.rate_limit_manager import rate_limit_manager
from app.services.memory_manager import memory_manager
from app.agents.config import agent_config_manager

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/summary")
async def get_metrics_summary(
    current_user: TokenData = Depends(require_admin)
) -> Dict[str, Any]:
    """
    Get overall metrics summary (admin only).
    
    Returns comprehensive metrics across all services.
    """
    # Get metrics from various services
    ai_metrics = await metrics_collector.get_metrics_summary()
    rate_limits = await rate_limit_manager.get_status()
    
    # Get model info
    model_usage = agent_config_manager.get_model_usage()
    
    # Compile summary
    summary = {
        "timestamp": datetime.utcnow().isoformat(),
        "ai_metrics": ai_metrics,
        "rate_limits": rate_limits,
        "model_usage": model_usage,
        "admin_user": current_user.address
    }
    
    return summary


@router.get("/agents")
async def get_agent_metrics(
    current_user: TokenData = Depends(require_admin)
) -> Dict[str, Any]:
    """Get metrics for all agents."""
    metrics_summary = await metrics_collector.get_metrics_summary()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "agents": metrics_summary.get("agents", {}),
        "total_requests": metrics_summary.get("overall", {}).get("total_requests", 0)
    }


@router.get("/agents/{agent_type}")
async def get_specific_agent_metrics(
    agent_type: str,
    current_user: TokenData = Depends(require_admin)
) -> Dict[str, Any]:
    """Get metrics for a specific agent."""
    # Get agent config to verify it exists
    try:
        from app.agents.config import AgentType
        agent_enum = AgentType(agent_type)
        config = agent_config_manager.get_config(agent_enum)
    except:
        raise HTTPException(status_code=404, detail=f"Agent type '{agent_type}' not found")
    
    # Get metrics
    metrics = await metrics_collector.get_agent_metrics(config.name)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "agent_type": agent_type,
        "agent_name": config.name,
        "metrics": metrics,
        "configuration": {
            "model": config.model,
            "temperature": config.temperature,
            "tools": config.tools
        }
    }


@router.get("/costs")
async def get_cost_metrics(
    current_user: TokenData = Depends(require_admin),
    hours: int = 24
) -> Dict[str, Any]:
    """Get cost breakdown and trends."""
    # Get metrics summary
    metrics_summary = await metrics_collector.get_metrics_summary()
    
    # Calculate costs by model
    costs_by_model = {}
    for model, model_metrics in metrics_summary.get("models", {}).items():
        if "cost" in model_metrics:
            costs_by_model[model] = {
                "total_cost": model_metrics["cost"],
                "requests": model_metrics.get("requests", 0),
                "avg_cost_per_request": (
                    model_metrics["cost"] / model_metrics["requests"]
                    if model_metrics.get("requests", 0) > 0 else 0
                )
            }
    
    # Calculate costs by agent
    costs_by_agent = {}
    for agent, agent_metrics in metrics_summary.get("agents", {}).items():
        if "cost" in agent_metrics:
            costs_by_agent[agent] = agent_metrics["cost"]
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "time_window_hours": hours,
        "total_cost": metrics_summary.get("overall", {}).get("total_cost", 0),
        "costs_by_model": costs_by_model,
        "costs_by_agent": costs_by_agent,
        "currency": "USD"
    }


@router.get("/rate-limits")
async def get_rate_limit_status(
    current_user: TokenData = Depends(require_admin),
    model: Optional[str] = None
) -> Dict[str, Any]:
    """Get current rate limit status."""
    status = await rate_limit_manager.get_status(model)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "rate_limits": status
    }


@router.post("/rate-limits/{model}/reset")
async def reset_model_rate_limits(
    model: str,
    current_user: TokenData = Depends(require_admin)
) -> Dict[str, Any]:
    """Reset rate limits for a specific model (admin only)."""
    await rate_limit_manager.reset_model_limits(model)
    
    return {
        "status": "success",
        "message": f"Rate limits reset for model: {model}",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/models")
async def get_model_info(
    current_user: TokenData = Depends(require_admin)
) -> Dict[str, Any]:
    """Get information about available models and their pricing."""
    # Get all models from cost calculator
    models = await cost_calculator.get_all_models()
    
    # Get current model usage
    model_usage = agent_config_manager.get_model_usage()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "models": models,
        "model_usage": model_usage
    }


@router.get("/sessions")
async def get_active_sessions(
    current_user: TokenData = Depends(require_admin)
) -> Dict[str, Any]:
    """Get information about active chat sessions."""
    # Get all sessions
    sessions_info = []
    for session_id, session in memory_manager.sessions.items():
        metrics = await memory_manager.get_session_metrics(session_id)
        sessions_info.append(metrics)
    
    # Sort by last activity
    sessions_info.sort(key=lambda x: x.get("last_activity", ""), reverse=True)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "active_sessions": len(sessions_info),
        "sessions": sessions_info
    }


@router.post("/reset")
async def reset_all_metrics(
    current_user: TokenData = Depends(require_admin),
    confirm: bool = False
) -> Dict[str, Any]:
    """Reset all metrics (admin only, requires confirmation)."""
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Confirmation required. Set confirm=true to reset all metrics."
        )
    
    # Reset metrics
    await metrics_collector.reset_metrics()
    
    return {
        "status": "success",
        "message": "All metrics have been reset",
        "timestamp": datetime.utcnow().isoformat(),
        "reset_by": current_user.address
    }


@router.get("/performance")
async def get_performance_metrics(
    current_user: TokenData = Depends(require_admin),
    hours: int = 1
) -> Dict[str, Any]:
    """Get performance metrics over time window."""
    metrics_summary = await metrics_collector.get_metrics_summary()
    
    # Extract performance data
    performance = {
        "timestamp": datetime.utcnow().isoformat(),
        "time_window_hours": hours,
        "overall": {
            "average_duration_ms": metrics_summary.get("overall", {}).get("average_duration", 0) * 1000,
            "total_requests": metrics_summary.get("overall", {}).get("total_requests", 0),
            "requests_per_hour": (
                metrics_summary.get("overall", {}).get("total_requests", 0) / hours
                if hours > 0 else 0
            )
        },
        "by_agent": {},
        "by_model": {}
    }
    
    # Add agent performance
    for agent, agent_metrics in metrics_summary.get("agents", {}).items():
        performance["by_agent"][agent] = {
            "average_duration_ms": agent_metrics.get("average_duration", 0) * 1000,
            "requests": agent_metrics.get("requests", 0)
        }
    
    # Add model performance
    for model, model_metrics in metrics_summary.get("models", {}).items():
        performance["by_model"][model] = {
            "average_duration_ms": model_metrics.get("average_duration", 0) * 1000,
            "requests": model_metrics.get("requests", 0),
            "rate_limit_hits": model_metrics.get("rate_limit_hits", 0)
        }
    
    return performance