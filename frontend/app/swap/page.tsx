'use client'

import { useState } from 'react'
import { Card } from '@/components/ui/Card'
import { 
  ArrowDownUp, 
  Settings, 
  Info, 
  ChevronDown,
  Zap,
  Clock,
  Shield,
  ArrowRight
} from 'lucide-react'

// Mock token list
const mockTokens = [
  { symbol: 'ETH', name: 'Ethereum', balance: 12.5, price: 3600, logo: '🔷' },
  { symbol: 'USDC', name: 'USD Coin', balance: 5000, price: 1, logo: '💵' },
  { symbol: 'MATIC', name: 'Polygon', balance: 15000, price: 2.13, logo: '🟣' },
  { symbol: 'OP', name: 'Optimism', balance: 8500, price: 3.35, logo: '🔴' },
  { symbol: 'ARB', name: 'Arbitrum', balance: 12000, price: 1.67, logo: '🔵' },
  { symbol: 'USDT', name: 'Tether', balance: 3000, price: 1, logo: '💚' },
  { symbol: 'DAI', name: 'Dai', balance: 2500, price: 1, logo: '🟡' },
  { symbol: 'LINK', name: 'Chainlink', balance: 150, price: 15, logo: '🔗' },
]

// Mock route data
const mockRoutes = [
  {
    id: 1,
    protocol: '1inch Fusion+',
    outputAmount: 3182.45,
    gasCost: 12.34,
    time: '~15 sec',
    isBest: true,
  },
  {
    id: 2,
    protocol: 'Uniswap V3',
    outputAmount: 3175.23,
    gasCost: 15.67,
    time: '~20 sec',
    isBest: false,
  },
  {
    id: 3,
    protocol: 'Curve',
    outputAmount: 3170.89,
    gasCost: 18.90,
    time: '~25 sec',
    isBest: false,
  },
]

export default function SwapPage() {
  const [fromToken, setFromToken] = useState(mockTokens[0])
  const [toToken, setToToken] = useState(mockTokens[1])
  const [fromAmount, setFromAmount] = useState('')
  const [toAmount, setToAmount] = useState('')
  const [showTokenSelect, setShowTokenSelect] = useState<'from' | 'to' | null>(null)
  const [slippage, setSlippage] = useState('0.5')
  const [showSettings, setShowSettings] = useState(false)

  const handleSwapTokens = () => {
    const temp = fromToken
    setFromToken(toToken)
    setToToken(temp)
    const tempAmount = fromAmount
    setFromAmount(toAmount)
    setToAmount(tempAmount)
  }

  const handleFromAmountChange = (value: string) => {
    setFromAmount(value)
    if (value && !isNaN(parseFloat(value))) {
      const calculatedAmount = (parseFloat(value) * fromToken.price / toToken.price).toFixed(6)
      setToAmount(calculatedAmount)
    } else {
      setToAmount('')
    }
  }

  const handleToAmountChange = (value: string) => {
    setToAmount(value)
    if (value && !isNaN(parseFloat(value))) {
      const calculatedAmount = (parseFloat(value) * toToken.price / fromToken.price).toFixed(6)
      setFromAmount(calculatedAmount)
    } else {
      setFromAmount('')
    }
  }


  return (
    <div className="px-8 py-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold">Swap</h1>
          <p className="text-muted-foreground mt-1">Exchange tokens with the best rates across multiple DEXs</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Swap Interface */}
          <div className="lg:col-span-2">
            <Card className="p-6">
              {/* Settings */}
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-semibold">Token Swap</h2>
                <button
                  onClick={() => setShowSettings(!showSettings)}
                  className="p-2 hover:bg-accent rounded-lg transition-colors"
                >
                  <Settings className="h-5 w-5" />
                </button>
              </div>

              {showSettings && (
                <Card className="p-4 mb-6 bg-background">
                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium mb-2 block">Slippage Tolerance</label>
                      <div className="flex gap-2">
                        {['0.1', '0.5', '1.0'].map((value) => (
                          <button
                            key={value}
                            onClick={() => setSlippage(value)}
                            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                              slippage === value
                                ? 'bg-primary text-primary-foreground'
                                : 'bg-secondary hover:bg-secondary/80'
                            }`}
                          >
                            {value}%
                          </button>
                        ))}
                        <input
                          type="text"
                          value={slippage}
                          onChange={(e) => setSlippage(e.target.value)}
                          className="px-3 py-1.5 bg-background border border-input rounded-md text-sm w-20"
                          placeholder="Custom"
                        />
                      </div>
                    </div>
                  </div>
                </Card>
              )}

              {/* From Token */}
              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">From</label>
                <div className="relative">
                  <div className="flex items-center gap-3 p-4 bg-background rounded-lg border border-border">
                    <button
                      onClick={() => setShowTokenSelect('from')}
                      className="flex items-center gap-2 px-3 py-1.5 bg-secondary hover:bg-secondary/80 rounded-lg transition-colors"
                    >
                      <span className="text-xl">{fromToken.logo}</span>
                      <span className="font-medium">{fromToken.symbol}</span>
                      <ChevronDown className="h-4 w-4" />
                    </button>
                    <input
                      type="text"
                      value={fromAmount}
                      onChange={(e) => handleFromAmountChange(e.target.value)}
                      placeholder="0.0"
                      className="flex-1 bg-transparent text-right text-2xl font-medium outline-none"
                    />
                  </div>
                  <div className="flex items-center justify-between mt-2 px-1">
                    <span className="text-sm text-muted-foreground">
                      Balance: {fromToken.balance.toLocaleString()} {fromToken.symbol}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      ~${fromAmount ? (parseFloat(fromAmount) * fromToken.price).toFixed(2) : '0.00'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Swap Button */}
              <div className="flex justify-center my-4">
                <button
                  onClick={handleSwapTokens}
                  className="p-2 hover:bg-accent rounded-lg transition-colors"
                >
                  <ArrowDownUp className="h-5 w-5" />
                </button>
              </div>

              {/* To Token */}
              <div className="space-y-2">
                <label className="text-sm text-muted-foreground">To</label>
                <div className="relative">
                  <div className="flex items-center gap-3 p-4 bg-background rounded-lg border border-border">
                    <button
                      onClick={() => setShowTokenSelect('to')}
                      className="flex items-center gap-2 px-3 py-1.5 bg-secondary hover:bg-secondary/80 rounded-lg transition-colors"
                    >
                      <span className="text-xl">{toToken.logo}</span>
                      <span className="font-medium">{toToken.symbol}</span>
                      <ChevronDown className="h-4 w-4" />
                    </button>
                    <input
                      type="text"
                      value={toAmount}
                      onChange={(e) => handleToAmountChange(e.target.value)}
                      placeholder="0.0"
                      className="flex-1 bg-transparent text-right text-2xl font-medium outline-none"
                    />
                  </div>
                  <div className="flex items-center justify-between mt-2 px-1">
                    <span className="text-sm text-muted-foreground">
                      Balance: {toToken.balance.toLocaleString()} {toToken.symbol}
                    </span>
                    <span className="text-sm text-muted-foreground">
                      ~${toAmount ? (parseFloat(toAmount) * toToken.price).toFixed(2) : '0.00'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Route Info */}
              {fromAmount && toAmount && (
                <Card className="mt-6 p-4 bg-background">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Rate</span>
                      <span className="text-sm font-medium">
                        1 {fromToken.symbol} = {(fromToken.price / toToken.price).toFixed(6)} {toToken.symbol}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Price Impact</span>
                      <span className="text-sm font-medium text-green-500">{'<0.01%'}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Network Fee</span>
                      <span className="text-sm font-medium">~$12.34</span>
                    </div>
                  </div>
                </Card>
              )}

              {/* Swap Button */}
              <button
                disabled={!fromAmount || !toAmount}
                className="w-full mt-6 py-4 bg-primary text-primary-foreground rounded-lg font-medium hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {!fromAmount || !toAmount ? 'Enter an amount' : 'Swap'}
              </button>
            </Card>
          </div>

          {/* Routes */}
          <div className="space-y-6">
            {/* Best Route */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Best Route</h3>
              {fromAmount && toAmount ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Zap className="h-5 w-5 text-yellow-500" />
                      <span className="font-medium">Optimized Route</span>
                    </div>
                    <span className="text-sm text-green-500">Save $3.21</span>
                  </div>
                  <div className="pl-7 space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <span>{fromToken.symbol}</span>
                      <ArrowRight className="h-3 w-3" />
                      <span className="text-muted-foreground">1inch</span>
                      <ArrowRight className="h-3 w-3" />
                      <span>{toToken.symbol}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Enter an amount to see available routes</p>
              )}
            </Card>

            {/* All Routes */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold mb-4">Available Routes</h3>
              {fromAmount && toAmount ? (
                <div className="space-y-3">
                  {mockRoutes.map((route) => (
                    <div
                      key={route.id}
                      className={`p-3 rounded-lg border ${
                        route.isBest ? 'border-primary bg-primary/5' : 'border-border bg-background'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{route.protocol}</span>
                          {route.isBest && (
                            <span className="text-xs bg-primary text-primary-foreground px-2 py-0.5 rounded">
                              BEST
                            </span>
                          )}
                        </div>
                        <span className="font-medium">{route.outputAmount.toLocaleString()} {toToken.symbol}</span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          <span>{route.time}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Shield className="h-3 w-3" />
                          <span>${route.gasCost.toFixed(2)}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">No routes available</p>
              )}
            </Card>

            {/* Info */}
            <Card className="p-4 bg-blue-500/10 border-blue-500/20">
              <div className="flex gap-3">
                <Info className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className="text-sm font-medium">Smart Routing</p>
                  <p className="text-sm text-muted-foreground">
                    We search across multiple DEXs to find you the best rates and lowest fees.
                  </p>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>

      {/* Token Select Modal */}
      {showTokenSelect && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Select Token</h3>
              <button
                onClick={() => setShowTokenSelect(null)}
                className="p-2 hover:bg-accent rounded-lg transition-colors"
              >
                ✕
              </button>
            </div>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {mockTokens.map((token) => (
                <button
                  key={token.symbol}
                  onClick={() => {
                    if (showTokenSelect === 'from') {
                      setFromToken(token)
                    } else {
                      setToToken(token)
                    }
                    setShowTokenSelect(null)
                  }}
                  className="w-full flex items-center justify-between p-3 hover:bg-accent rounded-lg transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{token.logo}</span>
                    <div className="text-left">
                      <p className="font-medium">{token.symbol}</p>
                      <p className="text-sm text-muted-foreground">{token.name}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-medium">{token.balance.toLocaleString()}</p>
                    <p className="text-sm text-muted-foreground">
                      ${(token.balance * token.price).toLocaleString()}
                    </p>
                  </div>
                </button>
              ))}
            </div>
          </Card>
        </div>
      )}
    </div>
  )
}