'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { 
  TrendingUp, 
  Shield, 
  Zap, 
  AlertTriangle, 
  Info, 
  Play,
  RefreshCw,
  Settings,
  ChevronRight
} from 'lucide-react'

// Mock data for rebalancing
const mockCurrentAllocation = [
  { symbol: 'ETH', percentage: 35.9, value: 45000, targetPercentage: 40 },
  { symbol: 'USDC', percentage: 25.5, value: 32000, targetPercentage: 20 },
  { symbol: 'MATIC', percentage: 22.7, value: 28432.56, targetPercentage: 20 },
  { symbol: 'OP', percentage: 15.9, value: 20000, targetPercentage: 10 },
  { symbol: 'ARB', percentage: 0, value: 0, targetPercentage: 10 },
]

const mockStrategies = [
  {
    id: 'conservative',
    name: 'Conservative',
    description: 'Lower risk, stable returns',
    icon: Shield,
    allocation: {
      'Stablecoins': 40,
      'Blue Chips': 40,
      'Mid Cap': 15,
      'Small Cap': 5,
    },
    metrics: {
      expectedReturn: '8-12%',
      risk: 'Low',
      sharpeRatio: 1.2,
    }
  },
  {
    id: 'balanced',
    name: 'Balanced',
    description: 'Moderate risk and returns',
    icon: TrendingUp,
    allocation: {
      'Stablecoins': 20,
      'Blue Chips': 40,
      'Mid Cap': 30,
      'Small Cap': 10,
    },
    metrics: {
      expectedReturn: '15-25%',
      risk: 'Medium',
      sharpeRatio: 1.5,
    }
  },
  {
    id: 'aggressive',
    name: 'Aggressive',
    description: 'Higher risk, higher returns',
    icon: Zap,
    allocation: {
      'Stablecoins': 10,
      'Blue Chips': 30,
      'Mid Cap': 40,
      'Small Cap': 20,
    },
    metrics: {
      expectedReturn: '25-40%',
      risk: 'High',
      sharpeRatio: 1.8,
    }
  },
]

const mockRebalancingSteps = [
  { action: 'Sell', from: 'USDC', amount: '2,000', to: 'USD', status: 'pending' },
  { action: 'Sell', from: 'MATIC', amount: '1,500', to: 'USD', status: 'pending' },
  { action: 'Buy', from: 'USD', amount: '2,500', to: 'ETH', status: 'pending' },
  { action: 'Buy', from: 'USD', amount: '1,000', to: 'ARB', status: 'pending' },
]

export default function RebalancePage() {
  const [selectedStrategy, setSelectedStrategy] = useState('balanced')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [isSimulating, setIsSimulating] = useState(false)

  const handleSimulate = () => {
    setIsSimulating(true)
    // Simulate API call
    setTimeout(() => setIsSimulating(false), 2000)
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Rebalance Portfolio</h1>
        <p className="text-muted-foreground mt-1">AI-powered portfolio optimization and rebalancing</p>
      </div>

      {/* Current vs Target Allocation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Current Allocation</h3>
          <div className="space-y-3">
            {mockCurrentAllocation.map((token) => (
              <div key={token.symbol} className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1">
                  <span className="font-medium w-16">{token.symbol}</span>
                  <div className="flex-1">
                    <div className="h-2 bg-secondary rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-primary transition-all duration-500"
                        style={{ width: `${token.percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
                <span className="text-sm font-medium w-16 text-right">{token.percentage}%</span>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">Target Allocation</h3>
          <div className="space-y-3">
            {mockCurrentAllocation.map((token) => (
              <div key={token.symbol} className="flex items-center justify-between">
                <div className="flex items-center gap-3 flex-1">
                  <span className="font-medium w-16">{token.symbol}</span>
                  <div className="flex-1">
                    <div className="h-2 bg-secondary rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-green-500 transition-all duration-500"
                        style={{ width: `${token.targetPercentage}%` }}
                      />
                    </div>
                  </div>
                </div>
                <span className="text-sm font-medium w-16 text-right">{token.targetPercentage}%</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Strategy Selection */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Select Strategy</h3>
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            <Settings className="h-4 w-4" />
            Advanced Settings
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {mockStrategies.map((strategy) => {
            const Icon = strategy.icon
            return (
              <button
                key={strategy.id}
                onClick={() => setSelectedStrategy(strategy.id)}
                className={`p-4 border-2 rounded-lg transition-all text-left ${
                  selectedStrategy === strategy.id
                    ? 'border-primary bg-primary/5'
                    : 'border-border hover:border-muted-foreground'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg ${
                    selectedStrategy === strategy.id ? 'bg-primary/10' : 'bg-secondary'
                  }`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium">{strategy.name}</h4>
                    <p className="text-sm text-muted-foreground mt-1">{strategy.description}</p>
                    <div className="mt-3 space-y-1">
                      <p className="text-xs">
                        <span className="text-muted-foreground">Expected Return:</span>{' '}
                        <span className="font-medium">{strategy.metrics.expectedReturn}</span>
                      </p>
                      <p className="text-xs">
                        <span className="text-muted-foreground">Risk Level:</span>{' '}
                        <span className="font-medium">{strategy.metrics.risk}</span>
                      </p>
                    </div>
                  </div>
                </div>
              </button>
            )
          })}
        </div>

        {showAdvanced && (
          <Card className="mt-4 p-4 bg-secondary/50 space-y-4">
            <div>
              <label className="text-sm font-medium">Rebalancing Threshold</label>
              <input
                type="range"
                min="1"
                max="10"
                defaultValue="5"
                className="w-full mt-2"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>1%</span>
                <span>5%</span>
                <span>10%</span>
              </div>
            </div>
            <div>
              <label className="text-sm font-medium">Max Slippage</label>
              <select className="w-full mt-2 px-3 py-2 bg-background border border-input rounded-md">
                <option>0.5%</option>
                <option>1%</option>
                <option>2%</option>
              </select>
            </div>
          </Card>
        )}
      </Card>

      {/* Rebalancing Preview */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Rebalancing Preview</h3>
        <div className="space-y-3">
          {mockRebalancingSteps.map((step, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-secondary/50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className={`p-2 rounded-lg ${
                  step.action === 'Buy' ? 'bg-green-500/10' : 'bg-red-500/10'
                }`}>
                  {step.action === 'Buy' ? (
                    <TrendingUp className="h-4 w-4 text-green-500" />
                  ) : (
                    <TrendingUp className="h-4 w-4 text-red-500 rotate-180" />
                  )}
                </div>
                <div>
                  <p className="font-medium">
                    {step.action} {step.amount} {step.action === 'Buy' ? step.to : step.from}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    {step.action === 'Buy' ? `With ${step.from}` : `For ${step.to}`}
                  </p>
                </div>
              </div>
              <ChevronRight className="h-5 w-5 text-muted-foreground" />
            </div>
          ))}
        </div>

        <Card className="mt-4 p-4 bg-orange-500/10 border-orange-500/20">
          <div className="flex gap-3">
            <AlertTriangle className="h-5 w-5 text-orange-500 flex-shrink-0 mt-0.5" />
            <div className="space-y-1 text-sm">
              <p className="font-medium">Estimated Costs</p>
              <p className="text-muted-foreground">
                Network fees: ~$45.67 • Price impact: 0.23% • Total trades: 4
              </p>
            </div>
          </div>
        </Card>
      </Card>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <button
          onClick={handleSimulate}
          disabled={isSimulating}
          className="flex-1 flex items-center justify-center gap-2 py-4 bg-secondary hover:bg-secondary/80 rounded-lg font-medium transition-colors disabled:opacity-50"
        >
          {isSimulating ? (
            <RefreshCw className="h-5 w-5 animate-spin" />
          ) : (
            <Play className="h-5 w-5" />
          )}
          {isSimulating ? 'Simulating...' : 'Simulate Rebalance'}
        </button>
        <button className="flex-1 py-4 bg-primary text-primary-foreground hover:bg-primary/90 rounded-lg font-medium transition-colors">
          Execute Rebalance
        </button>
      </div>

      {/* Info Card */}
      <Card className="p-4 bg-blue-500/10 border-blue-500/20">
        <div className="flex gap-3">
          <Info className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="space-y-1 text-sm">
            <p className="font-medium">AI-Powered Optimization</p>
            <p className="text-muted-foreground">
              Our AI analyzes market conditions, gas prices, and slippage to find the most efficient rebalancing path. 
              All trades are executed through 1inch for best rates.
            </p>
          </div>
        </div>
      </Card>
    </div>
  )
}