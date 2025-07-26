"""Authentication and authorization utilities."""

import os
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from eth_account.messages import encode_defunct
from eth_account import Account
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from web3 import Web3

from app.core.config import settings


# Password context for future use (if needed for admin accounts)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days


class SIWEMessage(BaseModel):
    """Sign-In with Ethereum message structure."""
    domain: str
    address: str
    statement: str
    uri: str
    version: str
    chain_id: int
    nonce: str
    issued_at: str
    expiration_time: Optional[str] = None
    not_before: Optional[str] = None
    request_id: Optional[str] = None
    resources: Optional[list[str]] = None


class TokenData(BaseModel):
    """JWT token payload structure."""
    address: str
    exp: Optional[datetime] = None
    iat: Optional[datetime] = None


def parse_siwe_message(message: str) -> SIWEMessage:
    """Parse a SIWE message string into components."""
    lines = message.strip().split('\n')
    
    # Extract components from the message
    components = {}
    
    # First line contains domain and wants
    if lines[0]:
        parts = lines[0].split(' wants you to sign in with your Ethereum account:')
        if len(parts) == 2:
            components['domain'] = parts[0].strip()
    
    # Second line is the address
    if len(lines) > 1:
        components['address'] = lines[1].strip()
    
    # Find statement (everything between address and URI)
    statement_lines = []
    uri_index = -1
    for i, line in enumerate(lines[2:], 2):
        if line.startswith('URI:'):
            uri_index = i
            break
        elif line.strip():
            statement_lines.append(line.strip())
    
    components['statement'] = ' '.join(statement_lines)
    
    # Parse the rest of the fields
    for i in range(uri_index, len(lines)):
        line = lines[i].strip()
        if line.startswith('URI:'):
            components['uri'] = line.split('URI:', 1)[1].strip()
        elif line.startswith('Version:'):
            components['version'] = line.split('Version:', 1)[1].strip()
        elif line.startswith('Chain ID:'):
            components['chain_id'] = int(line.split('Chain ID:', 1)[1].strip())
        elif line.startswith('Nonce:'):
            components['nonce'] = line.split('Nonce:', 1)[1].strip()
        elif line.startswith('Issued At:'):
            components['issued_at'] = line.split('Issued At:', 1)[1].strip()
        elif line.startswith('Expiration Time:'):
            components['expiration_time'] = line.split('Expiration Time:', 1)[1].strip()
        elif line.startswith('Not Before:'):
            components['not_before'] = line.split('Not Before:', 1)[1].strip()
        elif line.startswith('Request ID:'):
            components['request_id'] = line.split('Request ID:', 1)[1].strip()
        elif line.startswith('Resources:'):
            # Resources can be multi-line
            components['resources'] = []
            for j in range(i + 1, len(lines)):
                if lines[j].startswith('- '):
                    components['resources'].append(lines[j][2:].strip())
                else:
                    break
    
    return SIWEMessage(**components)


def verify_siwe_signature(message: str, signature: str, expected_address: str) -> bool:
    """
    Verify a SIWE message signature.
    
    Args:
        message: The SIWE message that was signed
        signature: The signature to verify
        expected_address: The expected signer address
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        # Parse the message
        siwe_msg = parse_siwe_message(message)
        
        # Check if address matches
        if siwe_msg.address.lower() != expected_address.lower():
            return False
        
        # Check expiration if present
        if siwe_msg.expiration_time:
            exp_time = datetime.fromisoformat(siwe_msg.expiration_time.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) > exp_time:
                return False
        
        # Check not before if present
        if siwe_msg.not_before:
            not_before = datetime.fromisoformat(siwe_msg.not_before.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) < not_before:
                return False
        
        # Recover address from signature
        message_hash = encode_defunct(text=message)
        recovered_address = Account.recover_message(message_hash, signature=signature)
        
        # Verify the recovered address matches
        return recovered_address.lower() == expected_address.lower()
        
    except Exception as e:
        print(f"SIWE verification error: {e}")
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    # Set expiration
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    })
    
    # Create token
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        address = payload.get("address")
        
        if address is None:
            return None
            
        return TokenData(
            address=address,
            exp=payload.get("exp"),
            iat=payload.get("iat")
        )
    except JWTError:
        return None


def generate_nonce() -> str:
    """Generate a random nonce for SIWE."""
    return Web3.keccak(text=f"{time.time()}{os.urandom(32).hex()}").hex()


def validate_ethereum_address(address: str) -> bool:
    """Validate an Ethereum address."""
    try:
        # Check if it's a valid address format
        if not Web3.is_address(address):
            return False
        
        # Convert to checksum address to ensure proper casing
        Web3.to_checksum_address(address)
        return True
    except Exception:
        return False


class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list[float]] = {}
    
    def check_rate_limit(self, identifier: str) -> bool:
        """
        Check if identifier has exceeded rate limit.
        
        Args:
            identifier: Unique identifier (e.g., wallet address)
            
        Returns:
            True if within limits, False if exceeded
        """
        now = time.time()
        
        # Clean old requests
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if now - req_time < self.window_seconds
            ]
        else:
            self.requests[identifier] = []
        
        # Check limit
        if len(self.requests[identifier]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[identifier].append(now)
        return True
    
    def get_remaining_requests(self, identifier: str) -> int:
        """Get remaining requests for identifier."""
        now = time.time()
        
        if identifier not in self.requests:
            return self.max_requests
        
        # Count recent requests
        recent_requests = [
            req_time for req_time in self.requests[identifier]
            if now - req_time < self.window_seconds
        ]
        
        return max(0, self.max_requests - len(recent_requests))


# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=100, window_seconds=3600)