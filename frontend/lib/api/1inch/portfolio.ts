import { getBalancesAPI } from './balances'
import { getTokensAPI } from './tokens'
import { getPricesAPI } from './prices'

export interface PortfolioToken {
  address: string
  symbol: string
  name: string
  decimals: number
  balance: string
  balanceFormatted: number
  priceUSD: number
  valueUSD: number
  chainId: number
  chainName: string
  logoURI?: string
  allocation?: number // Percentage of total portfolio
}

export interface ChainPortfolio {
  chainId: number
  chainName: string
  totalValueUSD: number
  tokens: PortfolioToken[]
  nativeToken?: PortfolioToken
}

export interface Portfolio {
  address: string
  totalValueUSD: number
  chains: ChainPortfolio[]
  topTokens: PortfolioToken[]
  lastUpdated: Date
}

const CHAIN_NAMES: { [chainId: number]: string } = {
  1: 'Ethereum',
  137: 'Polygon',
  10: 'Optimism',
  42161: 'Arbitrum',
  43114: 'Avalanche',
  56: 'BSC',
  100: 'Gnosis',
  250: 'Fantom',
  8453: 'Base'
}

export class PortfolioService {
  /**
   * Get complete portfolio data for a wallet address
   * @param walletAddress - The wallet address
   * @param chainIds - Array of chain IDs to include
   * @returns Complete portfolio data
   */
  async getPortfolio(
    walletAddress: string,
    chainIds: number[] = [1, 137, 10, 42161]
  ): Promise<Portfolio> {
    // Fetch balances for all chains
    const balancesAPI = getBalancesAPI()
    const chainBalances = await balancesAPI.getAllNonZeroBalances(
      walletAddress,
      chainIds
    )
    
    // Process each chain's portfolio
    const chainPortfolios = await Promise.all(
      chainBalances.map(async (chainBalance) => {
        return this.processChainPortfolio(
          chainBalance.chainId,
          chainBalance.balances
        )
      })
    )
    
    // Calculate total portfolio value
    const totalValueUSD = chainPortfolios.reduce(
      (total, chain) => total + chain.totalValueUSD,
      0
    )
    
    // Get top tokens across all chains
    const allTokens = chainPortfolios.flatMap(chain => chain.tokens)
    const topTokens = this.getTopTokens(allTokens, totalValueUSD)
    
    return {
      address: walletAddress,
      totalValueUSD,
      chains: chainPortfolios,
      topTokens,
      lastUpdated: new Date()
    }
  }

  /**
   * Process portfolio data for a single chain
   * @param chainId - The chain ID
   * @param balances - Token balances
   * @returns Chain portfolio data
   */
  private async processChainPortfolio(
    chainId: number,
    balances: { [tokenAddress: string]: string }
  ): Promise<ChainPortfolio> {
    const tokenAddresses = Object.keys(balances)
    
    // Fetch token metadata and prices in parallel
    const tokensAPI = getTokensAPI()
    const pricesAPI = getPricesAPI()
    const [tokenInfoMap, prices] = await Promise.all([
      tokensAPI.getMultipleTokenInfo(chainId, tokenAddresses),
      pricesAPI.getTokenPrices(chainId, tokenAddresses)
    ])
    
    // Process each token
    const tokens: PortfolioToken[] = []
    let totalValueUSD = 0
    
    for (const [tokenAddress, balance] of Object.entries(balances)) {
      const tokenInfo = tokenInfoMap.get(tokenAddress.toLowerCase())
      const price = prices[tokenAddress.toLowerCase()]
      
      if (tokenInfo && price) {
        const balanceFormatted = Number(balance) / Math.pow(10, tokenInfo.decimals)
        const valueUSD = balanceFormatted * parseFloat(price)
        
        const portfolioToken: PortfolioToken = {
          address: tokenAddress,
          symbol: tokenInfo.symbol,
          name: tokenInfo.name,
          decimals: tokenInfo.decimals,
          balance,
          balanceFormatted,
          priceUSD: parseFloat(price),
          valueUSD,
          chainId,
          chainName: CHAIN_NAMES[chainId] || `Chain ${chainId}`,
          logoURI: tokenInfo.logoURI
        }
        
        tokens.push(portfolioToken)
        totalValueUSD += valueUSD
      }
    }
    
    // Sort tokens by value
    tokens.sort((a, b) => b.valueUSD - a.valueUSD)
    
    // Calculate allocations
    tokens.forEach(token => {
      token.allocation = totalValueUSD > 0 
        ? (token.valueUSD / totalValueUSD) * 100 
        : 0
    })
    
    // Find native token if present
    const nativeToken = tokens.find(
      t => t.address.toLowerCase() === '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
    )
    
    return {
      chainId,
      chainName: CHAIN_NAMES[chainId] || `Chain ${chainId}`,
      totalValueUSD,
      tokens,
      nativeToken
    }
  }

  /**
   * Get top tokens by value across all chains
   * @param allTokens - All tokens from all chains
   * @param totalValue - Total portfolio value
   * @param limit - Number of top tokens to return
   * @returns Array of top tokens
   */
  private getTopTokens(
    allTokens: PortfolioToken[],
    totalValue: number,
    limit: number = 10
  ): PortfolioToken[] {
    // Sort by value and take top tokens
    const sorted = [...allTokens].sort((a, b) => b.valueUSD - a.valueUSD)
    const topTokens = sorted.slice(0, limit)
    
    // Recalculate allocations based on total portfolio
    topTokens.forEach(token => {
      token.allocation = totalValue > 0 
        ? (token.valueUSD / totalValue) * 100 
        : 0
    })
    
    return topTokens
  }

  /**
   * Get portfolio summary statistics
   * @param portfolio - Portfolio data
   * @returns Summary statistics
   */
  getPortfolioStats(portfolio: Portfolio) {
    const chainCount = portfolio.chains.length
    const tokenCount = portfolio.chains.reduce(
      (count, chain) => count + chain.tokens.length,
      0
    )
    
    const largestChain = portfolio.chains.reduce(
      (largest, chain) => 
        chain.totalValueUSD > (largest?.totalValueUSD || 0) ? chain : largest,
      portfolio.chains[0]
    )
    
    const largestToken = portfolio.topTokens[0]
    
    const diversificationScore = this.calculateDiversificationScore(
      portfolio.topTokens.map(t => t.allocation || 0)
    )
    
    return {
      totalValue: portfolio.totalValueUSD,
      chainCount,
      tokenCount,
      largestChain,
      largestToken,
      diversificationScore,
      risk: this.assessRisk(diversificationScore, largestToken?.allocation || 0)
    }
  }

  /**
   * Calculate diversification score (0-100)
   * @param allocations - Array of allocation percentages
   * @returns Diversification score
   */
  private calculateDiversificationScore(allocations: number[]): number {
    if (allocations.length === 0) return 0
    
    // Use Herfindahl-Hirschman Index (HHI)
    const hhi = allocations.reduce((sum, allocation) => {
      return sum + Math.pow(allocation / 100, 2)
    }, 0)
    
    // Convert HHI to diversification score (0-100)
    // HHI ranges from 0 to 1, where 1 is fully concentrated
    return Math.round((1 - hhi) * 100)
  }

  /**
   * Assess portfolio risk level
   * @param diversificationScore - Diversification score
   * @param largestAllocation - Largest token allocation percentage
   * @returns Risk level
   */
  private assessRisk(
    diversificationScore: number,
    largestAllocation: number
  ): 'Low' | 'Medium' | 'High' {
    if (diversificationScore >= 70 && largestAllocation < 40) {
      return 'Low'
    } else if (diversificationScore >= 50 || largestAllocation < 60) {
      return 'Medium'
    } else {
      return 'High'
    }
  }
}

// Lazy initialization for PortfolioService
let _portfolioServiceInstance: PortfolioService | null = null

export function getPortfolioService(): PortfolioService {
  if (!_portfolioServiceInstance) {
    _portfolioServiceInstance = new PortfolioService()
  }
  return _portfolioServiceInstance
}