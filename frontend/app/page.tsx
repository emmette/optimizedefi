'use client'

import { Card } from '@/components/ui/Card'
import { PortfolioChart } from '@/components/charts/PortfolioChart'
import { PerformanceChart } from '@/components/charts/PerformanceChart'
import { TrendingUp, TrendingDown, DollarSign, Percent, Activity, Shield } from 'lucide-react'

// Mock data for development
const mockPortfolioData = {
  totalValue: 125432.56,
  change24h: 2.34,
  changeValue24h: 2876.43,
  risk: 'Medium',
  diversification: 'Good',
  chains: [
    { name: 'Ethereum', value: 45000, percentage: 35.9 },
    { name: 'Polygon', value: 32000, percentage: 25.5 },
    { name: 'Optimism', value: 28432.56, percentage: 22.7 },
    { name: 'Arbitrum', value: 20000, percentage: 15.9 },
  ],
  performance: [
    { date: '2024-01-01', value: 100000 },
    { date: '2024-01-07', value: 105000 },
    { date: '2024-01-14', value: 110000 },
    { date: '2024-01-21', value: 115000 },
    { date: '2024-01-28', value: 120000 },
    { date: '2024-02-04', value: 125432.56 },
  ]
}

// Mock recent activity data
const mockRecentActivity = [
  {
    id: 1,
    type: 'swap',
    title: 'Swapped ETH → USDC',
    time: '2 hours ago',
    chain: 'Ethereum',
    details: 'Via 1inch Fusion+',
    amounts: [
      { value: '-0.5 ETH', positive: false },
      { value: '+1,578 USDC', positive: true }
    ]
  },
  {
    id: 2,
    type: 'receive',
    title: 'Received MATIC',
    time: '5 hours ago',
    chain: 'Polygon',
    details: 'From wallet',
    amounts: [
      { value: '+2,500 MATIC', positive: true }
    ]
  },
  {
    id: 3,
    type: 'rebalance',
    title: 'Portfolio Rebalanced',
    time: '1 day ago',
    chain: 'Multiple',
    details: 'AI-optimized allocation',
    amounts: [
      { value: '4 transactions', positive: null }
    ]
  },
  {
    id: 4,
    type: 'yield',
    title: 'Yield Harvested',
    time: '2 days ago',
    chain: 'Optimism',
    details: 'From AAVE v3',
    amounts: [
      { value: '+125.43 USDC', positive: true }
    ]
  },
  {
    id: 5,
    type: 'swap',
    title: 'Swapped USDT → DAI',
    time: '3 days ago',
    chain: 'Arbitrum',
    details: 'Via Uniswap V3',
    amounts: [
      { value: '-1,000 USDT', positive: false },
      { value: '+999.8 DAI', positive: true }
    ]
  }
]

export default function OverviewPage() {
  const isPositiveChange = mockPortfolioData.change24h > 0

  return (
    <div className="flex gap-6 h-full">
      {/* Main Content */}
      <div className="flex-1 p-6 space-y-6 overflow-y-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Portfolio Overview</h1>
        <p className="text-muted-foreground mt-1">Track your DeFi portfolio performance across multiple chains</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total Value</p>
              <p className="text-2xl font-bold mt-1">
                ${mockPortfolioData.totalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
              <div className={`flex items-center gap-1 mt-2 text-sm ${isPositiveChange ? 'text-green-500' : 'text-red-500'}`}>
                {isPositiveChange ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                <span>{Math.abs(mockPortfolioData.change24h)}%</span>
                <span className="text-muted-foreground">24h</span>
              </div>
            </div>
            <div className="p-3 bg-primary/10 rounded-lg">
              <DollarSign className="h-6 w-6 text-primary" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">24h Change</p>
              <p className={`text-2xl font-bold mt-1 ${isPositiveChange ? 'text-green-500' : 'text-red-500'}`}>
                {isPositiveChange ? '+' : '-'}${Math.abs(mockPortfolioData.changeValue24h).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
              <p className="text-sm text-muted-foreground mt-2">
                {isPositiveChange ? 'Profit' : 'Loss'} today
              </p>
            </div>
            <div className={`p-3 rounded-lg ${isPositiveChange ? 'bg-green-500/10' : 'bg-red-500/10'}`}>
              <Percent className={`h-6 w-6 ${isPositiveChange ? 'text-green-500' : 'text-red-500'}`} />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Risk Level</p>
              <p className="text-2xl font-bold mt-1">{mockPortfolioData.risk}</p>
              <p className="text-sm text-muted-foreground mt-2">Portfolio risk</p>
            </div>
            <div className="p-3 bg-orange-500/10 rounded-lg">
              <Shield className="h-6 w-6 text-orange-500" />
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Diversification</p>
              <p className="text-2xl font-bold mt-1">{mockPortfolioData.diversification}</p>
              <p className="text-sm text-muted-foreground mt-2">4 chains active</p>
            </div>
            <div className="p-3 bg-blue-500/10 rounded-lg">
              <Activity className="h-6 w-6 text-blue-500" />
            </div>
          </div>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Portfolio Distribution</h3>
          <PortfolioChart data={mockPortfolioData.chains} />
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Performance (30 Days)</h3>
          <PerformanceChart data={mockPortfolioData.performance} />
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="p-4 border border-border rounded-lg hover:bg-accent transition-colors text-left">
            <h4 className="font-medium">Optimize Portfolio</h4>
            <p className="text-sm text-muted-foreground mt-1">AI-powered rebalancing suggestions</p>
          </button>
          <button className="p-4 border border-border rounded-lg hover:bg-accent transition-colors text-left">
            <h4 className="font-medium">Swap Tokens</h4>
            <p className="text-sm text-muted-foreground mt-1">Best rates across DEXs</p>
          </button>
          <button className="p-4 border border-border rounded-lg hover:bg-accent transition-colors text-left">
            <h4 className="font-medium">View Analytics</h4>
            <p className="text-sm text-muted-foreground mt-1">Deep dive into performance</p>
          </button>
        </div>
      </Card>
      </div>

      {/* Recent Activity Panel */}
      <div className="w-80 bg-card border-l border-border flex flex-col h-full">
        <div className="p-6 border-b border-border flex justify-between items-center">
          <h3 className="text-lg font-semibold">Recent Activity</h3>
          <button className="text-sm text-primary hover:underline">View All</button>
        </div>
        <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {mockRecentActivity.map((activity) => (
            <div key={activity.id} className="space-y-2 pb-4 border-b border-border last:border-0">
              <div className="font-medium">{activity.title}</div>
              <div className="text-sm text-muted-foreground">
                {activity.time} • {activity.chain}
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">{activity.details}</span>
                <div className="text-right space-y-1">
                  {activity.amounts.map((amount, idx) => (
                    <div 
                      key={idx} 
                      className={`text-sm font-medium ${
                        amount.positive === true ? 'text-green-500' : 
                        amount.positive === false ? 'text-red-500' : 
                        'text-foreground'
                      }`}
                    >
                      {amount.value}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}