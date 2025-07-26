import { useQuery } from '@tanstack/react-query'
import { useAccount } from 'wagmi'
import { fetchPortfolio, fetchPortfolioHistory } from '@/lib/api/portfolio'

export function usePortfolio(chains?: number[]) {
  const { address } = useAccount()

  return useQuery({
    queryKey: ['portfolio', address, chains],
    queryFn: () => fetchPortfolio(address!, chains),
    enabled: !!address,
    refetchInterval: 30000, // Refetch every 30 seconds
  })
}

export function usePortfolioHistory(period: '24h' | '7d' | '30d' | '90d' | '1y' | 'all' = '7d') {
  const { address } = useAccount()

  return useQuery({
    queryKey: ['portfolio-history', address, period],
    queryFn: () => fetchPortfolioHistory(address!, period),
    enabled: !!address,
  })
}