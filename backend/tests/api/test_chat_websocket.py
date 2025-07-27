"""Tests for WebSocket chat endpoint."""

import json
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app


class TestChatWebSocket:
    """Test WebSocket chat functionality."""

    def test_websocket_connection_unauthenticated(self, client: TestClient):
        """Test WebSocket connection without authentication."""
        client_id = "test-client-123"
        
        with client.websocket_connect(f"/api/chat/ws/{client_id}") as websocket:
            # Should receive welcome message
            data = websocket.receive_json()
            assert data["type"] == "system"
            assert "OptimizeDeFi AI assistant" in data["content"]
            
            # Send a test message
            websocket.send_json({
                "type": "user_message",
                "content": "Hello, test message"
            })
            
            # Should receive typing indicator
            data = websocket.receive_json()
            assert data["type"] == "typing"

    def test_websocket_connection_authenticated(self, client: TestClient, test_jwt_token: str):
        """Test WebSocket connection with authentication."""
        client_id = "0x742d35Cc6634C0532925a3b844Bc9e7595f5b8e7"
        
        with client.websocket_connect(
            f"/api/chat/ws/{client_id}?token={test_jwt_token}"
        ) as websocket:
            # Should receive welcome message
            data = websocket.receive_json()
            assert data["type"] == "system"
            assert "OptimizeDeFi AI assistant" in data["content"]

    @patch("app.workflows.chat_workflow.get_chat_workflow")
    def test_websocket_message_flow(self, mock_get_workflow, client: TestClient):
        """Test complete message flow through WebSocket."""
        # Mock the chat workflow
        mock_workflow = MagicMock()
        mock_workflow.config.enable_streaming = False
        mock_workflow.invoke.return_value = {
            "messages": [
                MagicMock(
                    content="Test AI response",
                    metadata={"agent": "general", "agent_type": "general"}
                )
            ],
            "routing_result": {"selected_agent": "general", "confidence": 0.9}
        }
        mock_get_workflow.return_value = mock_workflow
        
        client_id = "test-client-123"
        
        with client.websocket_connect(f"/api/chat/ws/{client_id}") as websocket:
            # Skip welcome message
            websocket.receive_json()
            
            # Send user message
            user_message = {
                "content": "What is DeFi?",
                "metadata": {"test": True}
            }
            websocket.send_text(json.dumps(user_message))
            
            # Should receive typing indicator
            data = websocket.receive_json()
            assert data["type"] == "typing"
            
            # Should receive AI response
            data = websocket.receive_json()
            assert data["type"] == "ai_response"
            assert data["content"] == "Test AI response"
            assert data["metadata"]["agent"] == "general"

    def test_websocket_invalid_message(self, client: TestClient):
        """Test WebSocket with invalid message format."""
        client_id = "test-client-123"
        
        with client.websocket_connect(f"/api/chat/ws/{client_id}") as websocket:
            # Skip welcome message
            websocket.receive_json()
            
            # Send invalid message (missing content)
            websocket.send_text(json.dumps({"type": "user_message"}))
            
            # Should receive error message
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "Invalid message format" in data["content"]

    def test_websocket_session_id_generation(self, client: TestClient, test_jwt_token: str):
        """Test session ID generation for authenticated and unauthenticated users."""
        # Test unauthenticated session ID
        unauth_client_id = "anonymous-123"
        with patch("app.api.chat.performance_logger.log_custom") as mock_log:
            with client.websocket_connect(f"/api/chat/ws/{unauth_client_id}"):
                # Check session_id was generated
                mock_log.assert_called()
                call_args = mock_log.call_args[1]
                assert call_args["session_id"] == f"session_anon_{unauth_client_id}"
        
        # Test authenticated session ID
        auth_client_id = "0x742d35Cc6634C0532925a3b844Bc9e7595f5b8e7"
        with patch("app.api.chat.performance_logger.log_custom") as mock_log:
            with client.websocket_connect(
                f"/api/chat/ws/{auth_client_id}?token={test_jwt_token}"
            ):
                # Check session_id was generated
                mock_log.assert_called()
                call_args = mock_log.call_args[1]
                assert call_args["session_id"].startswith(f"session_{auth_client_id}")

    @patch("app.workflows.chat_workflow.get_chat_workflow")
    def test_websocket_workflow_error(self, mock_get_workflow, client: TestClient):
        """Test WebSocket behavior when workflow fails."""
        # Mock workflow initialization failure
        mock_get_workflow.return_value = None
        
        client_id = "test-client-123"
        
        with client.websocket_connect(f"/api/chat/ws/{client_id}") as websocket:
            # Skip welcome message
            websocket.receive_json()
            
            # Send user message
            websocket.send_text(json.dumps({"content": "Test message"}))
            
            # Should receive typing indicator
            data = websocket.receive_json()
            assert data["type"] == "typing"
            
            # Should receive error message
            data = websocket.receive_json()
            assert data["type"] == "error"
            assert "temporarily unavailable" in data["content"]

    def test_websocket_multiple_connections(self, client: TestClient):
        """Test multiple WebSocket connections."""
        client_id_1 = "client-1"
        client_id_2 = "client-2"
        
        # Open two connections
        with client.websocket_connect(f"/api/chat/ws/{client_id_1}") as ws1:
            with client.websocket_connect(f"/api/chat/ws/{client_id_2}") as ws2:
                # Both should receive welcome messages
                data1 = ws1.receive_json()
                data2 = ws2.receive_json()
                
                assert data1["type"] == "system"
                assert data2["type"] == "system"

    @patch("app.workflows.chat_workflow.get_chat_workflow")
    def test_websocket_streaming_response(self, mock_get_workflow, client: TestClient):
        """Test WebSocket with streaming response."""
        # Mock streaming workflow
        mock_workflow = MagicMock()
        mock_workflow.config.enable_streaming = True
        
        # Create async generator for streaming
        async def mock_stream(*args, **kwargs):
            yield {
                "route_query": {
                    "current_agent": "portfolio",
                    "routing_result": {"confidence": 0.95}
                }
            }
            yield {
                "portfolio_agent": {
                    "messages": [
                        MagicMock(
                            content="Your portfolio contains...",
                            metadata={"agent": "portfolio", "agent_type": "portfolio"}
                        )
                    ]
                }
            }
        
        mock_workflow.stream = mock_stream
        mock_get_workflow.return_value = mock_workflow
        
        client_id = "test-client-123"
        
        with client.websocket_connect(f"/api/chat/ws/{client_id}") as websocket:
            # Skip welcome message
            websocket.receive_json()
            
            # Send user message with streaming enabled
            websocket.send_text(json.dumps({
                "content": "Show my portfolio",
                "stream": True
            }))
            
            # Should receive typing indicator
            data = websocket.receive_json()
            assert data["type"] == "typing"
            
            # Should receive routing info
            data = websocket.receive_json()
            assert data["type"] == "routing"
            assert data["metadata"]["selected_agent"] == "portfolio"
            
            # Should receive AI response
            data = websocket.receive_json()
            assert data["type"] == "ai_response"
            assert "Your portfolio contains" in data["content"]
            assert data["metadata"]["agent"] == "portfolio"

    def test_websocket_disconnect_cleanup(self, client: TestClient):
        """Test cleanup on WebSocket disconnect."""
        client_id = "test-cleanup-123"
        
        with patch("app.api.chat.active_connections", {}) as mock_connections:
            # Connect
            with client.websocket_connect(f"/api/chat/ws/{client_id}") as websocket:
                # Verify connection is tracked
                assert client_id in mock_connections
                websocket.receive_json()  # Welcome message
            
            # After disconnect, connection should be cleaned up
            assert client_id not in mock_connections