// Test script to verify portfolio API is working

async function testPortfolioAPI() {
  const testAddress = '0x742d35Cc6634C0532925a3b844Bc9e7595f5b8e7'
  
  console.log('🧪 Testing Portfolio API...')
  console.log('================================')
  
  try {
    // Test backend portfolio endpoint
    console.log(`\n📊 Fetching portfolio for ${testAddress}...`)
    const response = await fetch(`http://localhost:8000/api/portfolio/${testAddress}`)
    
    console.log('Response status:', response.status)
    
    if (!response.ok) {
      console.error('❌ Failed to fetch portfolio:', response.statusText)
      const errorText = await response.text()
      console.error('Error details:', errorText)
      return
    }
    
    const data = await response.json()
    console.log('✅ Portfolio data received:')
    console.log('- Total Value:', data.total_value_usd ? `$${data.total_value_usd.toFixed(2)}` : '$0.00')
    console.log('- Chains:', data.chains?.length || 0)
    console.log('- Diversification Score:', data.diversification_score || 'N/A')
    
  } catch (error) {
    console.error('❌ Error:', error)
  }
  
  console.log('\n================================')
  console.log('✅ Test completed!')
}

testPortfolioAPI()