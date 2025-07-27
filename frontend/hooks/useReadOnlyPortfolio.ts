import { useQuery } from '@tanstack/react-query'
import { getPortfolioService, OneInchAPIError } from '@/lib/api/1inch'
import { isAddress } from 'viem'

export function useReadOnlyPortfolio(
  address?: string,
  chains?: number[]
) {
  return useQuery({
    queryKey: ['portfolio', 'readonly', address, chains],
    queryFn: async () => {
      if (!address || !isAddress(address)) {
        throw new Error('Invalid address')
      }
      
      try {
        // Use 1inch API to fetch portfolio data for any address
        const portfolioService = getPortfolioService()
        const portfolio = await portfolioService.getPortfolio(
          address,
          chains || [1, 137, 10, 42161]
        )
        
        // Transform to match our existing interface
        return {
          address: portfolio.address,
          total_value_usd: portfolio.totalValueUSD,
          chains: portfolio.chains.map(c => c.chainId),
          tokens: portfolio.chains.flatMap(chain => 
            chain.tokens.map(token => ({
              address: token.address,
              symbol: token.symbol,
              name: token.name,
              decimals: token.decimals,
              chain_id: token.chainId,
              balance: token.balance,
              balance_usd: token.valueUSD,
              price_usd: token.priceUSD,
              logo_url: token.logoURI
            }))
          ),
          last_updated: portfolio.lastUpdated.toISOString(),
          isReadOnly: true
        }
      } catch (error) {
        if (error instanceof OneInchAPIError && error.message.includes('API key not configured')) {
          // Return empty portfolio when API key is missing
          return {
            address: address,
            total_value_usd: 0,
            chains: [],
            tokens: [],
            last_updated: new Date().toISOString(),
            isReadOnly: true
          }
        }
        // Re-throw other errors to be handled by React Query
        throw error
      }
    },
    enabled: !!address && isAddress(address),
    staleTime: 60000, // Consider data stale after 1 minute
    cacheTime: 300000, // Keep in cache for 5 minutes
    retry: 2,
  })
}

// Hook to handle both connected wallet and read-only viewing
export function usePortfolioView(viewAddress?: string) {
  const { data: ownPortfolio, isLoading: ownLoading, error: ownError } = usePortfolio()
  const { data: readOnlyPortfolio, isLoading: readOnlyLoading, error: readOnlyError } = useReadOnlyPortfolio(viewAddress)
  
  // If viewing another address, use read-only data
  if (viewAddress && isAddress(viewAddress)) {
    return {
      data: readOnlyPortfolio,
      isLoading: readOnlyLoading,
      error: readOnlyError,
      isReadOnly: true,
      viewingAddress: viewAddress
    }
  }
  
  // Otherwise use connected wallet data
  return {
    data: ownPortfolio,
    isLoading: ownLoading,
    error: ownError,
    isReadOnly: false,
    viewingAddress: null
  }
}

// Import the regular portfolio hook
import { usePortfolio } from './usePortfolio'