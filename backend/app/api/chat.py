from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import asyncio

router = APIRouter()

# Store active connections
active_connections: Dict[str, WebSocket] = {}

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for AI chat"""
    await websocket.accept()
    active_connections[client_id] = websocket
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # TODO: Process message with LangGraph agent
            # For now, echo back a simple response
            response = {
                "type": "ai_response",
                "content": f"I received your message: {message.get('content', '')}",
                "timestamp": str(asyncio.get_event_loop().time())
            }
            
            await websocket.send_json(response)
            
    except WebSocketDisconnect:
        del active_connections[client_id]
    except Exception as e:
        print(f"WebSocket error: {e}")
        if client_id in active_connections:
            del active_connections[client_id]

@router.post("/message")
async def send_chat_message(message: dict):
    """REST endpoint for sending chat messages"""
    # TODO: Implement REST-based chat for non-WebSocket clients
    return {
        "status": "received",
        "message": message,
        "response": "This is a placeholder response"
    }