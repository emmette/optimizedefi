"""Custom middleware for the application."""

from typing import Optional
from fastapi import Request, HTTPException
from fastapi.security.utils import get_authorization_scheme_param
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.auth import verify_token, rate_limiter


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware that validates JWT tokens from cookies or headers.
    """
    
    def __init__(self, app, exclude_paths: Optional[list[str]] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/api/health",
            "/api/auth/nonce",
            "/api/auth/login",
            "/docs",
            "/openapi.json",
            "/redoc"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Skip auth for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Try to get token from cookie first
        token = request.cookies.get("access_token")
        
        # If not in cookie, try Authorization header
        if not token:
            authorization = request.headers.get("Authorization")
            if authorization:
                scheme, token = get_authorization_scheme_param(authorization)
                if scheme.lower() != "bearer":
                    token = None
        
        # If we have a token, verify it
        if token:
            token_data = verify_token(token)
            if token_data:
                # Add user info to request state
                request.state.user = token_data
            else:
                # Invalid token
                if request.url.path.startswith("/api/"):
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Invalid authentication credentials"}
                    )
        
        # For API routes, require authentication unless excluded or read-only
        # Portfolio GET endpoints can be accessed without auth
        is_portfolio_get = (request.method == "GET" and 
                           (request.url.path.startswith("/api/portfolio/") or
                            "/portfolio/" in request.url.path))
        
        if (request.url.path.startswith("/api/") and 
            not hasattr(request.state, "user") and
            not is_portfolio_get):
            return JSONResponse(
                status_code=401,
                content={"detail": "Authentication required"}
            )
        
        response = await call_next(request)
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware based on IP address or wallet address.
    """
    
    def __init__(self, app, requests_per_hour: int = 1000):
        super().__init__(app)
        self.requests_per_hour = requests_per_hour
    
    async def dispatch(self, request: Request, call_next):
        # Get identifier (wallet address if authenticated, otherwise IP)
        identifier = None
        
        # Check if user is authenticated
        if hasattr(request.state, "user") and request.state.user:
            identifier = request.state.user.address
        else:
            # Use IP address
            if request.client:
                identifier = request.client.host
            else:
                # Fallback to forwarded IP
                forwarded = request.headers.get("X-Forwarded-For")
                if forwarded:
                    identifier = forwarded.split(",")[0].strip()
        
        if identifier:
            # Check rate limit
            if not rate_limiter.check_rate_limit(identifier):
                remaining = rate_limiter.get_remaining_requests(identifier)
                return JSONResponse(
                    status_code=429,
                    content={"detail": f"Rate limit exceeded. {remaining} requests remaining."},
                    headers={
                        "X-RateLimit-Limit": str(rate_limiter.max_requests),
                        "X-RateLimit-Remaining": str(remaining),
                        "X-RateLimit-Reset": str(int(rate_limiter.window_seconds))
                    }
                )
        
        response = await call_next(request)
        
        # Add rate limit headers to response
        if identifier:
            remaining = rate_limiter.get_remaining_requests(identifier)
            response.headers["X-RateLimit-Limit"] = str(rate_limiter.max_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(rate_limiter.window_seconds))
        
        return response