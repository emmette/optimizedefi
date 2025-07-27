import { getOneInchClient } from './client'

export interface TokenPrice {
  [tokenAddress: string]: string // Price in USD as string
}

export interface PriceData {
  tokenAddress: string
  priceUSD: number
  chainId: number
  timestamp: number
}

export class PricesAPI {
  private get client() {
    const client = getOneInchClient()
    if (!client) {
      throw new Error('1inch API client not available')
    }
    return client
  }
  private priceCache: Map<string, TokenPrice> = new Map()
  private CACHE_DURATION = 60000 // 1 minute for prices
  private cacheTimestamps: Map<string, number> = new Map()

  /**
   * Get USD prices for multiple tokens on a specific chain
   * @param chainId - The chain ID
   * @param tokenAddresses - Array of token addresses
   * @param currency - Currency for prices (default: USD)
   * @returns Map of token addresses to prices
   */
  async getTokenPrices(
    chainId: number,
    tokenAddresses: string[],
    currency: string = 'USD'
  ): Promise<TokenPrice> {
    if (tokenAddresses.length === 0) {
      return {}
    }

    const cacheKey = `prices-${chainId}-${tokenAddresses.sort().join(',')}-${currency}`
    
    // Check cache first
    if (this.isCacheValid(cacheKey)) {
      return this.priceCache.get(cacheKey)!
    }

    try {
      const endpoint = `/price/v1.1/${chainId}`
      const response = await this.client.get<TokenPrice>(endpoint, {
        addresses: tokenAddresses.join(','),
        currency
      })
      
      // Cache the result
      this.priceCache.set(cacheKey, response)
      this.cacheTimestamps.set(cacheKey, Date.now())
      
      return response
    } catch (error) {
      console.error(`Failed to fetch prices for chain ${chainId}:`, error)
      return {}
    }
  }

  /**
   * Get USD price for a single token
   * @param chainId - The chain ID
   * @param tokenAddress - Token address
   * @returns Price in USD or null if not found
   */
  async getTokenPrice(
    chainId: number,
    tokenAddress: string
  ): Promise<number | null> {
    const prices = await this.getTokenPrices(chainId, [tokenAddress])
    const priceStr = prices[tokenAddress.toLowerCase()]
    
    if (!priceStr) return null
    
    return parseFloat(priceStr)
  }

  /**
   * Get native token price for a chain
   * @param chainId - The chain ID
   * @returns Native token price in USD
   */
  async getNativeTokenPrice(chainId: number): Promise<number | null> {
    const nativeTokenAddress = '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
    return this.getTokenPrice(chainId, nativeTokenAddress)
  }

  /**
   * Calculate total value for token balances
   * @param chainId - The chain ID
   * @param balances - Map of token addresses to balances (in wei)
   * @param tokenDecimals - Map of token addresses to decimals
   * @returns Total value in USD
   */
  async calculateTotalValue(
    chainId: number,
    balances: { [tokenAddress: string]: string },
    tokenDecimals: { [tokenAddress: string]: number }
  ): Promise<number> {
    const tokenAddresses = Object.keys(balances)
    if (tokenAddresses.length === 0) return 0

    const prices = await this.getTokenPrices(chainId, tokenAddresses)
    
    let totalValue = 0
    
    for (const [tokenAddress, balance] of Object.entries(balances)) {
      const price = prices[tokenAddress.toLowerCase()]
      const decimals = tokenDecimals[tokenAddress.toLowerCase()] || 18
      
      if (price && balance !== '0') {
        const tokenAmount = Number(balance) / Math.pow(10, decimals)
        const tokenValue = tokenAmount * parseFloat(price)
        totalValue += tokenValue
      }
    }
    
    return totalValue
  }

  /**
   * Get price data with additional metadata
   * @param chainId - The chain ID
   * @param tokenAddresses - Array of token addresses
   * @returns Array of price data with metadata
   */
  async getPriceData(
    chainId: number,
    tokenAddresses: string[]
  ): Promise<PriceData[]> {
    const prices = await this.getTokenPrices(chainId, tokenAddresses)
    const timestamp = Date.now()
    
    return Object.entries(prices).map(([tokenAddress, priceStr]) => ({
      tokenAddress,
      priceUSD: parseFloat(priceStr),
      chainId,
      timestamp
    }))
  }

  /**
   * Get prices across multiple chains
   * @param tokensByChain - Map of chain IDs to token addresses
   * @returns Map of chain IDs to token prices
   */
  async getMultiChainPrices(
    tokensByChain: { [chainId: number]: string[] }
  ): Promise<{ [chainId: number]: TokenPrice }> {
    const pricePromises = Object.entries(tokensByChain).map(
      async ([chainId, addresses]) => {
        const prices = await this.getTokenPrices(Number(chainId), addresses)
        return { chainId: Number(chainId), prices }
      }
    )
    
    const results = await Promise.allSettled(pricePromises)
    const multiChainPrices: { [chainId: number]: TokenPrice } = {}
    
    results.forEach(result => {
      if (result.status === 'fulfilled') {
        multiChainPrices[result.value.chainId] = result.value.prices
      }
    })
    
    return multiChainPrices
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
   * Clear price cache
   */
  clearCache(): void {
    this.priceCache.clear()
    this.cacheTimestamps.clear()
  }

  /**
   * Format price for display
   * @param price - Price value
   * @param decimals - Number of decimal places
   * @returns Formatted price string
   */
  formatPrice(price: number, decimals: number = 2): string {
    if (price < 0.01) {
      return price.toExponential(2)
    }
    return price.toFixed(decimals)
  }
}

// Lazy initialization for PricesAPI
let _pricesAPIInstance: PricesAPI | null = null

export function getPricesAPI(): PricesAPI {
  if (!_pricesAPIInstance) {
    _pricesAPIInstance = new PricesAPI()
  }
  return _pricesAPIInstance
}