import { useQuery } from '@tanstack/react-query'
import { useAccount } from 'wagmi'
import { fetchPortfolio, fetchPortfolioHistory, PortfolioResponse } from '@/lib/api/portfolio'

export function usePortfolio(chains?: number[]) {
  const { address } = useAccount()

  return useQuery({
    queryKey: ['portfolio', address, chains],
    queryFn: async () => {
      if (!address) throw new Error('No wallet address')
      
      try {
        // Use backend API to fetch portfolio data
        const portfolio = await fetchPortfolio(
          address,
          chains || [1, 137, 10, 42161] // Default chains
        )
        
        return portfolio
      } catch (error) {
        console.error('Failed to fetch portfolio:', error)
        // Return empty portfolio on error
        return {
          address: address,
          total_value_usd: 0,
          chains: [],
          tokens: [],
          last_updated: new Date().toISOString()
        }
      }
    },
    enabled: !!address,
    refetchInterval: 30000, // Refetch every 30 seconds
    retry: 3,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
  })
}

export function usePortfolioHistory(period: '24h' | '7d' | '30d' | '90d' | '1y' | 'all' = '7d') {
  const { address } = useAccount()

  return useQuery({
    queryKey: ['portfolio-history', address, period],
    queryFn: async () => {
      if (!address) throw new Error('No wallet address')
      
      try {
        return await fetchPortfolioHistory(address, period)
      } catch (error) {
        console.error('Failed to fetch portfolio history:', error)
        return {
          address: address,
          period,
          data: []
        }
      }
    },
    enabled: !!address,
  })
}

// Additional hook for portfolio statistics
export function usePortfolioStats(chains?: number[]) {
  const { data: portfolio, isLoading } = usePortfolio(chains)
  
  if (!portfolio || isLoading) {
    return {
      isLoading,
      stats: null
    }
  }
  
  // Calculate statistics from portfolio data
  const totalValue = portfolio.total_value_usd
  const tokenCount = portfolio.tokens.length
  const chainCount = new Set(portfolio.tokens.map(t => t.chain_id)).size
  
  // Find largest holding
  const largestHolding = portfolio.tokens.reduce((largest, token) => 
    token.balance_usd > (largest?.balance_usd || 0) ? token : largest,
    portfolio.tokens[0]
  )
  
  return {
    isLoading: false,
    stats: {
      totalValue,
      tokenCount,
      chainCount,
      largestHolding,
      diversificationScore: calculateDiversificationScore(portfolio.tokens),
      risk: assessRisk(portfolio.tokens)
    }
  }
}

function calculateDiversificationScore(tokens: any[]): number {
  if (tokens.length === 0) return 0
  
  const totalValue = tokens.reduce((sum, t) => sum + t.balance_usd, 0)
  const allocations = tokens.map(t => (t.balance_usd / totalValue) * 100)
  
  const hhi = allocations.reduce((sum, allocation) => {
    return sum + Math.pow(allocation / 100, 2)
  }, 0)
  
  return Math.round((1 - hhi) * 100)
}

function assessRisk(tokens: any[]): 'Low' | 'Medium' | 'High' {
  const score = calculateDiversificationScore(tokens)
  const totalValue = tokens.reduce((sum, t) => sum + t.balance_usd, 0)
  const largestAllocation = tokens.length > 0
    ? (tokens[0].balance_usd / totalValue) * 100
    : 0
  
  if (score >= 70 && largestAllocation < 40) {
    return 'Low'
  } else if (score >= 50 || largestAllocation < 60) {
    return 'Medium'
  } else {
    return 'High'
  }
}