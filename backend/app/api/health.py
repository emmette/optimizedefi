from fastapi import APIRouter, status
from datetime import datetime
import aiohttp

from app.core.config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "OptimizeDeFi API"
    }

@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check including external services"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "api": True,
            "1inch_api": False,
            "redis": False
        }
    }
    
    # Check 1inch API
    try:
        headers = {"Authorization": f"Bearer {settings.ONEINCH_API_KEY}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{settings.ONEINCH_BASE_URL}/chains",
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                health_status["checks"]["1inch_api"] = response.status == 200
    except Exception as e:
        health_status["checks"]["1inch_api"] = False
        health_status["errors"] = {"1inch_api": str(e)}
    
    # Update overall status
    if not all(health_status["checks"].values()):
        health_status["status"] = "degraded"
    
    return health_status