#!/usr/bin/env python3
"""Test 1inch functionality through the chat interface."""

import asyncio
import json
import websockets
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_chat_1inch():
    """Test 1inch functionality through chat WebSocket."""
    print("🚀 Testing 1inch through Chat Interface")
    print("=" * 50)
    
    # Connect to WebSocket
    ws_url = "ws://localhost:8000/api/chat/ws/test-client-1inch"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            # Receive welcome message
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"✅ Connected: {welcome_data['content'][:50]}...")
            
            # Test 1: Ask about token prices
            print("\n💬 Test 1: Asking about token prices...")
            message = {
                "content": "What are the current prices of USDC, DAI, and USDT on Ethereum?",
                "metadata": {}
            }
            await websocket.send(json.dumps(message))
            
            # Receive typing indicator
            typing = await websocket.recv()
            typing_data = json.loads(typing)
            if typing_data["type"] == "typing":
                print("   ⌨️  AI is typing...")
            
            # Receive response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"   🤖 Response: {response_data['content'][:200]}...")
            
            # Test 2: Ask about swap quotes
            print("\n💬 Test 2: Asking about swap quotes...")
            message = {
                "content": "How much DAI would I get for swapping 100 USDC on Ethereum?",
                "metadata": {}
            }
            await websocket.send(json.dumps(message))
            
            # Receive typing indicator
            typing = await websocket.recv()
            
            # Receive response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"   🤖 Response: {response_data['content'][:200]}...")
            
            # Test 3: Ask about supported chains
            print("\n💬 Test 3: Asking about supported chains...")
            message = {
                "content": "Which blockchain networks does this app support for swaps?",
                "metadata": {}
            }
            await websocket.send(json.dumps(message))
            
            # Receive typing indicator
            typing = await websocket.recv()
            
            # Receive response
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"   🤖 Response: {response_data['content'][:200]}...")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print("\n" + "=" * 50)
    print("✅ Chat 1inch test completed!")


if __name__ == "__main__":
    asyncio.run(test_chat_1inch())