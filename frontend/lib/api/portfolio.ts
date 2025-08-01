import { API_BASE_URL, API_ENDPOINTS } from './config'
import { useAuthStore } from '@/store/authStore'

function getAuthHeaders(): HeadersInit {
  const accessToken = useAuthStore.getState().accessToken
  if (accessToken) {
    return {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    }
  }
  return {
    'Content-Type': 'application/json'
  }
}

export interface Token {
  address: string
  symbol: string
  name: string
  decimals: number
  chain_id: number
  balance: string
  balance_human: number
  balance_usd: number
  price_usd: number
  logo_url?: string
}

export interface ChainData {
  chain_id: number
  chain_name: string
  total_value_usd: number
  tokens: Token[]
}

export interface PortfolioResponse {
  address: string
  total_value_usd: number
  chains: ChainData[]
  diversification_score: number
  risk_assessment: Record<string, any>
  performance: Record<string, any>
  last_updated: string
}

export interface PortfolioHistoryResponse {
  address: string
  period: string
  data: Array<{
    timestamp: string
    value_usd: number
  }>
}

export async function fetchPortfolio(
  address: string,
  chains?: number[]
): Promise<PortfolioResponse> {
  const params = new URLSearchParams()
  if (chains) {
    chains.forEach(chain => params.append('chains', chain.toString()))
  }
  
  const url = `${API_BASE_URL}${API_ENDPOINTS.portfolio(address)}${params.toString() ? `?${params}` : ''}`
  
  const response = await fetch(url, {
    headers: getAuthHeaders()
  })
  if (!response.ok) {
    throw new Error(`Failed to fetch portfolio: ${response.statusText}`)
  }
  
  return response.json()
}

export async function fetchPortfolioHistory(
  address: string,
  period: '24h' | '7d' | '30d' | '90d' | '1y' | 'all' = '7d'
): Promise<PortfolioHistoryResponse> {
  const url = `${API_BASE_URL}${API_ENDPOINTS.portfolioHistory(address)}?period=${period}`
  
  const response = await fetch(url, {
    headers: getAuthHeaders()
  })
  if (!response.ok) {
    throw new Error(`Failed to fetch portfolio history: ${response.statusText}`)
  }
  
  return response.json()
}