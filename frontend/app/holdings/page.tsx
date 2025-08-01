'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Search, TrendingUp, TrendingDown, RefreshCw, AlertCircle } from 'lucide-react'
import { usePortfolio } from '@/hooks/usePortfolio'
import { useAccount } from 'wagmi'
import { HoldingsPageSkeleton } from '@/components/ui/HoldingsSkeleton'


export default function HoldingsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'value' | 'change' | 'allocation'>('value')
  const [filterChain, setFilterChain] = useState<string>('all')
  const { isConnected, chain } = useAccount()
  const { data: portfolio, isLoading, error, refetch, isRefetching } = usePortfolio()
  
  // Check if on testnet
  const isTestnet = chain?.id === 11155111 || chain?.testnet === true

  // Transform portfolio data to holdings format
  const holdings = portfolio && portfolio.chains.length > 0 ? portfolio.chains.flatMap(chain => 
    chain.tokens.map(token => ({
      id: `${chain.chain_id}-${token.address}`,
      token: token.symbol,
      name: token.name,
      chain: chain.chain_name,
      chainId: chain.chain_id,
      balance: token.balance_human,
      value: token.balance_usd,
      price: token.price_usd,
      change24h: 0, // TODO: Implement 24h change calculation
      allocation: (token.balance_usd / portfolio.total_value_usd) * 100,
      address: token.address,
      logo_url: token.logo_url
    }))
  ) : []

  // Filter and sort holdings
  const filteredHoldings = holdings
    .filter(holding => {
      const matchesSearch = holding.token.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          holding.name.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesChain = filterChain === 'all' || holding.chain === filterChain
      return matchesSearch && matchesChain
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'value':
          return b.value - a.value
        case 'change':
          return b.change24h - a.change24h
        case 'allocation':
          return b.allocation - a.allocation
        default:
          return 0
      }
    })

  const totalValue = portfolio?.total_value_usd || 0
  
  // Calculate chain summary from real data
  const chainSummary = portfolio && portfolio.chains.length > 0 ? portfolio.chains.map(chain => ({
    chain: chain.chain_name,
    value: chain.total_value_usd,
    percentage: portfolio.total_value_usd > 0 ? (chain.total_value_usd / portfolio.total_value_usd) * 100 : 0,
    tokens: chain.tokens.length
  })) : []

  if (!isConnected) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-semibold mb-2">Connect Your Wallet</h2>
          <p className="text-muted-foreground">Please connect your wallet to view your holdings</p>
        </div>
      </div>
    )
  }
  
  if (isTestnet) {
    return (
      <div className="flex h-full items-center justify-center">
        <Card className="max-w-md p-8 text-center space-y-4">
          <div className="text-4xl mb-2">🧪</div>
          <h2 className="text-2xl font-semibold">Testnet Detected</h2>
          <p className="text-muted-foreground">
            You're connected to {chain?.name || 'a testnet'}. Holdings tracking is only available on mainnet networks.
          </p>
          <p className="text-sm text-muted-foreground">
            Please switch to Ethereum, Polygon, Optimism, Arbitrum, Base, Polygon zkEVM, World Chain, or Zora mainnet to view your holdings.
          </p>
        </Card>
      </div>
    )
  }

  if (isLoading) {
    return <HoldingsPageSkeleton />
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <Card className="max-w-md p-8 text-center space-y-4">
          <AlertCircle className="h-12 w-12 text-destructive mx-auto" />
          <h2 className="text-xl font-semibold">Failed to Load Portfolio</h2>
          <p className="text-muted-foreground">
            There was an error loading your portfolio data. This might be due to network issues or API limitations.
          </p>
          <button 
            onClick={() => refetch()}
            disabled={isRefetching}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
            {isRefetching ? 'Refreshing...' : 'Try Again'}
          </button>
        </Card>
      </div>
    )
  }

  return (
    <div className="px-8 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold">Holdings</h1>
          <p className="text-muted-foreground mt-1">Manage and track your digital assets across all chains</p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isRefetching}
          className="inline-flex items-center gap-2 px-3 py-1.5 text-sm bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
          {isRefetching ? 'Refreshing' : 'Refresh'}
        </button>
      </div>

      {/* Chain Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {chainSummary.map((chain) => (
          <Card key={chain.chain} className="p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium">{chain.chain}</h3>
              <span className="text-xs text-muted-foreground">{chain.tokens} tokens</span>
            </div>
            <p className="text-xl font-bold">${chain.value.toLocaleString()}</p>
            <div className="mt-2">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-muted-foreground">Portfolio %</span>
                <span>{chain.percentage.toFixed(1)}%</span>
              </div>
              <div className="w-full bg-background rounded-full h-2">
                <div 
                  className="bg-primary h-2 rounded-full transition-all duration-300"
                  style={{ width: `${chain.percentage}%` }}
                />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Controls */}
      <Card className="p-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search tokens..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-background border border-input rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          {/* Filter by Chain */}
          <select
            value={filterChain}
            onChange={(e) => setFilterChain(e.target.value)}
            className="px-4 py-2 bg-background border border-input rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="all">All Chains</option>
            {portfolio && portfolio.chains.map(chain => (
              <option key={chain.chain_id} value={chain.chain_name}>
                {chain.chain_name}
              </option>
            ))}
          </select>

          {/* Sort */}
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'value' | 'change' | 'allocation')}
            className="px-4 py-2 bg-background border border-input rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          >
            <option value="value">Sort by Value</option>
            <option value="change">Sort by 24h Change</option>
            <option value="allocation">Sort by Allocation</option>
          </select>
        </div>
      </Card>

      {/* Holdings Table */}
      <Card className="overflow-hidden">
        {filteredHoldings.length === 0 ? (
          <div className="p-12 text-center">
            <div className="mb-4">
              <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto" />
            </div>
            <h3 className="text-lg font-semibold mb-2">No Holdings Found</h3>
            <p className="text-muted-foreground mb-4">
              {holdings.length === 0 
                ? "You don't have any tokens in your portfolio yet."
                : "No tokens match your current filters."}
            </p>
            {holdings.length === 0 && (
              <button
                onClick={() => refetch()}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors"
              >
                <RefreshCw className="h-4 w-4" />
                Refresh Portfolio
              </button>
            )}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-background border-b border-border">
                <tr>
                  <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">Asset</th>
                  <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">Chain</th>
                  <th className="text-right px-6 py-4 text-sm font-medium text-muted-foreground">Balance</th>
                  <th className="text-right px-6 py-4 text-sm font-medium text-muted-foreground">Price</th>
                  <th className="text-right px-6 py-4 text-sm font-medium text-muted-foreground">Value</th>
                  <th className="text-right px-6 py-4 text-sm font-medium text-muted-foreground">24h Change</th>
                  <th className="text-right px-6 py-4 text-sm font-medium text-muted-foreground">Allocation</th>
                  <th className="text-center px-6 py-4 text-sm font-medium text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredHoldings.map((holding) => (
                <tr key={holding.id} className="border-b border-border hover:bg-accent/50 transition-colors">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      {holding.logo_url ? (
                        <img 
                          src={holding.logo_url} 
                          alt={holding.token}
                          className="w-10 h-10 rounded-full"
                          onError={(e) => {
                            e.currentTarget.style.display = 'none'
                            e.currentTarget.nextElementSibling?.classList.remove('hidden')
                          }}
                        />
                      ) : null}
                      <div className={`w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center ${holding.logo_url ? 'hidden' : ''}`}>
                        <span className="text-sm font-bold">{holding.token.slice(0, 2)}</span>
                      </div>
                      <div>
                        <p className="font-medium">{holding.token}</p>
                        <p className="text-sm text-muted-foreground">{holding.name}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-sm">{holding.chain}</span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <span className="font-medium">{holding.balance.toLocaleString()}</span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <span className="text-sm">${holding.price.toLocaleString()}</span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <span className="font-medium">${holding.value.toLocaleString()}</span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div className={`flex items-center justify-end gap-1 ${holding.change24h > 0 ? 'text-green-500' : holding.change24h < 0 ? 'text-red-500' : 'text-muted-foreground'}`}>
                      {holding.change24h > 0 ? (
                        <TrendingUp className="h-4 w-4" />
                      ) : holding.change24h < 0 ? (
                        <TrendingDown className="h-4 w-4" />
                      ) : null}
                      <span className="text-sm font-medium">
                        {holding.change24h > 0 ? '+' : ''}{holding.change24h.toFixed(2)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <div>
                      <p className="font-medium">{holding.allocation.toFixed(1)}%</p>
                      <div className="w-20 bg-background rounded-full h-1.5 mt-1">
                        <div 
                          className="bg-primary h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${holding.allocation}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center justify-center gap-2">
                      <button className="px-3 py-1.5 text-xs bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
                        Swap
                      </button>
                      <button className="px-3 py-1.5 text-xs bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/80 transition-colors">
                        Info
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        )}
      </Card>

      {/* Summary */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold mb-1">Portfolio Summary</h3>
            <p className="text-sm text-muted-foreground">
              {holdings.length} assets across {chainSummary.length} chains
            </p>
          </div>
          <div className="text-right">
            <p className="text-2xl font-bold">
              ${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
            <p className="text-sm text-muted-foreground">Total Portfolio Value</p>
          </div>
        </div>
      </Card>
    </div>
  )
}