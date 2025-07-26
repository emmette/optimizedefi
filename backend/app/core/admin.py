"""Admin access control for metrics and sensitive endpoints."""

from typing import List, Optional
from fastapi import HTTPException, Depends
from app.core.auth import get_current_user, TokenData
from app.core.config import settings


class AdminAccessControl:
    """Admin access control based on wallet addresses."""
    
    def __init__(self, admin_addresses: Optional[List[str]] = None):
        """
        Initialize admin access control.
        
        Args:
            admin_addresses: List of admin wallet addresses
        """
        if admin_addresses is None:
            admin_addresses = settings.ADMIN_WALLET_ADDRESSES
        
        # Normalize addresses to lowercase
        self.admin_addresses = [addr.lower() for addr in admin_addresses if addr]
    
    def is_admin(self, wallet_address: str) -> bool:
        """
        Check if a wallet address has admin privileges.
        
        Args:
            wallet_address: Ethereum wallet address to check
            
        Returns:
            True if address is admin, False otherwise
        """
        return wallet_address.lower() in self.admin_addresses
    
    def add_admin(self, wallet_address: str) -> None:
        """
        Add a wallet address to admin list.
        
        Args:
            wallet_address: Ethereum wallet address to add
        """
        normalized = wallet_address.lower()
        if normalized not in self.admin_addresses:
            self.admin_addresses.append(normalized)
    
    def remove_admin(self, wallet_address: str) -> None:
        """
        Remove a wallet address from admin list.
        
        Args:
            wallet_address: Ethereum wallet address to remove
        """
        normalized = wallet_address.lower()
        if normalized in self.admin_addresses:
            self.admin_addresses.remove(normalized)
    
    def list_admins(self) -> List[str]:
        """
        Get list of admin addresses.
        
        Returns:
            List of admin wallet addresses
        """
        return self.admin_addresses.copy()


# Global admin access control instance
admin_access_control = AdminAccessControl()


async def require_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """
    FastAPI dependency to require admin access.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        TokenData if user is admin
        
    Raises:
        HTTPException: If user is not admin
    """
    if not admin_access_control.is_admin(current_user.address):
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    return current_user


async def get_admin_status(current_user: TokenData = Depends(get_current_user)) -> dict:
    """
    Get admin status for current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dictionary with admin status
    """
    return {
        "address": current_user.address,
        "is_admin": admin_access_control.is_admin(current_user.address)
    }


async def check_admin_optional(
    current_user: Optional[TokenData] = Depends(get_current_user)
) -> Optional[bool]:
    """
    Optional admin check dependency.
    
    Args:
        current_user: Current authenticated user (optional)
        
    Returns:
        True if admin, False if not admin, None if not authenticated
    """
    if current_user is None:
        return None
    
    return admin_access_control.is_admin(current_user.address)