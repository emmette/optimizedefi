import { getOneInchClient } from './client'

export interface TokenInfo {
  address: string
  chainId: number
  name: string
  symbol: string
  decimals: number
  logoURI?: string
  tags?: string[]
  eip2612?: boolean
  isFoT?: boolean // Fee on Transfer
  displayedSymbol?: string
}

export interface TokenList {
  [tokenAddress: string]: TokenInfo
}

export interface CustomToken {
  address: string
  chainId: number
}

export class TokensAPI {
  private get client() {
    const client = getOneInchClient()
    if (!client) {
      throw new Error('1inch API client not available')
    }
    return client
  }
  private tokenCache: Map<string, TokenList> = new Map()
  private CACHE_DURATION = 3600000 // 1 hour in ms
  private cacheTimestamps: Map<string, number> = new Map()

  /**
   * Get all supported tokens for a specific chain
   * @param chainId - The chain ID
   * @returns Map of token addresses to token information
   */
  async getTokens(chainId: number): Promise<TokenList> {
    const cacheKey = `tokens-${chainId}`
    
    // Check cache first
    if (this.isCacheValid(cacheKey)) {
      return this.tokenCache.get(cacheKey)!
    }

    try {
      const endpoint = `/swap/v6.0/${chainId}/tokens`
      const response = await this.client.get<{ tokens: TokenList }>(endpoint)
      
      // Cache the result
      this.tokenCache.set(cacheKey, response.tokens)
      this.cacheTimestamps.set(cacheKey, Date.now())
      
      return response.tokens
    } catch (error) {
      console.error(`Failed to fetch tokens for chain ${chainId}:`, error)
      return {}
    }
  }

  /**
   * Get token information by address
   * @param chainId - The chain ID
   * @param tokenAddress - The token contract address
   * @returns Token information or null if not found
   */
  async getTokenInfo(
    chainId: number,
    tokenAddress: string
  ): Promise<TokenInfo | null> {
    const tokens = await this.getTokens(chainId)
    const normalizedAddress = tokenAddress.toLowerCase()
    
    // Check if token exists in the list
    const tokenInfo = Object.values(tokens).find(
      token => token.address.toLowerCase() === normalizedAddress
    )
    
    if (tokenInfo) {
      return tokenInfo
    }

    // If not found, try to fetch custom token info
    return this.getCustomTokenInfo(chainId, tokenAddress)
  }

  /**
   * Get information for a custom token not in the default list
   * @param chainId - The chain ID
   * @param tokenAddress - The token contract address
   * @returns Token information or null if not found
   */
  async getCustomTokenInfo(
    chainId: number,
    tokenAddress: string
  ): Promise<TokenInfo | null> {
    try {
      const endpoint = `/swap/v6.0/${chainId}/custom/tokens`
      const response = await this.client.get<{ [key: string]: TokenInfo }>(
        endpoint,
        { addresses: tokenAddress }
      )
      
      return response[tokenAddress.toLowerCase()] || null
    } catch (error) {
      console.error(`Failed to fetch custom token info:`, error)
      return null
    }
  }

  /**
   * Get token information for multiple addresses
   * @param chainId - The chain ID
   * @param tokenAddresses - Array of token addresses
   * @returns Map of token addresses to token information
   */
  async getMultipleTokenInfo(
    chainId: number,
    tokenAddresses: string[]
  ): Promise<Map<string, TokenInfo>> {
    const tokens = await this.getTokens(chainId)
    const tokenMap = new Map<string, TokenInfo>()
    
    // First, check the cached token list
    tokenAddresses.forEach(address => {
      const normalizedAddress = address.toLowerCase()
      const tokenInfo = Object.values(tokens).find(
        token => token.address.toLowerCase() === normalizedAddress
      )
      if (tokenInfo) {
        tokenMap.set(normalizedAddress, tokenInfo)
      }
    })
    
    // Get custom tokens for addresses not found in the list
    const missingAddresses = tokenAddresses.filter(
      address => !tokenMap.has(address.toLowerCase())
    )
    
    if (missingAddresses.length > 0) {
      const customTokens = await this.getCustomTokenInfo(
        chainId,
        missingAddresses.join(',')
      )
      
      if (customTokens) {
        tokenMap.set(customTokens.address.toLowerCase(), customTokens)
      }
    }
    
    return tokenMap
  }

  /**
   * Search tokens by symbol or name
   * @param chainId - The chain ID
   * @param query - Search query
   * @returns Array of matching tokens
   */
  async searchTokens(
    chainId: number,
    query: string
  ): Promise<TokenInfo[]> {
    const tokens = await this.getTokens(chainId)
    const lowerQuery = query.toLowerCase()
    
    return Object.values(tokens).filter(token =>
      token.symbol.toLowerCase().includes(lowerQuery) ||
      token.name.toLowerCase().includes(lowerQuery) ||
      token.address.toLowerCase().includes(lowerQuery)
    )
  }

  /**
   * Get popular/common tokens for a chain
   * @param chainId - The chain ID
   * @returns Array of popular tokens
   */
  async getPopularTokens(chainId: number): Promise<TokenInfo[]> {
    const tokens = await this.getTokens(chainId)
    
    // Define popular token symbols per chain
    const popularSymbols: { [chainId: number]: string[] } = {
      1: ['USDT', 'USDC', 'DAI', 'WBTC', 'WETH', 'LINK', 'UNI', 'AAVE', 'CRV', 'SUSHI'],
      137: ['USDT', 'USDC', 'DAI', 'WETH', 'WBTC', 'MATIC', 'LINK', 'AAVE', 'CRV', 'SUSHI'],
      10: ['USDT', 'USDC', 'DAI', 'WETH', 'WBTC', 'OP', 'LINK', 'SNX'],
      42161: ['USDT', 'USDC', 'DAI', 'WETH', 'WBTC', 'ARB', 'LINK', 'GMX']
    }
    
    const symbols = popularSymbols[chainId] || []
    
    return Object.values(tokens).filter(token =>
      symbols.includes(token.symbol)
    ).slice(0, 10)
  }

  /**
   * Check if cache is valid
   * @param key - Cache key
   * @returns True if cache is valid
   */
  private isCacheValid(key: string): boolean {
    const timestamp = this.cacheTimestamps.get(key)
    if (!timestamp) return false
    
    return Date.now() - timestamp < this.CACHE_DURATION
  }

  /**
   * Clear token cache
   */
  clearCache(): void {
    this.tokenCache.clear()
    this.cacheTimestamps.clear()
  }
}

// Lazy initialization for TokensAPI
let _tokensAPIInstance: TokensAPI | null = null

export function getTokensAPI(): TokensAPI {
  if (!_tokensAPIInstance) {
    _tokensAPIInstance = new TokensAPI()
  }
  return _tokensAPIInstance
}