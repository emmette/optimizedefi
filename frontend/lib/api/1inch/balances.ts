import { getOneInchClient } from './client'

export interface TokenBalance {
  tokenAddress: string
  balance: string
  chainId: number
}

export interface WalletBalance {
  [tokenAddress: string]: string
}

export interface ChainBalances {
  chainId: number
  balances: WalletBalance
}

export class BalancesAPI {
  private get client() {
    const client = getOneInchClient()
    if (!client) {
      throw new Error('1inch API client not available')
    }
    return client
  }

  /**
   * Get token balances for a wallet address on a specific chain
   * @param chainId - The chain ID (1 for Ethereum, 137 for Polygon, etc.)
   * @param walletAddress - The wallet address to query
   * @returns Token balances mapping
   */
  async getBalances(
    chainId: number,
    walletAddress: string
  ): Promise<WalletBalance> {
    try {
      const endpoint = `/balance/v1.2/${chainId}/balances/${walletAddress}`
      const response = await this.client.get<WalletBalance>(endpoint)
      return response
    } catch (error) {
      console.error(`Failed to fetch balances for chain ${chainId}:`, error)
      return {}
    }
  }

  /**
   * Get token balances across multiple chains
   * @param walletAddress - The wallet address to query
   * @param chainIds - Array of chain IDs to query
   * @returns Array of balances per chain
   */
  async getMultiChainBalances(
    walletAddress: string,
    chainIds: number[] = [1, 137, 10, 42161] // Ethereum, Polygon, Optimism, Arbitrum
  ): Promise<ChainBalances[]> {
    const balancePromises = chainIds.map(async (chainId) => {
      const balances = await this.getBalances(chainId, walletAddress)
      return {
        chainId,
        balances
      }
    })

    const results = await Promise.allSettled(balancePromises)
    
    return results
      .filter((result): result is PromiseFulfilledResult<ChainBalances> => 
        result.status === 'fulfilled'
      )
      .map(result => result.value)
  }

  /**
   * Get native token balance (ETH, MATIC, etc.) for a wallet
   * @param chainId - The chain ID
   * @param walletAddress - The wallet address to query
   * @returns Native token balance in wei
   */
  async getNativeBalance(
    chainId: number,
    walletAddress: string
  ): Promise<string> {
    const balances = await this.getBalances(chainId, walletAddress)
    // Native token is represented by a special address in 1inch
    const nativeTokenAddress = '0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee'
    return balances[nativeTokenAddress] || '0'
  }

  /**
   * Filter out zero balances and dust amounts
   * @param balances - Token balances to filter
   * @param threshold - Minimum balance threshold (in wei)
   * @returns Filtered balances
   */
  filterNonZeroBalances(
    balances: WalletBalance,
    threshold: string = '1000000' // Default to 1M wei
  ): WalletBalance {
    const filtered: WalletBalance = {}
    
    Object.entries(balances).forEach(([tokenAddress, balance]) => {
      if (BigInt(balance) > BigInt(threshold)) {
        filtered[tokenAddress] = balance
      }
    })
    
    return filtered
  }

  /**
   * Get all non-zero balances across multiple chains
   * @param walletAddress - The wallet address to query
   * @param chainIds - Array of chain IDs to query
   * @returns Filtered balances per chain
   */
  async getAllNonZeroBalances(
    walletAddress: string,
    chainIds: number[] = [1, 137, 10, 42161]
  ): Promise<ChainBalances[]> {
    const allBalances = await this.getMultiChainBalances(walletAddress, chainIds)
    
    return allBalances.map(chainBalance => ({
      chainId: chainBalance.chainId,
      balances: this.filterNonZeroBalances(chainBalance.balances)
    })).filter(chainBalance => Object.keys(chainBalance.balances).length > 0)
  }
}

// Lazy initialization for BalancesAPI
let _balancesAPIInstance: BalancesAPI | null = null

export function getBalancesAPI(): BalancesAPI {
  if (!_balancesAPIInstance) {
    _balancesAPIInstance = new BalancesAPI()
  }
  return _balancesAPIInstance
}