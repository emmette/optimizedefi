// Comprehensive integration test for OptimizeDeFi
const WebSocket = require('ws');

async function testIntegration() {
  console.log('🧪 OptimizeDeFi Integration Test');
  console.log('=====================================\n');
  
  const results = {
    backend: false,
    portfolio: false,
    websocket: false,
    chat: false
  };
  
  // Test 1: Backend Health Check
  console.log('1️⃣ Testing Backend Health...');
  try {
    const healthResponse = await fetch('http://localhost:8000/health');
    const healthData = await healthResponse.json();
    console.log(`✅ Backend is ${healthData.status}`);
    console.log(`   - 1inch API: ${healthData.integrations?.['1inch'] || 'unknown'}`);
    results.backend = true;
  } catch (error) {
    console.error('❌ Backend health check failed:', error.message);
  }
  
  // Test 2: Portfolio API (unauthenticated)
  console.log('\n2️⃣ Testing Portfolio API...');
  const testAddress = '0x742d35Cc6634C0532925a3b844Bc9e7595f5b8e7';
  try {
    const portfolioResponse = await fetch(`http://localhost:8000/api/portfolio/${testAddress}`);
    if (portfolioResponse.ok) {
      const portfolioData = await portfolioResponse.json();
      console.log('✅ Portfolio API accessible without auth');
      console.log(`   - Address: ${portfolioData.address}`);
      console.log(`   - Total Value: $${portfolioData.total_value_usd || 0}`);
      console.log(`   - Diversification Score: ${portfolioData.diversification_score || 'N/A'}`);
      results.portfolio = true;
    } else {
      console.error('❌ Portfolio API returned error:', portfolioResponse.status);
    }
  } catch (error) {
    console.error('❌ Portfolio API test failed:', error.message);
  }
  
  // Test 3: WebSocket Chat
  console.log('\n3️⃣ Testing WebSocket Chat Service...');
  await new Promise((resolve) => {
    const clientId = `test-client-${Date.now()}`;
    const ws = new WebSocket(`ws://localhost:8000/api/chat/ws/${clientId}`);
    let messageCount = 0;
    
    const timeout = setTimeout(() => {
      console.error('❌ WebSocket test timed out');
      ws.close();
      resolve();
    }, 15000);
    
    ws.on('open', () => {
      console.log('✅ WebSocket connected');
      results.websocket = true;
      
      const message = {
        type: 'message',
        content: 'What chains does OptimizeDeFi support?',
        metadata: { timestamp: new Date().toISOString() }
      };
      
      console.log('   Sending test message...');
      ws.send(JSON.stringify(message));
    });
    
    ws.on('message', (data) => {
      messageCount++;
      try {
        const message = JSON.parse(data.toString());
        if (message.type === 'ai_response') {
          console.log('✅ Received AI response');
          console.log(`   - Response preview: ${message.content.substring(0, 80)}...`);
          results.chat = true;
          
          clearTimeout(timeout);
          ws.close();
          resolve();
        }
      } catch (error) {
        console.error('   Error parsing message:', error.message);
      }
    });
    
    ws.on('error', (error) => {
      console.error('❌ WebSocket error:', error.message);
      clearTimeout(timeout);
      resolve();
    });
    
    ws.on('close', () => {
      console.log(`   WebSocket closed (received ${messageCount} messages)`);
      clearTimeout(timeout);
      resolve();
    });
  });
  
  // Test 4: Frontend Server
  console.log('\n4️⃣ Testing Frontend Server...');
  try {
    const frontendResponse = await fetch('http://localhost:3001');
    if (frontendResponse.ok) {
      console.log('✅ Frontend server is running on port 3001');
    } else {
      console.log(`⚠️  Frontend returned status: ${frontendResponse.status}`);
    }
  } catch (error) {
    console.error('❌ Frontend server test failed:', error.message);
  }
  
  // Summary
  console.log('\n=====================================');
  console.log('📊 Test Summary:');
  console.log(`   Backend Health: ${results.backend ? '✅' : '❌'}`);
  console.log(`   Portfolio API:  ${results.portfolio ? '✅' : '❌'}`);
  console.log(`   WebSocket:      ${results.websocket ? '✅' : '❌'}`);
  console.log(`   Chat Service:   ${results.chat ? '✅' : '❌'}`);
  
  const allPassed = Object.values(results).every(v => v);
  console.log(`\n${allPassed ? '✅ All tests passed!' : '⚠️  Some tests failed'}`);
  
  if (allPassed) {
    console.log('\n🎉 OptimizeDeFi is fully functional!');
    console.log('   - Frontend: http://localhost:3001');
    console.log('   - Backend API: http://localhost:8000');
    console.log('   - WebSocket Chat: Working');
    console.log('   - Portfolio Data: Accessible');
  }
}

testIntegration().catch(console.error);