'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { TrendingUp, DollarSign, PieChart, BarChart3, Calendar, Download } from 'lucide-react'

// Mock data for analytics
const mockAnalyticsData = {
  performance: {
    '24h': { value: 2.34, amount: 2876.43 },
    '7d': { value: 5.67, amount: 6712.89 },
    '30d': { value: 12.45, amount: 13897.23 },
    '90d': { value: 28.91, amount: 28456.78 },
    '1y': { value: 145.67, amount: 64321.09 },
  },
  topGainers: [
    { symbol: 'OP', name: 'Optimism', change: 15.67, value: 8000 },
    { symbol: 'ARB', name: 'Arbitrum', change: 12.34, value: 8000 },
    { symbol: 'ETH', name: 'Ethereum', change: 8.91, value: 10468 },
  ],
  topLosers: [
    { symbol: 'MATIC', name: 'Polygon', change: -5.23, value: 10000 },
    { symbol: 'LINK', name: 'Chainlink', change: -3.45, value: 3200 },
    { symbol: 'UNI', name: 'Uniswap', change: -2.11, value: 2100 },
  ],
  chainDistribution: [
    { chain: 'Ethereum', value: 45000, percentage: 35.9, tokens: 15 },
    { chain: 'Polygon', value: 32000, percentage: 25.5, tokens: 12 },
    { chain: 'Optimism', value: 28432.56, percentage: 22.7, tokens: 8 },
    { chain: 'Arbitrum', value: 20000, percentage: 15.9, tokens: 10 },
  ],
  riskMetrics: {
    volatility: 'Medium',
    sharpeRatio: 1.45,
    maxDrawdown: -15.23,
    correlation: 0.67,
  }
}

export default function AnalyticsPage() {
  const [selectedPeriod, setSelectedPeriod] = useState('30d')

  const periods = [
    { id: '24h', label: '24H' },
    { id: '7d', label: '7D' },
    { id: '30d', label: '30D' },
    { id: '90d', label: '90D' },
    { id: '1y', label: '1Y' },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold">Analytics</h1>
          <p className="text-muted-foreground mt-1">Deep insights into your portfolio performance</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors">
          <Download className="h-4 w-4" />
          Export Report
        </button>
      </div>

      {/* Period Selector */}
      <div className="flex gap-2">
        {periods.map((period) => (
          <button
            key={period.id}
            onClick={() => setSelectedPeriod(period.id)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              selectedPeriod === period.id
                ? 'bg-primary text-primary-foreground'
                : 'bg-secondary hover:bg-secondary/80'
            }`}
          >
            {period.label}
          </button>
        ))}
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Period Return</p>
              <p className={`text-2xl font-bold mt-1 ${
                mockAnalyticsData.performance[selectedPeriod as keyof typeof mockAnalyticsData.performance].value > 0 
                  ? 'text-green-500' 
                  : 'text-red-500'
              }`}>
                {mockAnalyticsData.performance[selectedPeriod as keyof typeof mockAnalyticsData.performance].value > 0 ? '+' : ''}
                {mockAnalyticsData.performance[selectedPeriod as keyof typeof mockAnalyticsData.performance].value}%
              </p>
            </div>
            <TrendingUp className="h-8 w-8 text-muted-foreground" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Profit/Loss</p>
              <p className={`text-2xl font-bold mt-1 ${
                mockAnalyticsData.performance[selectedPeriod as keyof typeof mockAnalyticsData.performance].amount > 0 
                  ? 'text-green-500' 
                  : 'text-red-500'
              }`}>
                ${mockAnalyticsData.performance[selectedPeriod as keyof typeof mockAnalyticsData.performance].amount.toLocaleString()}
              </p>
            </div>
            <DollarSign className="h-8 w-8 text-muted-foreground" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Volatility</p>
              <p className="text-2xl font-bold mt-1">{mockAnalyticsData.riskMetrics.volatility}</p>
            </div>
            <BarChart3 className="h-8 w-8 text-muted-foreground" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Sharpe Ratio</p>
              <p className="text-2xl font-bold mt-1">{mockAnalyticsData.riskMetrics.sharpeRatio}</p>
            </div>
            <PieChart className="h-8 w-8 text-muted-foreground" />
          </div>
        </Card>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Historical Performance Chart */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Historical Performance</h3>
          <div className="h-64 flex items-center justify-center border-2 border-dashed border-border rounded-lg">
            <p className="text-muted-foreground">D3.js Line Chart Placeholder</p>
          </div>
        </Card>

        {/* Asset Allocation Chart */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Asset Allocation</h3>
          <div className="h-64 flex items-center justify-center border-2 border-dashed border-border rounded-lg">
            <p className="text-muted-foreground">D3.js Donut Chart Placeholder</p>
          </div>
        </Card>
      </div>

      {/* Top Movers */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Gainers */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-green-500">Top Gainers</h3>
          <div className="space-y-3">
            {mockAnalyticsData.topGainers.map((token) => (
              <div key={token.symbol} className="flex items-center justify-between p-3 bg-green-500/10 rounded-lg">
                <div>
                  <p className="font-medium">{token.symbol}</p>
                  <p className="text-sm text-muted-foreground">{token.name}</p>
                </div>
                <div className="text-right">
                  <p className="font-medium text-green-500">+{token.change}%</p>
                  <p className="text-sm text-muted-foreground">${token.value.toLocaleString()}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Top Losers */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4 text-red-500">Top Losers</h3>
          <div className="space-y-3">
            {mockAnalyticsData.topLosers.map((token) => (
              <div key={token.symbol} className="flex items-center justify-between p-3 bg-red-500/10 rounded-lg">
                <div>
                  <p className="font-medium">{token.symbol}</p>
                  <p className="text-sm text-muted-foreground">{token.name}</p>
                </div>
                <div className="text-right">
                  <p className="font-medium text-red-500">{token.change}%</p>
                  <p className="text-sm text-muted-foreground">${token.value.toLocaleString()}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Chain Distribution */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Chain Distribution</h3>
        <div className="space-y-4">
          {mockAnalyticsData.chainDistribution.map((chain) => (
            <div key={chain.chain} className="flex items-center justify-between">
              <div className="flex items-center gap-4 flex-1">
                <div className="w-32">
                  <p className="font-medium">{chain.chain}</p>
                  <p className="text-sm text-muted-foreground">{chain.tokens} tokens</p>
                </div>
                <div className="flex-1">
                  <div className="h-2 bg-secondary rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-primary transition-all duration-500"
                      style={{ width: `${chain.percentage}%` }}
                    />
                  </div>
                </div>
              </div>
              <div className="text-right ml-4">
                <p className="font-medium">${chain.value.toLocaleString()}</p>
                <p className="text-sm text-muted-foreground">{chain.percentage}%</p>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Risk Metrics */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Risk Analysis</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <p className="text-sm text-muted-foreground">Volatility</p>
            <p className="text-xl font-bold mt-1">{mockAnalyticsData.riskMetrics.volatility}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Sharpe Ratio</p>
            <p className="text-xl font-bold mt-1">{mockAnalyticsData.riskMetrics.sharpeRatio}</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Max Drawdown</p>
            <p className="text-xl font-bold mt-1 text-red-500">{mockAnalyticsData.riskMetrics.maxDrawdown}%</p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Correlation</p>
            <p className="text-xl font-bold mt-1">{mockAnalyticsData.riskMetrics.correlation}</p>
          </div>
        </div>
      </Card>
    </div>
  )
}