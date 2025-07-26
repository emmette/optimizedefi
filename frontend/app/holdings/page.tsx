'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { Search, TrendingUp, TrendingDown } from 'lucide-react'
// import { usePortfolio } from '@/hooks/usePortfolio'
// import { useAccount } from 'wagmi'

// Mock holdings data
const mockHoldings = [
  {
    id: 1,
    token: 'ETH',
    name: 'Ethereum',
    chain: 'Ethereum',
    balance: 12.5,
    value: 45000,
    price: 3600,
    change24h: 2.34,
    allocation: 35.9,
  },
  {
    id: 2,
    token: 'MATIC',
    name: 'Polygon',
    chain: 'Polygon',
    balance: 15000,
    value: 32000,
    price: 2.13,
    change24h: -1.2,
    allocation: 25.5,
  },
  {
    id: 3,
    token: 'OP',
    name: 'Optimism',
    chain: 'Optimism',
    balance: 8500,
    value: 28432.56,
    price: 3.35,
    change24h: 5.67,
    allocation: 22.7,
  },
  {
    id: 4,
    token: 'ARB',
    name: 'Arbitrum',
    chain: 'Arbitrum',
    balance: 12000,
    value: 20000,
    price: 1.67,
    change24h: -0.5,
    allocation: 15.9,
  },
  {
    id: 5,
    token: 'USDC',
    name: 'USD Coin',
    chain: 'Ethereum',
    balance: 5000,
    value: 5000,
    price: 1.0,
    change24h: 0,
    allocation: 3.9,
  },
  {
    id: 6,
    token: 'USDT',
    name: 'Tether',
    chain: 'Polygon',
    balance: 3000,
    value: 3000,
    price: 1.0,
    change24h: 0,
    allocation: 2.4,
  },
  {
    id: 7,
    token: 'DAI',
    name: 'Dai',
    chain: 'Optimism',
    balance: 2500,
    value: 2500,
    price: 1.0,
    change24h: 0.01,
    allocation: 2.0,
  },
  {
    id: 8,
    token: 'LINK',
    name: 'Chainlink',
    chain: 'Ethereum',
    balance: 150,
    value: 2250,
    price: 15.0,
    change24h: 3.21,
    allocation: 1.8,
  },
]

// Mock chain summary data
const mockChainSummary = [
  { chain: 'Ethereum', value: 52250, percentage: 41.7, tokens: 3 },
  { chain: 'Polygon', value: 35000, percentage: 27.9, tokens: 2 },
  { chain: 'Optimism', value: 30932.56, percentage: 24.7, tokens: 2 },
  { chain: 'Arbitrum', value: 20000, percentage: 15.9, tokens: 1 },
]

export default function HoldingsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'value' | 'change' | 'allocation'>('value')
  const [filterChain, setFilterChain] = useState<string>('all')
  // TODO: Implement portfolio data integration
  // const { isConnected } = useAccount()
  // const { data: portfolio, isLoading } = usePortfolio()

  // Filter and sort holdings
  const filteredHoldings = mockHoldings
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

  const totalValue = mockHoldings.reduce((sum, holding) => sum + holding.value, 0)

  return (
    <div className="px-8 py-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Holdings</h1>
        <p className="text-muted-foreground mt-1">Manage and track your digital assets across all chains</p>
      </div>

      {/* Chain Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {mockChainSummary.map((chain) => (
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
            <option value="Ethereum">Ethereum</option>
            <option value="Polygon">Polygon</option>
            <option value="Optimism">Optimism</option>
            <option value="Arbitrum">Arbitrum</option>
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
                      <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
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
      </Card>

      {/* Summary */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold mb-1">Portfolio Summary</h3>
            <p className="text-sm text-muted-foreground">
              {mockHoldings.length} assets across {mockChainSummary.length} chains
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