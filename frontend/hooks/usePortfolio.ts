import { useQuery } from '@tanstack/react-query'
import { useAccount } from 'wagmi'
import { fetchPortfolio, fetchPortfolioHistory, PortfolioResponse, Token } from '@/lib/api/portfolio'

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
          chains || [1, 137, 42161, 42170, 10, 8453, 1101, 810180, 7777777] // All supported chains
        )
        
        return portfolio
      } catch (error) {
        console.error('Failed to fetch portfolio:', error)
        // Return empty portfolio on error with proper structure
        return {
          address: address,
          total_value_usd: 0,
          chains: [],
          diversification_score: 0,
          risk_assessment: { score: 0, level: 'Unknown' },
          performance: { change_24h: 0, change_7d: 0 },
          last_updated: new Date().toISOString()
        } as PortfolioResponse
      }
    },
    enabled: !!address,
    refetchInterval: 30000, // Refetch every 30 seconds
    retry: 3,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
    staleTime: 10000, // Consider data stale after 10 seconds
    gcTime: 5 * 60 * 1000, // Keep data in cache for 5 minutes
    refetchOnWindowFocus: false, // Don't refetch when tab gains focus
    refetchOnReconnect: true // Refetch when connection is restored
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
    retry: 2,
    retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 10000),
    staleTime: 60000, // Consider data stale after 1 minute
    gcTime: 10 * 60 * 1000, // Keep data in cache for 10 minutes
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
  
  // Flatten tokens from all chains
  const allTokens = portfolio.chains.flatMap(chain => 
    chain.tokens.map(token => ({
      ...token,
      chain_id: chain.chain_id,
      chain_name: chain.chain_name
    }))
  )
  
  // Calculate statistics from portfolio data
  const totalValue = portfolio.total_value_usd
  const tokenCount = allTokens.length
  const chainCount = portfolio.chains.length
  
  // Find largest holding
  const largestHolding = allTokens.reduce((largest, token) => 
    token.balance_usd > (largest?.balance_usd || 0) ? token : largest,
    allTokens[0]
  )
  
  return {
    isLoading: false,
    stats: {
      totalValue,
      tokenCount,
      chainCount,
      largestHolding,
      diversificationScore: calculateDiversificationScore(allTokens),
      risk: assessRisk(allTokens)
    }
  }
}

interface ExtendedToken extends Token {
  chain_id: number
  chain_name: string
}

function calculateDiversificationScore(tokens: ExtendedToken[]): number {
  if (tokens.length === 0) return 0
  
  const totalValue = tokens.reduce((sum, t) => sum + t.balance_usd, 0)
  if (totalValue === 0) return 0
  
  const allocations = tokens.map(t => (t.balance_usd / totalValue) * 100)
  
  const hhi = allocations.reduce((sum, allocation) => {
    return sum + Math.pow(allocation / 100, 2)
  }, 0)
  
  return Math.round((1 - hhi) * 100)
}

function assessRisk(tokens: ExtendedToken[]): 'Low' | 'Medium' | 'High' {
  const score = calculateDiversificationScore(tokens)
  const totalValue = tokens.reduce((sum, t) => sum + t.balance_usd, 0)
  
  if (totalValue === 0 || tokens.length === 0) return 'High'
  
  // Sort tokens by value to find largest allocation
  const sortedTokens = [...tokens].sort((a, b) => b.balance_usd - a.balance_usd)
  const largestAllocation = (sortedTokens[0].balance_usd / totalValue) * 100
  
  if (score >= 70 && largestAllocation < 40) {
    return 'Low'
  } else if (score >= 50 || largestAllocation < 60) {
    return 'Medium'
  } else {
    return 'High'
  }
}