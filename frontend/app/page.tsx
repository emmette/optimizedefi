'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { D3PortfolioDonutChart } from '@/components/charts/D3PortfolioDonutChart'
import { D3PerformanceChart } from '@/components/charts/D3PerformanceChart'
import { D3ChainDistributionChart } from '@/components/charts/D3ChainDistributionChart'
import { TrendingUp, TrendingDown, DollarSign, Percent, Activity, Shield, ChevronRight } from 'lucide-react'
import { usePortfolio } from '@/hooks/usePortfolio'
import { useAccount } from 'wagmi'
import { CardSkeleton, ChartSkeleton } from '@/components/ui/LoadingSkeleton'

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
  const [isActivityCollapsed, setIsActivityCollapsed] = useState(false)
  const { isConnected, chain } = useAccount()
  const { data: portfolio, isLoading } = usePortfolio()
  
  // Check if on testnet
  const isTestnet = chain?.id === 11155111 || chain?.testnet === true
  
  // Use portfolio data if available, otherwise fall back to mock data
  const portfolioData = portfolio ? {
    totalValue: portfolio.total_value_usd,
    change24h: 2.34, // TODO: Calculate from historical data
    changeValue24h: portfolio.total_value_usd * 0.0234, // TODO: Calculate from historical data
    risk: getRiskLevel(portfolio.risk_assessment),
    diversification: getDiversificationLevel(portfolio.diversification_score),
    chains: portfolio.chains.map(chain => ({
      name: chain.chain_name,
      value: chain.total_value_usd,
      percentage: (chain.total_value_usd / portfolio.total_value_usd) * 100
    })),
    performance: mockPortfolioData.performance // TODO: Fetch from history endpoint
  } : mockPortfolioData
  
  // Helper functions to convert metrics to display strings
  function getRiskLevel(riskAssessment: any): string {
    const score = riskAssessment?.score || 50
    if (score < 30) return 'Low'
    if (score < 70) return 'Medium'
    return 'High'
  }
  
  function getDiversificationLevel(score: number): string {
    if (score >= 80) return 'Excellent'
    if (score >= 60) return 'Good'
    if (score >= 40) return 'Fair'
    return 'Poor'
  }
  
  const isPositiveChange = portfolioData.change24h > 0

  if (!isConnected) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-semibold mb-2">Connect Your Wallet</h2>
          <p className="text-muted-foreground">Please connect your wallet to view your portfolio</p>
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
            You're connected to {chain?.name || 'a testnet'}. Portfolio tracking is only available on mainnet networks.
          </p>
          <p className="text-sm text-muted-foreground">
            Please switch to Ethereum, Polygon, Optimism, or Arbitrum mainnet to view your portfolio.
          </p>
        </Card>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="flex h-full">
        <div className="flex-1 px-4 sm:px-6 lg:px-8 py-4 sm:py-6 space-y-4 sm:space-y-6 overflow-y-auto">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
            {[...Array(4)].map((_, i) => (
              <CardSkeleton key={i} />
            ))}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 sm:gap-6">
            <div className="lg:col-span-3">
              <ChartSkeleton />
            </div>
            <div className="lg:col-span-2">
              <ChartSkeleton />
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-full">
      {/* Main Content */}
      <div className="flex-1 px-4 sm:px-6 lg:px-8 py-4 sm:py-6 space-y-4 sm:space-y-6 overflow-y-auto">

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <Card className="p-4 sm:p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total Value</p>
              <p className="text-2xl font-bold mt-1">
                ${portfolioData.totalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
              <div className={`flex items-center gap-1 mt-2 text-sm ${isPositiveChange ? 'text-green-500' : 'text-red-500'}`}>
                {isPositiveChange ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                <span>{Math.abs(portfolioData.change24h)}%</span>
                <span className="text-muted-foreground">24h</span>
              </div>
            </div>
            <div className="p-3 bg-primary/10 rounded-lg">
              <DollarSign className="h-6 w-6 text-primary" />
            </div>
          </div>
        </Card>

        <Card className="p-4 sm:p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">24h Change</p>
              <p className={`text-2xl font-bold mt-1 ${isPositiveChange ? 'text-green-500' : 'text-red-500'}`}>
                {isPositiveChange ? '+' : '-'}${Math.abs(portfolioData.changeValue24h).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
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

        <Card className="p-4 sm:p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Risk Level</p>
              <p className="text-2xl font-bold mt-1">{portfolioData.risk}</p>
              <p className="text-sm text-muted-foreground mt-2">Portfolio risk</p>
            </div>
            <div className="p-3 bg-orange-500/10 rounded-lg">
              <Shield className="h-6 w-6 text-orange-500" />
            </div>
          </div>
        </Card>

        <Card className="p-4 sm:p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Diversification</p>
              <p className="text-2xl font-bold mt-1">{portfolioData.diversification}</p>
              <p className="text-sm text-muted-foreground mt-2">4 chains active</p>
            </div>
            <div className="p-3 bg-blue-500/10 rounded-lg">
              <Activity className="h-6 w-6 text-blue-500" />
            </div>
          </div>
        </Card>
      </div>

      {/* First Row: Portfolio Performance and Top Opportunities */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-3">
          <D3PerformanceChart data={mockPortfolioData.performance.map(d => ({ 
            date: new Date(d.date), 
            value: d.value 
          }))} />
        </div>

        <Card className="p-4 sm:p-6 lg:col-span-2">
          <h3 className="text-lg font-semibold mb-4">Top Opportunities</h3>
          <div className="space-y-4">
            <div className="p-4 bg-background rounded-lg border border-border">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-medium">Rebalance to Conservative</h4>
                  <p className="text-sm text-muted-foreground">Lower risk, stable returns</p>
                </div>
                <span className="text-green-500 text-sm font-medium">+12% APY</span>
              </div>
              <button className="text-sm text-primary hover:underline">View Details →</button>
            </div>
            <div className="p-4 bg-background rounded-lg border border-border">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-medium">Yield Farming on Polygon</h4>
                  <p className="text-sm text-muted-foreground">High yield opportunity</p>
                </div>
                <span className="text-green-500 text-sm font-medium">+25% APY</span>
              </div>
              <button className="text-sm text-primary hover:underline">View Details →</button>
            </div>
            <div className="p-4 bg-background rounded-lg border border-border">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <h4 className="font-medium">Optimize Gas Costs</h4>
                  <p className="text-sm text-muted-foreground">Save on transaction fees</p>
                </div>
                <span className="text-green-500 text-sm font-medium">Save $234</span>
              </div>
              <button className="text-sm text-primary hover:underline">View Details →</button>
            </div>
          </div>
        </Card>
      </div>

      {/* Second Row: Asset Allocation and Chain Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-4 sm:gap-6">
        <div className="lg:col-span-3">
          <D3PortfolioDonutChart 
            tokens={portfolio ? portfolio.chains.flatMap(chain => chain.tokens) : []} 
            totalValue={portfolioData.totalValue} 
          />
        </div>

        <div className="lg:col-span-2">
          <D3ChainDistributionChart 
            data={portfolio ? portfolio.chains.map(chain => ({
              chainId: chain.chain_id,
              name: chain.chain_name,
              value: chain.total_value_usd,
              percentage: (chain.total_value_usd / portfolio.total_value_usd) * 100
            })) : portfolioData.chains.map((chain, idx) => ({
              chainId: [1, 137, 10, 42161][idx] || 1,
              name: chain.name,
              value: chain.value,
              percentage: chain.percentage
            }))} 
          />
        </div>
      </div>

      </div>

      {/* Recent Activity Panel - Hidden on mobile */}
      <div className={`hidden lg:flex relative bg-card border-l border-border flex-col h-full transition-all duration-300 ${isActivityCollapsed ? 'w-0' : 'w-80'}`}>
        {/* Collapse Toggle Button */}
        <button
          onClick={() => setIsActivityCollapsed(!isActivityCollapsed)}
          className="absolute -left-4 top-6 p-1 hover:bg-accent rounded-md transition-colors z-10"
        >
          <ChevronRight className={`h-5 w-5 transition-transform ${isActivityCollapsed ? 'rotate-180' : ''}`} />
        </button>
        
        <div className={`${isActivityCollapsed ? 'hidden' : ''}`}>
          <div className="p-6 border-b border-border flex justify-between items-center">
            <h3 className="text-lg font-semibold">Recent Activity</h3>
            <button className="text-sm text-primary hover:underline">View All</button>
          </div>
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
          {mockRecentActivity.map((activity) => (
            <div key={activity.id} className="p-3 bg-background rounded-lg space-y-2">
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
    </div>
  )
}