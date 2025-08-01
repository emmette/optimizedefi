'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/card'
import { D3PerformanceChart } from '@/components/charts/D3PerformanceChart'
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  PieChart,
  BarChart3,
  Calendar,
  Download,
  AlertCircle
} from 'lucide-react'
import { usePortfolio } from '@/hooks/usePortfolio'
import { useAccount } from 'wagmi'
import { CardSkeleton, ChartSkeleton } from '@/components/ui/LoadingSkeleton'

// Mock performance data
const mockPerformanceData = {
  '1D': [
    { date: '00:00', value: 123000 },
    { date: '04:00', value: 122500 },
    { date: '08:00', value: 124000 },
    { date: '12:00', value: 125000 },
    { date: '16:00', value: 124500 },
    { date: '20:00', value: 125432.56 },
  ],
  '1W': [
    { date: 'Mon', value: 120000 },
    { date: 'Tue', value: 121500 },
    { date: 'Wed', value: 123000 },
    { date: 'Thu', value: 122000 },
    { date: 'Fri', value: 124000 },
    { date: 'Sat', value: 125000 },
    { date: 'Sun', value: 125432.56 },
  ],
  '1M': [
    { date: 'Week 1', value: 100000 },
    { date: 'Week 2', value: 110000 },
    { date: 'Week 3', value: 115000 },
    { date: 'Week 4', value: 125432.56 },
  ],
  '1Y': [
    { date: 'Jan', value: 80000 },
    { date: 'Feb', value: 85000 },
    { date: 'Mar', value: 90000 },
    { date: 'Apr', value: 95000 },
    { date: 'May', value: 92000 },
    { date: 'Jun', value: 98000 },
    { date: 'Jul', value: 105000 },
    { date: 'Aug', value: 110000 },
    { date: 'Sep', value: 115000 },
    { date: 'Oct', value: 118000 },
    { date: 'Nov', value: 122000 },
    { date: 'Dec', value: 125432.56 },
  ],
}

// Mock transaction metrics
const mockTransactionMetrics = {
  totalTransactions: 342,
  avgTransactionSize: 2450.50,
  gasFeesSpent: 1234.56,
  successRate: 98.5,
  mostActiveChain: 'Ethereum',
  mostTradedToken: 'ETH',
}

// Mock yield metrics
const mockYieldMetrics = {
  totalYieldEarned: 8543.21,
  avgAPY: 12.5,
  activePositions: 7,
  bestPerformer: {
    protocol: 'Aave V3',
    apy: 18.5,
    earned: 3200.50,
  },
}

// Mock gas optimization
const mockGasMetrics = {
  totalSaved: 543.21,
  optimizedTransactions: 45,
  avgSavings: 12.07,
  bestSaving: {
    amount: 89.50,
    chain: 'Ethereum',
    type: 'Batch Swap',
  },
}

type TimeRange = '1D' | '1W' | '1M' | '1Y'

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState<TimeRange>('1M')
  const [activeMetric, setActiveMetric] = useState<'portfolio' | 'transactions' | 'yield' | 'gas'>('portfolio')
  const { isConnected, chain } = useAccount()
  const { data: portfolio, isLoading, error } = usePortfolio()

  // Check if on testnet
  const isTestnet = chain?.id === 11155111 || chain?.testnet === true

  const performanceData = mockPerformanceData[timeRange]
  const currentValue = portfolio?.total_value_usd || performanceData[performanceData.length - 1].value
  const previousValue = performanceData[0].value
  const change = currentValue - previousValue
  const changePercent = previousValue > 0 ? (change / previousValue) * 100 : 0

  if (!isConnected) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-semibold mb-2">Connect Your Wallet</h2>
          <p className="text-muted-foreground">Please connect your wallet to view analytics</p>
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
            You're connected to {chain?.name || 'a testnet'}. Analytics are only available on mainnet networks.
          </p>
          <p className="text-sm text-muted-foreground">
            Please switch to Ethereum, Polygon, Optimism, Arbitrum, Base, Polygon zkEVM, World Chain, or Zora mainnet.
          </p>
        </Card>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="px-8 py-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Analytics</h1>
            <p className="text-muted-foreground mt-1">Track your portfolio performance and metrics</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
        <ChartSkeleton />
      </div>
    )
  }

  if (error || !portfolio) {
    return (
      <div className="flex h-full items-center justify-center">
        <Card className="max-w-md p-8 text-center space-y-4">
          <AlertCircle className="h-12 w-12 text-destructive mx-auto" />
          <h2 className="text-xl font-semibold">Failed to Load Analytics</h2>
          <p className="text-muted-foreground">
            There was an error loading your analytics data. Please try again later.
          </p>
        </Card>
      </div>
    )
  }

  return (
    <div className="px-8 py-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Analytics</h1>
          <p className="text-muted-foreground mt-1">Track your portfolio performance and metrics</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-secondary hover:bg-secondary/80 rounded-lg transition-colors">
          <Download className="h-4 w-4" />
          Export Report
        </button>
      </div>

      {/* Time Range Selector */}
      <div className="flex gap-2">
        {(['1D', '1W', '1M', '1Y'] as TimeRange[]).map((range) => (
          <button
            key={range}
            onClick={() => setTimeRange(range)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              timeRange === range
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary hover:bg-secondary/80'
            }`}
          >
            {range}
          </button>
        ))}
      </div>

      {/* Performance Chart */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h3 className="text-lg font-semibold">Portfolio Performance</h3>
            <div className="flex items-center gap-4 mt-2">
              <p className="text-3xl font-bold">
                ${currentValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </p>
              <div className={`flex items-center gap-1 ${change > 0 ? 'text-green-500' : 'text-red-500'}`}>
                {change > 0 ? <TrendingUp className="h-5 w-5" /> : <TrendingDown className="h-5 w-5" />}
                <span className="font-medium">
                  {change > 0 ? '+' : ''}{changePercent.toFixed(2)}%
                </span>
                <span className="text-muted-foreground">({change > 0 ? '+' : ''}${change.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })})</span>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Calendar className="h-4 w-4" />
            {timeRange === '1D' ? 'Today' : 
             timeRange === '1W' ? 'This Week' : 
             timeRange === '1M' ? 'This Month' : 'This Year'}
          </div>
        </div>
        <div className="h-64">
          <D3PerformanceChart data={performanceData.map(d => ({ 
            date: new Date(d.date), 
            value: d.value 
          }))} height={250} />
        </div>
      </Card>

      {/* Metric Tabs */}
      <div className="flex gap-2 border-b border-border">
        {[
          { id: 'portfolio', label: 'Portfolio', icon: PieChart },
          { id: 'transactions', label: 'Transactions', icon: Activity },
          { id: 'yield', label: 'Yield', icon: TrendingUp },
          { id: 'gas', label: 'Gas Optimization', icon: BarChart3 },
        ].map((tab) => {
          const Icon = tab.icon
          return (
            <button
              key={tab.id}
              onClick={() => setActiveMetric(tab.id as 'portfolio' | 'transactions' | 'yield' | 'gas')}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                activeMetric === tab.id
                  ? 'border-primary text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              <Icon className="h-4 w-4" />
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Metric Content */}
      {activeMetric === 'portfolio' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Find largest and smallest positions */}
          {(() => {
            const allTokens = portfolio.chains.flatMap(chain => 
              chain.tokens.map(token => ({
                ...token,
                chainName: chain.chain_name,
                allocation: (token.balance_usd / portfolio.total_value_usd) * 100
              }))
            ).sort((a, b) => b.balance_usd - a.balance_usd)
            
            const largestToken = allTokens[0]
            const smallestToken = allTokens[allTokens.length - 1]
            
            return (
              <>
                <Card className="p-6">
                  <h3 className="text-sm font-medium text-muted-foreground mb-2">Total Tokens</h3>
                  <p className="text-2xl font-bold">{allTokens.length}</p>
                  <p className="text-sm text-muted-foreground mt-1">Across {portfolio.chains.length} chains</p>
                </Card>
                <Card className="p-6">
                  <h3 className="text-sm font-medium text-muted-foreground mb-2">Diversification Score</h3>
                  <p className="text-2xl font-bold">{portfolio.diversification_score}%</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    {portfolio.diversification_score >= 80 ? 'Excellent' :
                     portfolio.diversification_score >= 60 ? 'Good' :
                     portfolio.diversification_score >= 40 ? 'Fair' : 'Poor'}
                  </p>
                </Card>
                <Card className="p-6">
                  <h3 className="text-sm font-medium text-muted-foreground mb-2">Risk Level</h3>
                  <p className="text-2xl font-bold">{portfolio.risk_assessment?.level || 'Unknown'}</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Score: {portfolio.risk_assessment?.score || 0}/100
                  </p>
                </Card>
                {largestToken && (
                  <Card className="p-6">
                    <h3 className="text-sm font-medium text-muted-foreground mb-2">Largest Position</h3>
                    <p className="text-2xl font-bold">{largestToken.symbol}</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      {largestToken.allocation.toFixed(1)}% of portfolio
                    </p>
                  </Card>
                )}
                {smallestToken && largestToken !== smallestToken && (
                  <Card className="p-6">
                    <h3 className="text-sm font-medium text-muted-foreground mb-2">Smallest Position</h3>
                    <p className="text-2xl font-bold">{smallestToken.symbol}</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      {smallestToken.allocation.toFixed(1)}% of portfolio
                    </p>
                  </Card>
                )}
                <Card className="p-6">
                  <h3 className="text-sm font-medium text-muted-foreground mb-2">Most Active Chain</h3>
                  <p className="text-2xl font-bold">
                    {portfolio.chains.reduce((max, chain) => 
                      chain.total_value_usd > (max?.total_value_usd || 0) ? chain : max
                    , null)?.chain_name || 'N/A'}
                  </p>
                  <p className="text-sm text-muted-foreground mt-1">By value</p>
                </Card>
              </>
            )
          })()}
        </div>
      )}

      {activeMetric === 'transactions' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card className="p-6 col-span-full">
            <div className="text-center py-8">
              <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Transaction Analytics Coming Soon</h3>
              <p className="text-muted-foreground">
                Historical transaction data and analytics will be available in a future update.
              </p>
            </div>
          </Card>
        </div>
      )}

      {activeMetric === 'yield' && (
        <div className="space-y-6">
          <Card className="p-6">
            <div className="text-center py-8">
              <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Yield Analytics Coming Soon</h3>
              <p className="text-muted-foreground">
                Yield tracking and optimization analytics will be available in a future update.
              </p>
            </div>
          </Card>
        </div>
      )}

      {activeMetric === 'gas' && (
        <div className="space-y-6">
          <Card className="p-6">
            <div className="text-center py-8">
              <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Gas Analytics Coming Soon</h3>
              <p className="text-muted-foreground">
                Gas optimization tracking and analytics will be available in a future update.
              </p>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}