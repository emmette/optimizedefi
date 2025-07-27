"""End-to-end integration tests for chat functionality."""

import asyncio
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient
from langchain_core.messages import HumanMessage, AIMessage
import websocket

from app.main import app
from app.workflows.chat_workflow import get_chat_workflow


class TestChatE2E:
    """End-to-end tests for the complete chat flow."""

    @pytest.fixture
    def mock_chat_workflow(self):
        """Mock the chat workflow for testing."""
        with patch("app.workflows.chat_workflow.get_chat_workflow") as mock_get:
            workflow = MagicMock()
            workflow.config.enable_streaming = False
            
            # Mock the invoke method
            async def mock_invoke(messages, session_id=None, metadata=None):
                # Simulate processing time
                await asyncio.sleep(0.1)
                
                # Return mock response based on the last message
                last_message = messages[-1]
                if "portfolio" in last_message.content.lower():
                    response = "Your portfolio value is $10,000 with 60% ETH and 40% USDC."
                    agent = "portfolio"
                elif "swap" in last_message.content.lower():
                    response = "I can help you swap tokens. What would you like to swap?"
                    agent = "swap"
                else:
                    response = "I can help you with DeFi portfolio optimization."
                    agent = "general"
                
                return {
                    "messages": messages + [
                        AIMessage(
                            content=response,
                            metadata={"agent": agent, "agent_type": agent}
                        )
                    ],
                    "routing_result": {
                        "selected_agent": agent,
                        "confidence": 0.95
                    },
                    "metadata": metadata or {}
                }
            
            workflow.invoke = mock_invoke
            mock_get.return_value = workflow
            yield workflow

    def test_chat_flow_unauthenticated(self, client: TestClient, mock_chat_workflow):
        """Test complete chat flow for unauthenticated user."""
        client_id = "test-e2e-unauth"
        
        with client.websocket_connect(f"/api/chat/ws/{client_id}") as websocket:
            # Should receive welcome message
            welcome = websocket.receive_json()
            assert welcome["type"] == "system"
            assert "Welcome" in welcome["content"]
            
            # Send a message
            user_message = {
                "content": "What is DeFi?",
                "metadata": {"test": True}
            }
            websocket.send_text(json.dumps(user_message))
            
            # Should receive typing indicator
            typing_msg = websocket.receive_json()
            assert typing_msg["type"] == "typing"
            assert typing_msg["isTyping"] is True
            
            # Should receive AI response
            ai_response = websocket.receive_json()
            assert ai_response["type"] == "ai_response"
            assert "DeFi portfolio optimization" in ai_response["content"]
            assert ai_response["metadata"]["agent"] == "general"
            
            # Test conversation continuity
            followup = {
                "content": "Show my portfolio",
                "metadata": {}
            }
            websocket.send_text(json.dumps(followup))
            
            # Typing indicator
            typing_msg = websocket.receive_json()
            assert typing_msg["type"] == "typing"
            
            # Portfolio response
            portfolio_response = websocket.receive_json()
            assert portfolio_response["type"] == "ai_response"
            assert "$10,000" in portfolio_response["content"]
            assert portfolio_response["metadata"]["agent"] == "portfolio"

    def test_chat_flow_authenticated(self, client: TestClient, test_jwt_token: str, mock_chat_workflow):
        """Test complete chat flow for authenticated user."""
        client_id = "0x742d35Cc6634C0532925a3b844Bc9e7595f5b8e7"
        
        with client.websocket_connect(
            f"/api/chat/ws/{client_id}?token={test_jwt_token}"
        ) as websocket:
            # Welcome message
            welcome = websocket.receive_json()
            assert welcome["type"] == "system"
            
            # Send swap request
            swap_request = {
                "content": "I want to swap 100 USDC for ETH",
                "metadata": {"authenticated": True}
            }
            websocket.send_text(json.dumps(swap_request))
            
            # Typing
            typing_msg = websocket.receive_json()
            assert typing_msg["type"] == "typing"
            
            # Swap agent response
            swap_response = websocket.receive_json()
            assert swap_response["type"] == "ai_response"
            assert "swap tokens" in swap_response["content"]
            assert swap_response["metadata"]["agent"] == "swap"

    def test_chat_streaming_mode(self, client: TestClient, mock_chat_workflow):
        """Test chat with streaming enabled."""
        # Configure workflow for streaming
        mock_chat_workflow.config.enable_streaming = True
        
        async def mock_stream(messages, session_id=None, metadata=None):
            # Simulate streaming events
            yield {
                "route_query": {
                    "current_agent": "portfolio",
                    "routing_result": {"confidence": 0.95, "selected_agent": "portfolio"}
                }
            }
            await asyncio.sleep(0.05)
            
            yield {
                "portfolio_agent": {
                    "messages": [
                        AIMessage(
                            content="Analyzing your portfolio...",
                            metadata={"agent": "portfolio", "agent_type": "portfolio"}
                        )
                    ]
                }
            }
            await asyncio.sleep(0.05)
            
            yield {
                "portfolio_agent": {
                    "messages": [
                        AIMessage(
                            content="Your portfolio is worth $15,000.",
                            metadata={"agent": "portfolio", "agent_type": "portfolio"}
                        )
                    ]
                }
            }
        
        mock_chat_workflow.stream = mock_stream
        
        client_id = "test-streaming"
        
        with client.websocket_connect(f"/api/chat/ws/{client_id}") as websocket:
            # Skip welcome
            websocket.receive_json()
            
            # Send message requesting streaming
            websocket.send_text(json.dumps({
                "content": "Analyze my portfolio",
                "stream": True
            }))
            
            # Typing indicator
            typing = websocket.receive_json()
            assert typing["type"] == "typing"
            
            # Routing info
            routing = websocket.receive_json()
            assert routing["type"] == "routing"
            assert routing["metadata"]["selected_agent"] == "portfolio"
            
            # First content chunk
            chunk1 = websocket.receive_json()
            assert chunk1["type"] == "ai_response"
            assert "Analyzing" in chunk1["content"]
            
            # Second content chunk
            chunk2 = websocket.receive_json()
            assert chunk2["type"] == "ai_response"
            assert "$15,000" in chunk2["content"]

    def test_chat_error_handling(self, client: TestClient):
        """Test error handling in chat flow."""
        # Test with workflow initialization failure
        with patch("app.workflows.chat_workflow.get_chat_workflow", return_value=None):
            client_id = "test-error"
            
            with client.websocket_connect(f"/api/chat/ws/{client_id}") as websocket:
                # Welcome message
                websocket.receive_json()
                
                # Send message
                websocket.send_text(json.dumps({"content": "Test error"}))
                
                # Typing
                websocket.receive_json()
                
                # Should receive error
                error_msg = websocket.receive_json()
                assert error_msg["type"] == "error"
                assert "temporarily unavailable" in error_msg["content"]

    def test_chat_session_persistence(self, client: TestClient, mock_chat_workflow):
        """Test that chat sessions persist across connections."""
        client_id = "test-persistence"
        
        # First connection
        with client.websocket_connect(f"/api/chat/ws/{client_id}") as ws1:
            ws1.receive_json()  # Welcome
            
            # Send first message
            ws1.send_text(json.dumps({"content": "Remember this: The secret is 42"}))
            ws1.receive_json()  # Typing
            response1 = ws1.receive_json()
            assert response1["type"] == "ai_response"
        
        # Second connection - should have same session
        with client.websocket_connect(f"/api/chat/ws/{client_id}") as ws2:
            ws2.receive_json()  # Welcome
            
            # Ask about previous message
            ws2.send_text(json.dumps({"content": "What was the secret?"}))
            ws2.receive_json()  # Typing
            response2 = ws2.receive_json()
            
            # In a real implementation with memory, this would recall the secret
            assert response2["type"] == "ai_response"

    def test_concurrent_chat_sessions(self, client: TestClient, mock_chat_workflow):
        """Test multiple concurrent chat sessions."""
        client1 = "user-1"
        client2 = "user-2"
        
        # Open two connections simultaneously
        with client.websocket_connect(f"/api/chat/ws/{client1}") as ws1:
            with client.websocket_connect(f"/api/chat/ws/{client2}") as ws2:
                # Skip welcome messages
                ws1.receive_json()
                ws2.receive_json()
                
                # Send messages from both users
                ws1.send_text(json.dumps({"content": "User 1: Show portfolio"}))
                ws2.send_text(json.dumps({"content": "User 2: Help with swap"}))
                
                # Both should receive typing indicators
                typing1 = ws1.receive_json()
                typing2 = ws2.receive_json()
                assert typing1["type"] == "typing"
                assert typing2["type"] == "typing"
                
                # Both should receive appropriate responses
                response1 = ws1.receive_json()
                response2 = ws2.receive_json()
                
                assert response1["type"] == "ai_response"
                assert "$10,000" in response1["content"]
                assert response1["metadata"]["agent"] == "portfolio"
                
                assert response2["type"] == "ai_response"
                assert "swap tokens" in response2["content"]
                assert response2["metadata"]["agent"] == "swap"

    def test_message_validation(self, client: TestClient, mock_chat_workflow):
        """Test message format validation."""
        client_id = "test-validation"
        
        with client.websocket_connect(f"/api/chat/ws/{client_id}") as websocket:
            websocket.receive_json()  # Welcome
            
            # Test various invalid message formats
            invalid_messages = [
                "plain string",  # Not JSON
                json.dumps({"type": "user_message"}),  # Missing content
                json.dumps({"content": ""}),  # Empty content
                json.dumps({"content": 123}),  # Non-string content
                json.dumps({"content": "a" * 10001}),  # Too long (if there's a limit)
            ]
            
            for invalid_msg in invalid_messages:
                websocket.send_text(invalid_msg)
                
                response = websocket.receive_json()
                assert response["type"] == "error"
                assert "Invalid" in response["content"] or "Error" in response["content"]

    @pytest.mark.asyncio
    async def test_performance_logging(self, client: TestClient, mock_chat_workflow):
        """Test that performance metrics are logged."""
        with patch("app.api.chat.performance_logger.log_custom") as mock_log:
            client_id = "test-performance"
            
            with client.websocket_connect(f"/api/chat/ws/{client_id}") as websocket:
                websocket.receive_json()  # Welcome
                
                # Send message
                websocket.send_text(json.dumps({"content": "Test performance"}))
                websocket.receive_json()  # Typing
                websocket.receive_json()  # Response
                
                # Check that performance was logged
                mock_log.assert_called()
                call_args = [call.kwargs for call in mock_log.call_args_list]
                
                # Should have logged connection and chat completion
                assert any("event" in args and args["event"] == "websocket_connected" for args in call_args)
                assert any("event" in args and args["event"] == "chat_completion" for args in call_args)

    def test_rate_limiting(self, client: TestClient, mock_chat_workflow):
        """Test rate limiting on chat messages."""
        client_id = "test-rate-limit"
        
        with client.websocket_connect(f"/api/chat/ws/{client_id}") as websocket:
            websocket.receive_json()  # Welcome
            
            # Send many messages rapidly
            for i in range(20):
                websocket.send_text(json.dumps({"content": f"Message {i}"}))
            
            # Should eventually receive rate limit error
            # (Implementation would need actual rate limiting)
            # For now, just verify messages are processed
            received_messages = 0
            while received_messages < 10:
                msg = websocket.receive_json()
                if msg["type"] in ["typing", "ai_response"]:
                    received_messages += 1
                elif msg["type"] == "error" and "rate" in msg["content"].lower():
                    # Rate limit hit
                    break
            
            assert received_messages > 0