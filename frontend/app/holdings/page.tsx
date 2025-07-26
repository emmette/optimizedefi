'use client'

import { useState } from 'react'
import Image from 'next/image'
import { Card } from '@/components/ui/Card'
import { Search, ChevronDown, ExternalLink, Copy } from 'lucide-react'

// Mock data for token holdings
const mockHoldings = [
  {
    id: '1',
    symbol: 'ETH',
    name: 'Ethereum',
    balance: '5.234',
    value: 10468.0,
    price: 2000.0,
    change24h: 2.34,
    chain: 'Ethereum',
    chainId: 1,
    address: '0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE',
    logo: 'https://tokens.1inch.io/0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee.png'
  },
  {
    id: '2',
    symbol: 'USDC',
    name: 'USD Coin',
    balance: '15000',
    value: 15000.0,
    price: 1.0,
    change24h: 0.01,
    chain: 'Ethereum',
    chainId: 1,
    address: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
    logo: 'https://tokens.1inch.io/0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48.png'
  },
  {
    id: '3',
    symbol: 'MATIC',
    name: 'Polygon',
    balance: '12500',
    value: 10000.0,
    price: 0.8,
    change24h: -1.23,
    chain: 'Polygon',
    chainId: 137,
    address: '0x0000000000000000000000000000000000001010',
    logo: 'https://tokens.1inch.io/0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0.png'
  },
  {
    id: '4',
    symbol: 'OP',
    name: 'Optimism',
    balance: '4000',
    value: 8000.0,
    price: 2.0,
    change24h: 5.67,
    chain: 'Optimism',
    chainId: 10,
    address: '0x4200000000000000000000000000000000000042',
    logo: 'https://tokens.1inch.io/0x4200000000000000000000000000000000000042.png'
  },
  {
    id: '5',
    symbol: 'ARB',
    name: 'Arbitrum',
    balance: '8000',
    value: 8000.0,
    price: 1.0,
    change24h: 3.45,
    chain: 'Arbitrum',
    chainId: 42161,
    address: '0x912CE59144191C1204E64559FE8253a0e49E6548',
    logo: 'https://tokens.1inch.io/0x912ce59144191c1204e64559fe8253a0e49e6548.png'
  }
]

const chains = [
  { id: 'all', name: 'All Chains', count: mockHoldings.length },
  { id: '1', name: 'Ethereum', count: 2 },
  { id: '137', name: 'Polygon', count: 1 },
  { id: '10', name: 'Optimism', count: 1 },
  { id: '42161', name: 'Arbitrum', count: 1 },
]

export default function HoldingsPage() {
  const [selectedChain, setSelectedChain] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState<'value' | 'change' | 'name'>('value')

  // Filter and sort holdings
  const filteredHoldings = mockHoldings
    .filter(token => {
      const matchesChain = selectedChain === 'all' || token.chainId.toString() === selectedChain
      const matchesSearch = 
        token.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
        token.name.toLowerCase().includes(searchQuery.toLowerCase())
      return matchesChain && matchesSearch
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'value':
          return b.value - a.value
        case 'change':
          return b.change24h - a.change24h
        case 'name':
          return a.name.localeCompare(b.name)
        default:
          return 0
      }
    })

  const totalValue = filteredHoldings.reduce((sum, token) => sum + token.value, 0)

  const copyAddress = (address: string) => {
    navigator.clipboard.writeText(address)
    // In production, show a toast notification
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Holdings</h1>
        <p className="text-muted-foreground mt-1">View and manage your token holdings across all chains</p>
      </div>

      {/* Chain Filter Tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {chains.map((chain) => (
          <button
            key={chain.id}
            onClick={() => setSelectedChain(chain.id)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors whitespace-nowrap ${
              selectedChain === chain.id
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary hover:bg-secondary/80'
            }`}
          >
            {chain.name} ({chain.count})
          </button>
        ))}
      </div>

      {/* Search and Sort */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search tokens..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-background border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
        <div className="relative">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'value' | 'change' | 'name')}
            className="appearance-none px-4 py-2 pr-10 bg-background border border-input rounded-lg focus:outline-none focus:ring-2 focus:ring-ring cursor-pointer"
          >
            <option value="value">Sort by Value</option>
            <option value="change">Sort by 24h Change</option>
            <option value="name">Sort by Name</option>
          </select>
          <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
        </div>
      </div>

      {/* Summary Card */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Total Portfolio Value</p>
            <p className="text-3xl font-bold mt-1">
              ${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm text-muted-foreground">{filteredHoldings.length} Tokens</p>
            <p className="text-sm text-muted-foreground mt-1">
              {selectedChain === 'all' ? 'All Chains' : chains.find(c => c.id === selectedChain)?.name}
            </p>
          </div>
        </div>
      </Card>

      {/* Token List */}
      <Card className="overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left p-4 font-medium text-muted-foreground">Token</th>
                <th className="text-right p-4 font-medium text-muted-foreground">Balance</th>
                <th className="text-right p-4 font-medium text-muted-foreground">Price</th>
                <th className="text-right p-4 font-medium text-muted-foreground">Value</th>
                <th className="text-right p-4 font-medium text-muted-foreground">24h Change</th>
                <th className="text-right p-4 font-medium text-muted-foreground">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredHoldings.map((token) => (
                <tr key={token.id} className="border-b border-border hover:bg-accent/50 transition-colors">
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <Image
                        src={token.logo}
                        alt={token.symbol}
                        width={32}
                        height={32}
                        className="rounded-full"
                      />
                      <div>
                        <p className="font-medium">{token.symbol}</p>
                        <p className="text-sm text-muted-foreground">{token.name}</p>
                      </div>
                    </div>
                  </td>
                  <td className="p-4 text-right">
                    <p className="font-medium">{parseFloat(token.balance).toLocaleString()}</p>
                    <p className="text-sm text-muted-foreground">{token.chain}</p>
                  </td>
                  <td className="p-4 text-right">
                    <p className="font-medium">${token.price.toLocaleString()}</p>
                  </td>
                  <td className="p-4 text-right">
                    <p className="font-medium">
                      ${token.value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </p>
                  </td>
                  <td className="p-4 text-right">
                    <p className={`font-medium ${token.change24h > 0 ? 'text-green-500' : 'text-red-500'}`}>
                      {token.change24h > 0 ? '+' : ''}{token.change24h.toFixed(2)}%
                    </p>
                  </td>
                  <td className="p-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => copyAddress(token.address)}
                        className="p-1.5 hover:bg-accent rounded-md transition-colors"
                        title="Copy address"
                      >
                        <Copy className="h-4 w-4" />
                      </button>
                      <a
                        href={`https://etherscan.io/token/${token.address}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-1.5 hover:bg-accent rounded-md transition-colors"
                        title="View on explorer"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}