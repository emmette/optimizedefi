// Mock data service for development
// This will be replaced with actual API calls in production

export interface Token {
  id: string
  symbol: string
  name: string
  address: string
  chainId: number
  chain: string
  balance: string
  value: number
  price: number
  change24h: number
  logo: string
}

export interface PortfolioData {
  totalValue: number
  change24h: number
  changeValue24h: number
  tokens: Token[]
}

export interface ChainDistribution {
  chain: string
  chainId: number
  value: number
  percentage: number
  tokenCount: number
}

// Base token data
const baseTokens: Omit<Token, 'id' | 'balance' | 'value'>[] = [
  {
    symbol: 'ETH',
    name: 'Ethereum',
    address: '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE',
    chainId: 1,
    chain: 'Ethereum',
    price: 2000,
    change24h: 2.34,
    logo: 'https://tokens.1inch.io/0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee.png'
  },
  {
    symbol: 'USDC',
    name: 'USD Coin',
    address: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
    chainId: 1,
    chain: 'Ethereum',
    price: 1,
    change24h: 0.01,
    logo: 'https://tokens.1inch.io/0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48.png'
  },
  {
    symbol: 'MATIC',
    name: 'Polygon',
    address: '0x0000000000000000000000000000000000001010',
    chainId: 137,
    chain: 'Polygon',
    price: 0.8,
    change24h: -1.23,
    logo: 'https://tokens.1inch.io/0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0.png'
  },
  {
    symbol: 'OP',
    name: 'Optimism',
    address: '0x4200000000000000000000000000000000000042',
    chainId: 10,
    chain: 'Optimism',
    price: 2,
    change24h: 5.67,
    logo: 'https://tokens.1inch.io/0x4200000000000000000000000000000000000042.png'
  },
  {
    symbol: 'ARB',
    name: 'Arbitrum',
    address: '0x912CE59144191C1204E64559FE8253a0e49E6548',
    chainId: 42161,
    chain: 'Arbitrum',
    price: 1,
    change24h: 3.45,
    logo: 'https://tokens.1inch.io/0x912ce59144191c1204e64559fe8253a0e49e6548.png'
  },
  {
    symbol: 'LINK',
    name: 'Chainlink',
    address: '0x514910771AF9Ca656af840dff83E8264EcF986CA',
    chainId: 1,
    chain: 'Ethereum',
    price: 15,
    change24h: -3.45,
    logo: 'https://tokens.1inch.io/0x514910771af9ca656af840dff83e8264ecf986ca.png'
  },
  {
    symbol: 'UNI',
    name: 'Uniswap',
    address: '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984',
    chainId: 1,
    chain: 'Ethereum',
    price: 5.5,
    change24h: -2.11,
    logo: 'https://tokens.1inch.io/0x1f9840a85d5af5bf1d1762f925bdaddc4201f984.png'
  }
]

// Generate mock portfolio data
export function getMockPortfolioData(): PortfolioData {
  const tokens: Token[] = baseTokens.map((token, index) => {
    const balance = Math.random() * 10000
    const value = balance * token.price
    return {
      ...token,
      id: `${token.chainId}-${token.address}`,
      balance: balance.toFixed(4),
      value: value
    }
  })

  const totalValue = tokens.reduce((sum, token) => sum + token.value, 0)
  const change24h = 2.34 // Mock overall change
  const changeValue24h = totalValue * (change24h / 100)

  return {
    totalValue,
    change24h,
    changeValue24h,
    tokens
  }
}

// Get chain distribution
export function getChainDistribution(tokens: Token[]): ChainDistribution[] {
  const chainMap = new Map<number, ChainDistribution>()

  tokens.forEach(token => {
    const existing = chainMap.get(token.chainId) || {
      chain: token.chain,
      chainId: token.chainId,
      value: 0,
      percentage: 0,
      tokenCount: 0
    }

    existing.value += token.value
    existing.tokenCount += 1
    chainMap.set(token.chainId, existing)
  })

  const totalValue = tokens.reduce((sum, token) => sum + token.value, 0)
  const distributions = Array.from(chainMap.values())

  distributions.forEach(dist => {
    dist.percentage = (dist.value / totalValue) * 100
  })

  return distributions.sort((a, b) => b.value - a.value)
}

// Generate historical data
export function generateHistoricalData(days: number = 30) {
  const data = []
  const baseValue = 100000
  const now = new Date()

  for (let i = days; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    
    // Add some randomness to simulate price movement
    const change = (Math.random() - 0.45) * 0.02 // -1% to +1.1% daily change
    const value = baseValue * (1 + (days - i) * 0.0015 + change * 10)
    
    data.push({
      date: date.toISOString().split('T')[0],
      value: Math.round(value * 100) / 100
    })
  }

  return data
}

// Mock swap quote
export function getMockSwapQuote(
  fromToken: string,
  toToken: string,
  amount: number
) {
  // Simple mock exchange rate
  const rates: Record<string, Record<string, number>> = {
    'ETH': { 'USDC': 2000, 'MATIC': 2500, 'OP': 1000, 'ARB': 2000 },
    'USDC': { 'ETH': 0.0005, 'MATIC': 1.25, 'OP': 0.5, 'ARB': 1 },
    'MATIC': { 'ETH': 0.0004, 'USDC': 0.8, 'OP': 0.4, 'ARB': 0.8 },
    'OP': { 'ETH': 0.001, 'USDC': 2, 'MATIC': 2.5, 'ARB': 2 },
    'ARB': { 'ETH': 0.0005, 'USDC': 1, 'MATIC': 1.25, 'OP': 0.5 }
  }

  const rate = rates[fromToken]?.[toToken] || 1
  const toAmount = amount * rate
  const priceImpact = amount > 10000 ? 0.5 : 0.1
  const gasFee = 12.34

  return {
    fromToken,
    toToken,
    fromAmount: amount,
    toAmount,
    rate,
    priceImpact,
    gasFee,
    protocols: [
      { name: 'Uniswap V3', part: 60 },
      { name: 'SushiSwap', part: 40 }
    ]
  }
}