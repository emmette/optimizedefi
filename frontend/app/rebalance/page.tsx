'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { 
  Zap, 
  Shield, 
  TrendingUp, 
  AlertTriangle,
  CheckCircle,
  ChevronRight,
  Info,
  Settings,
  RefreshCw,
  DollarSign,
  ArrowRight
} from 'lucide-react'

// Mock portfolio allocations
const mockCurrentAllocation = [
  { token: 'ETH', percentage: 35.9, value: 45000, target: 30 },
  { token: 'MATIC', percentage: 25.5, value: 32000, target: 20 },
  { token: 'OP', percentage: 22.7, value: 28432.56, target: 25 },
  { token: 'ARB', percentage: 15.9, value: 20000, target: 15 },
  { token: 'USDC', percentage: 3.9, value: 5000, target: 5 },
  { token: 'USDT', percentage: 2.4, value: 3000, target: 3 },
  { token: 'DAI', percentage: 2.0, value: 2500, target: 2 },
]

// Mock strategies
const mockStrategies = [
  {
    id: 'conservative',
    name: 'Conservative',
    description: 'Lower risk, stable returns',
    risk: 'Low',
    expectedAPY: 8.5,
    allocation: {
      stablecoins: 40,
      bluechips: 50,
      altcoins: 10,
    },
  },
  {
    id: 'balanced',
    name: 'Balanced',
    description: 'Moderate risk and returns',
    risk: 'Medium',
    expectedAPY: 12.5,
    allocation: {
      stablecoins: 25,
      bluechips: 50,
      altcoins: 25,
    },
  },
  {
    id: 'aggressive',
    name: 'Aggressive',
    description: 'Higher risk, higher returns',
    risk: 'High',
    expectedAPY: 18.5,
    allocation: {
      stablecoins: 10,
      bluechips: 40,
      altcoins: 50,
    },
  },
  {
    id: 'custom',
    name: 'Custom',
    description: 'Create your own allocation',
    risk: 'Variable',
    expectedAPY: 0,
    allocation: {
      stablecoins: 0,
      bluechips: 0,
      altcoins: 0,
    },
  },
]

// Mock rebalance actions
const mockRebalanceActions = [
  { from: 'ETH', to: 'USDC', amount: 1500, reason: 'Reduce volatility' },
  { from: 'MATIC', to: 'OP', amount: 2000, reason: 'Better growth potential' },
  { from: 'ARB', to: 'DAI', amount: 1000, reason: 'Increase stable allocation' },
]

export default function RebalancePage() {
  const [selectedStrategy, setSelectedStrategy] = useState(mockStrategies[1])
  const [showAdvanced, setShowAdvanced] = useState(false)

  const totalValue = mockCurrentAllocation.reduce((sum, item) => sum + item.value, 0)

  return (
    <div className="px-8 py-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold">Rebalance</h1>
        <p className="text-muted-foreground mt-1">Optimize your portfolio allocation with AI-powered strategies</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Current Allocation */}
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Current Allocation</h3>
          <div className="space-y-3">
            {mockCurrentAllocation.map((item) => (
              <div key={item.token}>
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium">{item.token}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-muted-foreground">
                      {item.percentage.toFixed(1)}%
                    </span>
                    {Math.abs(item.percentage - item.target) > 2 && (
                      <AlertTriangle className="h-3 w-3 text-yellow-500" />
                    )}
                  </div>
                </div>
                <div className="w-full bg-background rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all duration-300"
                    style={{ width: `${item.percentage}%` }}
                  />
                </div>
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs text-muted-foreground">
                    ${item.value.toLocaleString()}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    Target: {item.target}%
                  </span>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 pt-6 border-t border-border">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Total Value</span>
              <span className="font-semibold">
                ${totalValue.toLocaleString()}
              </span>
            </div>
          </div>
        </Card>

        {/* Strategy Selection */}
        <Card className="p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Rebalancing Strategy</h3>
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <Settings className="h-4 w-4" />
              Advanced
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            {mockStrategies.map((strategy) => (
              <button
                key={strategy.id}
                onClick={() => setSelectedStrategy(strategy)}
                className={`p-4 rounded-lg border transition-all text-left ${
                  selectedStrategy.id === strategy.id
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-primary/50'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h4 className="font-medium">{strategy.name}</h4>
                    <p className="text-sm text-muted-foreground">{strategy.description}</p>
                  </div>
                  {selectedStrategy.id === strategy.id && (
                    <CheckCircle className="h-5 w-5 text-primary" />
                  )}
                </div>
                <div className="flex items-center gap-4 mt-3">
                  <div className="flex items-center gap-1">
                    <Shield className={`h-4 w-4 ${
                      strategy.risk === 'Low' ? 'text-green-500' :
                      strategy.risk === 'Medium' ? 'text-yellow-500' :
                      strategy.risk === 'High' ? 'text-red-500' : 'text-muted-foreground'
                    }`} />
                    <span className="text-sm">{strategy.risk}</span>
                  </div>
                  {strategy.expectedAPY > 0 && (
                    <div className="flex items-center gap-1">
                      <TrendingUp className="h-4 w-4 text-green-500" />
                      <span className="text-sm">{strategy.expectedAPY}% APY</span>
                    </div>
                  )}
                </div>
              </button>
            ))}
          </div>

          {/* Strategy Details */}
          {selectedStrategy.id !== 'custom' && (
            <Card className="p-4 bg-background">
              <h4 className="font-medium mb-3">Allocation Breakdown</h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm">Stablecoins</span>
                  <span className="text-sm font-medium">{selectedStrategy.allocation.stablecoins}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Blue Chips (ETH, BTC)</span>
                  <span className="text-sm font-medium">{selectedStrategy.allocation.bluechips}%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm">Altcoins</span>
                  <span className="text-sm font-medium">{selectedStrategy.allocation.altcoins}%</span>
                </div>
              </div>
            </Card>
          )}

          {/* Advanced Settings */}
          {showAdvanced && (
            <Card className="mt-4 p-4 bg-background">
              <h4 className="font-medium mb-3">Advanced Settings</h4>
              <div className="space-y-3">
                <div>
                  <label className="text-sm text-muted-foreground">Max Slippage</label>
                  <input
                    type="text"
                    defaultValue="1.0"
                    className="w-full mt-1 px-3 py-2 bg-background border border-input rounded-md text-sm"
                    placeholder="1.0%"
                  />
                </div>
                <div>
                  <label className="text-sm text-muted-foreground">Rebalance Threshold</label>
                  <input
                    type="text"
                    defaultValue="5.0"
                    className="w-full mt-1 px-3 py-2 bg-background border border-input rounded-md text-sm"
                    placeholder="5.0%"
                  />
                </div>
              </div>
            </Card>
          )}
        </Card>
      </div>

      {/* Rebalance Actions */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Rebalance Actions</h3>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <RefreshCw className="h-4 w-4" />
            <span>3 transactions required</span>
          </div>
        </div>

        <div className="space-y-3 mb-6">
          {mockRebalanceActions.map((action, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-background rounded-lg">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-primary/10 rounded-lg">
                  <ArrowRight className="h-4 w-4 text-primary" />
                </div>
                <div>
                  <p className="font-medium">
                    Swap {action.from} → {action.to}
                  </p>
                  <p className="text-sm text-muted-foreground">{action.reason}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="font-medium">${action.amount.toLocaleString()}</p>
                <p className="text-sm text-muted-foreground">~{(action.amount / totalValue * 100).toFixed(1)}%</p>
              </div>
            </div>
          ))}
        </div>

        {/* Cost Summary */}
        <Card className="p-4 bg-background mb-6">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Estimated Gas Fees</span>
              <span className="font-medium">~$45.67</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Price Impact</span>
              <span className="font-medium text-green-500">{'<0.1%'}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Time to Complete</span>
              <span className="font-medium">~2 minutes</span>
            </div>
          </div>
        </Card>

        {/* Action Buttons */}
        <div className="flex gap-3">
          <button className="flex-1 py-3 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors flex items-center justify-center gap-2">
            <Zap className="h-5 w-5" />
            Execute Rebalance
          </button>
          <button className="px-6 py-3 bg-secondary hover:bg-secondary/80 rounded-lg font-medium transition-colors">
            Preview
          </button>
        </div>
      </Card>

      {/* Info Card */}
      <Card className="p-4 bg-blue-500/10 border-blue-500/20">
        <div className="flex gap-3">
          <Info className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="text-sm font-medium">AI-Powered Optimization</p>
            <p className="text-sm text-muted-foreground">
              Our AI analyzes market conditions, gas prices, and liquidity to find the most efficient rebalancing path with minimal slippage.
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}