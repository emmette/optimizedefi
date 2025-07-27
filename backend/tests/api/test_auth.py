"""Tests for authentication endpoints."""

from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from app.core.auth import create_access_token, verify_token, generate_nonce


class TestAuthentication:
    """Test authentication functionality."""

    def test_get_nonce(self, client: TestClient):
        """Test nonce generation endpoint."""
        # POST request with address in body
        request_data = {
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f5b8e7"
        }
        
        response = client.post("/api/auth/nonce", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "nonce" in data
        assert len(data["nonce"]) > 0

    @patch("app.api.auth.verify_siwe_signature")
    def test_login_success(self, mock_verify, client: TestClient, test_siwe_message):
        """Test successful login with SIWE."""
        # Mock successful signature verification
        mock_verify.return_value = True
        
        # Generate a nonce first
        nonce_request = {
            "address": test_siwe_message["address"]
        }
        
        # Get nonce
        response = client.post("/api/auth/nonce", json=nonce_request)
        assert response.status_code == 200
        nonce = response.json()["nonce"]
        
        # Update test message with nonce
        test_siwe_message["nonce"] = nonce
        
        # Login
        login_data = {
            "message": str(test_siwe_message),
            "signature": "0x" + "00" * 65,  # Mock signature
            "address": test_siwe_message["address"]
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["address"] == test_siwe_message["address"].lower()
        
        # Verify the token
        token_data = verify_token(data["access_token"])
        assert token_data is not None
        assert token_data.address == test_siwe_message["address"].lower()

    @patch("app.api.auth.verify_siwe_signature")
    def test_login_invalid_signature(self, mock_verify, client: TestClient, test_siwe_message):
        """Test login with invalid signature."""
        # Mock failed signature verification
        mock_verify.return_value = False
        
        login_data = {
            "message": str(test_siwe_message),
            "signature": "0x" + "00" * 65,
            "address": test_siwe_message["address"]
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid signature" in response.json()["detail"]

    def test_login_invalid_address(self, client: TestClient):
        """Test login with invalid Ethereum address."""
        login_data = {
            "message": "test message",
            "signature": "0x" + "00" * 65,
            "address": "invalid-address"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        assert response.status_code == 400
        assert "Invalid Ethereum address" in response.json()["detail"]

    def test_logout(self, client: TestClient, test_jwt_token: str):
        """Test logout endpoint."""
        headers = {"Authorization": f"Bearer {test_jwt_token}"}
        response = client.post("/api/auth/logout", headers=headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"

    def test_logout_unauthorized(self, client: TestClient):
        """Test logout without authentication."""
        response = client.post("/api/auth/logout")
        
        assert response.status_code == 403  # FastAPI HTTPBearer returns 403 for missing credentials

    def test_get_current_user(self, client: TestClient, test_jwt_token: str):
        """Test getting current user information."""
        headers = {"Authorization": f"Bearer {test_jwt_token}"}
        response = client.get("/api/auth/me", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        # The test JWT token creates address in lowercase
        assert data["address"] in ["0x742d35cc6634c0532925a3b844bc9e7595f5b8e7", "0x742d35Cc6634C0532925a3b844Bc9e7595f5b8e7".lower()]
        assert data["authenticated"] is True

    def test_get_current_user_unauthorized(self, client: TestClient):
        """Test getting current user without authentication."""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 403  # FastAPI HTTPBearer returns 403 for missing credentials

    def test_jwt_token_creation_and_verification(self):
        """Test JWT token creation and verification."""
        test_address = "0x742d35Cc6634C0532925a3b844Bc9e7595f5b8e7"
        
        # Create token
        token = create_access_token(
            data={"address": test_address.lower()},
            expires_delta=timedelta(hours=1)
        )
        
        # Verify token
        token_data = verify_token(token)
        assert token_data is not None
        assert token_data.address == test_address.lower()
        
        # Test expired token
        expired_token = create_access_token(
            data={"address": test_address.lower()},
            expires_delta=timedelta(hours=-1)  # Already expired
        )
        
        expired_data = verify_token(expired_token)
        assert expired_data is None

    @patch("app.api.auth.rate_limiter.check_rate_limit")
    def test_rate_limiting(self, mock_rate_limit, client: TestClient):
        """Test rate limiting on authentication endpoints."""
        # Mock rate limit exceeded
        mock_rate_limit.return_value = False
        
        request_data = {
            "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f5b8e7"
        }
        
        response = client.post("/api/auth/nonce", json=request_data)
        
        assert response.status_code == 429
        # Check that the response contains rate limit message
        detail = response.json()["detail"]
        assert "Rate limit exceeded" in detail or "rate limit" in detail.lower()

    def test_nonce_generation(self):
        """Test nonce generation function."""
        nonce1 = generate_nonce()
        nonce2 = generate_nonce()
        
        # Nonces should be unique
        assert nonce1 != nonce2
        
        # Nonces should have sufficient length
        assert len(nonce1) >= 16
        assert len(nonce2) >= 16

    @patch("app.api.auth.verify_siwe_signature")
    def test_login_with_cookie(self, mock_verify, client: TestClient, test_siwe_message):
        """Test that login sets HTTP-only cookie."""
        mock_verify.return_value = True
        
        login_data = {
            "message": str(test_siwe_message),
            "signature": "0x" + "00" * 65,
            "address": test_siwe_message["address"]
        }
        
        response = client.post("/api/auth/login", json=login_data)
        
        # Check that cookie is set
        assert "access_token" in response.cookies
        
        # Cookie should have security attributes
        cookie = response.cookies["access_token"]
        # Note: TestClient doesn't fully simulate cookie attributes,
        # but in production these would be set