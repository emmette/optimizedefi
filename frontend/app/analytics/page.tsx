'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { PerformanceChart } from '@/components/charts/PerformanceChart'
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Activity, 
  PieChart,
  BarChart3,
  Calendar,
  Download
} from 'lucide-react'

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

  const performanceData = mockPerformanceData[timeRange]
  const currentValue = performanceData[performanceData.length - 1].value
  const previousValue = performanceData[0].value
  const change = currentValue - previousValue
  const changePercent = (change / previousValue) * 100

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
          <PerformanceChart data={performanceData} />
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
              onClick={() => setActiveMetric(tab.id as any)}
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
          <Card className="p-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Best Performer</h3>
            <p className="text-2xl font-bold">ETH</p>
            <p className="text-sm text-green-500 mt-1">+12.5% this month</p>
          </Card>
          <Card className="p-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Worst Performer</h3>
            <p className="text-2xl font-bold">MATIC</p>
            <p className="text-sm text-red-500 mt-1">-3.2% this month</p>
          </Card>
          <Card className="p-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Most Volatile</h3>
            <p className="text-2xl font-bold">OP</p>
            <p className="text-sm text-muted-foreground mt-1">±15.3% volatility</p>
          </Card>
          <Card className="p-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Largest Position</h3>
            <p className="text-2xl font-bold">ETH</p>
            <p className="text-sm text-muted-foreground mt-1">35.9% of portfolio</p>
          </Card>
          <Card className="p-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Smallest Position</h3>
            <p className="text-2xl font-bold">LINK</p>
            <p className="text-sm text-muted-foreground mt-1">1.8% of portfolio</p>
          </Card>
          <Card className="p-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Risk Score</h3>
            <p className="text-2xl font-bold">Medium</p>
            <p className="text-sm text-orange-500 mt-1">Score: 6.5/10</p>
          </Card>
        </div>
      )}

      {activeMetric === 'transactions' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card className="p-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Total Transactions</h3>
            <p className="text-2xl font-bold">{mockTransactionMetrics.totalTransactions}</p>
            <p className="text-sm text-muted-foreground mt-1">This month</p>
          </Card>
          <Card className="p-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Average Size</h3>
            <p className="text-2xl font-bold">${mockTransactionMetrics.avgTransactionSize.toLocaleString()}</p>
            <p className="text-sm text-muted-foreground mt-1">Per transaction</p>
          </Card>
          <Card className="p-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Gas Fees Spent</h3>
            <p className="text-2xl font-bold">${mockTransactionMetrics.gasFeesSpent.toLocaleString()}</p>
            <p className="text-sm text-muted-foreground mt-1">Total fees</p>
          </Card>
          <Card className="p-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Success Rate</h3>
            <p className="text-2xl font-bold">{mockTransactionMetrics.successRate}%</p>
            <p className="text-sm text-green-500 mt-1">Excellent</p>
          </Card>
          <Card className="p-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Most Active Chain</h3>
            <p className="text-2xl font-bold">{mockTransactionMetrics.mostActiveChain}</p>
            <p className="text-sm text-muted-foreground mt-1">165 transactions</p>
          </Card>
          <Card className="p-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-2">Most Traded</h3>
            <p className="text-2xl font-bold">{mockTransactionMetrics.mostTradedToken}</p>
            <p className="text-sm text-muted-foreground mt-1">89 trades</p>
          </Card>
        </div>
      )}

      {activeMetric === 'yield' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="p-6">
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Total Yield Earned</h3>
              <p className="text-2xl font-bold">${mockYieldMetrics.totalYieldEarned.toLocaleString()}</p>
              <p className="text-sm text-green-500 mt-1">All time</p>
            </Card>
            <Card className="p-6">
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Average APY</h3>
              <p className="text-2xl font-bold">{mockYieldMetrics.avgAPY}%</p>
              <p className="text-sm text-muted-foreground mt-1">Across positions</p>
            </Card>
            <Card className="p-6">
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Active Positions</h3>
              <p className="text-2xl font-bold">{mockYieldMetrics.activePositions}</p>
              <p className="text-sm text-muted-foreground mt-1">Earning yield</p>
            </Card>
            <Card className="p-6">
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Best Performer</h3>
              <p className="text-2xl font-bold">{mockYieldMetrics.bestPerformer.protocol}</p>
              <p className="text-sm text-green-500 mt-1">{mockYieldMetrics.bestPerformer.apy}% APY</p>
            </Card>
          </div>
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Top Yield Sources</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-background rounded-lg">
                <div>
                  <p className="font-medium">Aave V3 - ETH</p>
                  <p className="text-sm text-muted-foreground">Ethereum</p>
                </div>
                <div className="text-right">
                  <p className="font-medium text-green-500">18.5% APY</p>
                  <p className="text-sm text-muted-foreground">+$3,200.50</p>
                </div>
              </div>
              <div className="flex items-center justify-between p-3 bg-background rounded-lg">
                <div>
                  <p className="font-medium">Compound - USDC</p>
                  <p className="text-sm text-muted-foreground">Polygon</p>
                </div>
                <div className="text-right">
                  <p className="font-medium text-green-500">12.3% APY</p>
                  <p className="text-sm text-muted-foreground">+$2,100.35</p>
                </div>
              </div>
              <div className="flex items-center justify-between p-3 bg-background rounded-lg">
                <div>
                  <p className="font-medium">Yearn - DAI</p>
                  <p className="text-sm text-muted-foreground">Optimism</p>
                </div>
                <div className="text-right">
                  <p className="font-medium text-green-500">9.8% APY</p>
                  <p className="text-sm text-muted-foreground">+$1,542.86</p>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {activeMetric === 'gas' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card className="p-6">
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Total Saved</h3>
              <p className="text-2xl font-bold">${mockGasMetrics.totalSaved.toLocaleString()}</p>
              <p className="text-sm text-green-500 mt-1">This month</p>
            </Card>
            <Card className="p-6">
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Optimized Txns</h3>
              <p className="text-2xl font-bold">{mockGasMetrics.optimizedTransactions}</p>
              <p className="text-sm text-muted-foreground mt-1">Transactions</p>
            </Card>
            <Card className="p-6">
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Avg Savings</h3>
              <p className="text-2xl font-bold">${mockGasMetrics.avgSavings.toFixed(2)}</p>
              <p className="text-sm text-muted-foreground mt-1">Per transaction</p>
            </Card>
            <Card className="p-6">
              <h3 className="text-sm font-medium text-muted-foreground mb-2">Best Saving</h3>
              <p className="text-2xl font-bold">${mockGasMetrics.bestSaving.amount.toFixed(2)}</p>
              <p className="text-sm text-muted-foreground mt-1">{mockGasMetrics.bestSaving.type}</p>
            </Card>
          </div>
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Optimization Breakdown</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Batch Transactions</span>
                </div>
                <span className="font-medium">$234.50 saved</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                  <span>Optimal Routing</span>
                </div>
                <span className="font-medium">$189.32 saved</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                  <span>Gas Price Timing</span>
                </div>
                <span className="font-medium">$89.21 saved</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                  <span>Contract Optimization</span>
                </div>
                <span className="font-medium">$30.18 saved</span>
              </div>
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}