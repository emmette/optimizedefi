from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from app.core.auth import (
    verify_siwe_signature,
    create_access_token,
    verify_token,
    generate_nonce,
    validate_ethereum_address,
    rate_limiter,
    TokenData
)
from app.core.config import settings


router = APIRouter()
security = HTTPBearer()


class NonceRequest(BaseModel):
    """Request model for nonce generation."""
    address: str


class NonceResponse(BaseModel):
    """Response model for nonce generation."""
    nonce: str


class LoginRequest(BaseModel):
    """Request model for SIWE login."""
    message: str
    signature: str
    address: str


class LoginResponse(BaseModel):
    """Response model for successful login."""
    access_token: str
    token_type: str = "bearer"
    address: str


class UserResponse(BaseModel):
    """Response model for user info."""
    address: str
    authenticated: bool = True


# In-memory nonce storage (in production, use Redis or database)
nonce_storage: dict[str, str] = {}


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[TokenData]:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        TokenData if authenticated, raises HTTPException otherwise
    """
    token = credentials.credentials
    token_data = verify_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data


@router.post("/nonce", response_model=NonceResponse)
async def generate_nonce_endpoint(request: NonceRequest):
    """
    Generate a nonce for SIWE authentication.
    
    Args:
        request: Contains the wallet address
        
    Returns:
        Generated nonce
    """
    # Validate address
    if not validate_ethereum_address(request.address):
        raise HTTPException(status_code=400, detail="Invalid Ethereum address")
    
    # Check rate limit
    if not rate_limiter.check_rate_limit(request.address.lower()):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    
    # Generate and store nonce
    nonce = generate_nonce()
    nonce_storage[request.address.lower()] = nonce
    
    return NonceResponse(nonce=nonce)


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, response: Response):
    """
    Authenticate user with SIWE.
    
    Args:
        request: Contains SIWE message, signature, and address
        response: FastAPI response object for setting cookies
        
    Returns:
        JWT access token
    """
    # Validate address
    if not validate_ethereum_address(request.address):
        raise HTTPException(status_code=400, detail="Invalid Ethereum address")
    
    # Check rate limit
    if not rate_limiter.check_rate_limit(request.address.lower()):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please try again later."
        )
    
    # Verify signature
    if not verify_siwe_signature(
        message=request.message,
        signature=request.signature,
        expected_address=request.address
    ):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Create access token
    access_token_expires = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    access_token = create_access_token(
        data={"address": request.address.lower()},
        expires_delta=access_token_expires
    )
    
    # Set HTTP-only cookie (optional, frontend can also handle token)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=settings.JWT_EXPIRATION_HOURS * 3600
    )
    
    # Clear nonce after successful login
    nonce_storage.pop(request.address.lower(), None)
    
    return LoginResponse(
        access_token=access_token,
        address=request.address.lower()
    )


@router.post("/logout")
async def logout(response: Response, _: TokenData = Depends(get_current_user)):
    """
    Logout user by clearing the access token cookie.
    
    Args:
        response: FastAPI response object
        _: Current user (ensures authenticated)
    """
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: TokenData = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User information
    """
    return UserResponse(
        address=current_user.address,
        authenticated=True
    )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    response: Response,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Refresh the access token.
    
    Args:
        response: FastAPI response object
        current_user: Current authenticated user
        
    Returns:
        New JWT access token
    """
    # Create new access token
    access_token_expires = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    access_token = create_access_token(
        data={"address": current_user.address},
        expires_delta=access_token_expires
    )
    
    # Update cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=settings.JWT_EXPIRATION_HOURS * 3600
    )
    
    return LoginResponse(
        access_token=access_token,
        address=current_user.address
    )