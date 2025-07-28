// Test script to verify WebSocket chat functionality
const WebSocket = require('ws');

async function testWebSocketChat() {
  console.log('🧪 Testing WebSocket Chat Service...');
  console.log('================================\n');
  
  const clientId = `test-client-${Date.now()}`;
  const wsUrl = `ws://localhost:8000/api/chat/ws/${clientId}`;
  
  console.log(`📡 Connecting to WebSocket: ${wsUrl}`);
  
  const ws = new WebSocket(wsUrl, {
    headers: {
      'User-Agent': 'test-client'
    }
  });
  
  let messageReceived = false;
  
  ws.on('open', () => {
    console.log('✅ WebSocket connected successfully!\n');
    
    // Send a test message
    const testMessage = {
      type: 'message',
      content: 'What is the current price of ETH?',
      metadata: {
        timestamp: new Date().toISOString()
      }
    };
    
    console.log('📤 Sending test message:', testMessage.content);
    ws.send(JSON.stringify(testMessage));
  });
  
  ws.on('message', (data) => {
    try {
      const message = JSON.parse(data.toString());
      console.log('\n📥 Received message:');
      console.log('- Type:', message.type);
      console.log('- Content:', message.content?.substring(0, 100) + '...');
      console.log('- Agent:', message.metadata?.agent || 'N/A');
      console.log('- Agent Type:', message.metadata?.agent_type || 'N/A');
      
      messageReceived = true;
      
      // Send another message to test continuous operation
      if (message.type === 'message' && !message.content.includes('Test follow-up')) {
        setTimeout(() => {
          const followUp = {
            type: 'message',
            content: 'Test follow-up: Can you explain gas fees?',
            metadata: {
              timestamp: new Date().toISOString()
            }
          };
          console.log('\n📤 Sending follow-up message:', followUp.content);
          ws.send(JSON.stringify(followUp));
        }, 1000);
      } else {
        // Close after receiving response to follow-up
        setTimeout(() => {
          ws.close();
        }, 2000);
      }
    } catch (error) {
      console.error('❌ Error parsing message:', error);
    }
  });
  
  ws.on('error', (error) => {
    console.error('\n❌ WebSocket error:', error.message);
  });
  
  ws.on('close', (code, reason) => {
    console.log('\n🔌 WebSocket closed');
    console.log('- Code:', code);
    console.log('- Reason:', reason.toString() || 'No reason provided');
    console.log('\n================================');
    
    if (messageReceived) {
      console.log('✅ Test completed successfully!');
      console.log('✅ Chat service is responding to messages');
    } else {
      console.log('⚠️  Test completed but no messages were received');
    }
    
    process.exit(0);
  });
  
  // Timeout after 30 seconds
  setTimeout(() => {
    console.log('\n⏱️  Test timeout reached (30s)');
    ws.close();
    process.exit(1);
  }, 30000);
}

testWebSocketChat();