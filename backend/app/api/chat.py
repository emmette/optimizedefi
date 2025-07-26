"""WebSocket chat handler with LangGraph integration."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from typing import Dict, List, Optional, Any
import json
import asyncio
import uuid
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.core.auth import get_current_user_ws, TokenData
from app.workflows import get_chat_workflow, ChatState
from app.services.performance_logger import performance_logger
from app.services.metrics import metrics_collector
from app.services.memory_manager import memory_manager

router = APIRouter()

# Store active connections
active_connections: Dict[str, WebSocket] = {}

# Store user sessions
user_sessions: Dict[str, str] = {}  # user_id -> session_id


class ChatMessage:
    """Chat message structure."""
    
    def __init__(
        self,
        type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.type = type
        self.content = content
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow().isoformat()
        self.id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    user: Optional[TokenData] = Depends(get_current_user_ws)
):
    """WebSocket endpoint for AI chat with authentication."""
    await websocket.accept()
    active_connections[client_id] = websocket
    
    # Get or create session ID for user
    session_id = None
    if user:
        session_id = user_sessions.get(user.address)
        if not session_id:
            session_id = f"session_{user.address}_{uuid.uuid4().hex[:8]}"
            user_sessions[user.address] = session_id
    
    # Log connection
    performance_logger.log_custom(
        "websocket_connected",
        client_id=client_id,
        user_address=user.address if user else None,
        session_id=session_id
    )
    
    try:
        # Send welcome message
        welcome_msg = ChatMessage(
            type="system",
            content="Connected to OptimizeDeFi AI assistant. How can I help you today?",
            metadata={"agent": "system"}
        )
        await websocket.send_json(welcome_msg.to_dict())
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message_data = json.loads(data)
                
                # Validate message
                if "content" not in message_data:
                    error_msg = ChatMessage(
                        type="error",
                        content="Invalid message format: missing content"
                    )
                    await websocket.send_json(error_msg.to_dict())
                    continue
                
                # Create user message
                user_content = message_data["content"]
                user_msg = HumanMessage(
                    content=user_content,
                    metadata={
                        "client_id": client_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                )
                
                # Track request
                async with performance_logger.log_operation(
                    operation_type="chat_request",
                    client_id=client_id,
                    session_id=session_id,
                    message_length=len(user_content)
                ) as metrics:
                    # Send typing indicator
                    typing_msg = ChatMessage(
                        type="typing",
                        content="",
                        metadata={"agent": "thinking"}
                    )
                    await websocket.send_json(typing_msg.to_dict())
                    
                    # Process with workflow
                    try:
                        # Add metadata
                        metadata = {
                            "client_id": client_id,
                            "user_address": user.address if user else None,
                            "request_metadata": message_data.get("metadata", {})
                        }
                        
                        # Get workflow instance
                        chat_workflow = get_chat_workflow()
                        if chat_workflow is None:
                            # Workflow initialization failed - send error
                            error_msg = ChatMessage(
                                type="error",
                                content="Chat service is temporarily unavailable. Please ensure API keys are configured.",
                                metadata={"error_type": "service_unavailable"}
                            )
                            await websocket.send_json(error_msg.to_dict())
                            continue
                        
                        # Check if streaming is requested
                        stream_response = message_data.get("stream", True)
                        
                        if stream_response and chat_workflow.config.enable_streaming:
                            # Stream response
                            agent_name = None
                            response_content = ""
                            
                            async for event in chat_workflow.stream(
                                messages=[user_msg],  # Just current message
                                session_id=session_id,
                                metadata=metadata
                            ):
                                # Process streaming events
                                for node_name, node_output in event.items():
                                    if node_name == "route_query":
                                        # Send routing info
                                        routing_msg = ChatMessage(
                                            type="routing",
                                            content="",
                                            metadata={
                                                "selected_agent": node_output.get("current_agent"),
                                                "confidence": node_output.get("routing_result", {}).get("confidence")
                                            }
                                        )
                                        await websocket.send_json(routing_msg.to_dict())
                                    
                                    elif node_name.endswith("_agent"):
                                        # Extract agent response
                                        if "messages" in node_output and node_output["messages"]:
                                            last_msg = node_output["messages"][-1]
                                            if isinstance(last_msg, AIMessage):
                                                agent_name = last_msg.metadata.get("agent", "AI")
                                                response_content = last_msg.content
                                                
                                                # Send response
                                                response_msg = ChatMessage(
                                                    type="ai_response",
                                                    content=response_content,
                                                    metadata={
                                                        "agent": agent_name,
                                                        "agent_type": last_msg.metadata.get("agent_type")
                                                    }
                                                )
                                                await websocket.send_json(response_msg.to_dict())
                        else:
                            # Non-streaming response
                            final_state = await chat_workflow.invoke(
                                messages=[user_msg],  # Just current message
                                session_id=session_id,
                                metadata=metadata
                            )
                            
                            # Extract response
                            if final_state["messages"]:
                                last_msg = final_state["messages"][-1]
                                if isinstance(last_msg, AIMessage):
                                    response_msg = ChatMessage(
                                        type="ai_response",
                                        content=last_msg.content,
                                        metadata={
                                            "agent": last_msg.metadata.get("agent", "AI"),
                                            "agent_type": last_msg.metadata.get("agent_type"),
                                            "routing": final_state.get("routing_result")
                                        }
                                    )
                                    await websocket.send_json(response_msg.to_dict())
                        
                        # Record metrics
                        metrics.metadata["response_generated"] = True
                        metrics.metadata["streaming"] = stream_response
                        
                    except Exception as e:
                        # Send error message
                        error_msg = ChatMessage(
                            type="error",
                            content=f"I encountered an error processing your request: {str(e)}",
                            metadata={"error_type": type(e).__name__}
                        )
                        await websocket.send_json(error_msg.to_dict())
                        
                        # Log error
                        performance_logger.logger.error(
                            "chat_processing_error",
                            client_id=client_id,
                            error=str(e),
                            error_type=type(e).__name__
                        )
                        
                        metrics.metadata["error"] = str(e)
                
            except json.JSONDecodeError:
                error_msg = ChatMessage(
                    type="error",
                    content="Invalid JSON message"
                )
                await websocket.send_json(error_msg.to_dict())
            
            except Exception as e:
                performance_logger.logger.error(
                    "websocket_message_error",
                    client_id=client_id,
                    error=str(e)
                )
    
    except WebSocketDisconnect:
        # Clean up connection
        del active_connections[client_id]
        performance_logger.log_custom(
            "websocket_disconnected",
            client_id=client_id,
            session_id=session_id
        )
    
    except Exception as e:
        performance_logger.logger.error(
            "websocket_error",
            client_id=client_id,
            error=str(e),
            error_type=type(e).__name__
        )
        if client_id in active_connections:
            del active_connections[client_id]


@router.post("/message")
async def send_chat_message(
    message: Dict[str, Any],
    current_user: TokenData = Depends(get_current_user)
):
    """REST endpoint for sending chat messages."""
    try:
        # Validate message
        if "content" not in message:
            raise HTTPException(status_code=400, detail="Missing message content")
        
        # Get or create session
        session_id = user_sessions.get(current_user.address)
        if not session_id:
            session_id = f"session_{current_user.address}_{uuid.uuid4().hex[:8]}"
            user_sessions[current_user.address] = session_id
        
        # Create messages
        messages = [HumanMessage(content=message["content"])]
        
        # Process with workflow
        metadata = {
            "user_address": current_user.address,
            "rest_api": True
        }
        
        # Get workflow instance
        chat_workflow = get_chat_workflow()
        if chat_workflow is None:
            raise HTTPException(
                status_code=503,
                detail="Chat service is temporarily unavailable. Please ensure API keys are configured."
            )
        
        # Invoke workflow (non-streaming for REST)
        final_state = await chat_workflow.invoke(
            messages=messages,
            session_id=session_id,
            metadata=metadata
        )
        
        # Extract response
        response_content = "I couldn't generate a response."
        agent_info = {}
        
        if final_state["messages"]:
            last_msg = final_state["messages"][-1]
            if isinstance(last_msg, AIMessage):
                response_content = last_msg.content
                agent_info = {
                    "agent": last_msg.metadata.get("agent"),
                    "agent_type": last_msg.metadata.get("agent_type")
                }
        
        return {
            "status": "success",
            "request": {
                "content": message["content"],
                "timestamp": datetime.utcnow().isoformat()
            },
            "response": {
                "content": response_content,
                "metadata": agent_info,
                "routing": final_state.get("routing_result")
            },
            "session_id": session_id
        }
        
    except Exception as e:
        performance_logger.logger.error(
            "rest_chat_error",
            user=current_user.address,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/sessions/{session_id}/history")
async def get_chat_history(
    session_id: str,
    current_user: TokenData = Depends(get_current_user),
    limit: int = 50
):
    """Get chat history for a session."""
    # Verify session belongs to user
    user_session = user_sessions.get(current_user.address)
    if user_session != session_id:
        raise HTTPException(status_code=403, detail="Access denied to session")
    
    # Get messages from memory manager
    messages = await memory_manager.get_messages_for_context(session_id)
    
    # Convert to serializable format
    history = []
    for msg in messages[-limit:]:  # Limit results
        if isinstance(msg, HumanMessage):
            history.append({
                "type": "human",
                "content": msg.content,
                "metadata": msg.metadata if hasattr(msg, "metadata") else {}
            })
        elif isinstance(msg, AIMessage):
            history.append({
                "type": "ai",
                "content": msg.content,
                "metadata": msg.metadata if hasattr(msg, "metadata") else {}
            })
        elif isinstance(msg, SystemMessage):
            history.append({
                "type": "system",
                "content": msg.content,
                "metadata": msg.metadata if hasattr(msg, "metadata") else {}
            })
    
    # Get session metrics
    metrics = await memory_manager.get_session_metrics(session_id)
    
    return {
        "session_id": session_id,
        "messages": history,
        "metrics": metrics
    }


@router.delete("/sessions/{session_id}")
async def clear_session(
    session_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Clear a chat session."""
    # Verify session belongs to user
    user_session = user_sessions.get(current_user.address)
    if user_session != session_id:
        raise HTTPException(status_code=403, detail="Access denied to session")
    
    # Clear session
    if current_user.address in user_sessions:
        del user_sessions[current_user.address]
    
    # Clear from memory manager
    await memory_manager.clear_session(session_id)
    
    return {
        "status": "success",
        "message": "Session cleared"
    }