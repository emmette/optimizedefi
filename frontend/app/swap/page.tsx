'use client'

import { useState } from 'react'
import Image from 'next/image'
import { Card } from '@/components/ui/Card'
import { ArrowDownUp, Settings, Info, ChevronDown, Search } from 'lucide-react'

// Mock token list
const mockTokens = [
  { symbol: 'ETH', name: 'Ethereum', balance: '5.234', value: 10468.0, logo: 'https://tokens.1inch.io/0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee.png' },
  { symbol: 'USDC', name: 'USD Coin', balance: '15000', value: 15000.0, logo: 'https://tokens.1inch.io/0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48.png' },
  { symbol: 'MATIC', name: 'Polygon', balance: '12500', value: 10000.0, logo: 'https://tokens.1inch.io/0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0.png' },
  { symbol: 'OP', name: 'Optimism', balance: '4000', value: 8000.0, logo: 'https://tokens.1inch.io/0x4200000000000000000000000000000000000042.png' },
  { symbol: 'ARB', name: 'Arbitrum', balance: '8000', value: 8000.0, logo: 'https://tokens.1inch.io/0x912ce59144191c1204e64559fe8253a0e49e6548.png' },
]

export default function SwapPage() {
  const [fromToken, setFromToken] = useState(mockTokens[0])
  const [toToken, setToToken] = useState(mockTokens[1])
  const [fromAmount, setFromAmount] = useState('')
  const [toAmount, setToAmount] = useState('')
  const [showFromTokenList, setShowFromTokenList] = useState(false)
  const [showToTokenList, setShowToTokenList] = useState(false)
  const [slippage, setSlippage] = useState('0.5')
  const [showSettings, setShowSettings] = useState(false)

  const handleSwapTokens = () => {
    const temp = fromToken
    setFromToken(toToken)
    setToToken(temp)
    setFromAmount(toAmount)
    setToAmount(fromAmount)
  }

  const handleFromAmountChange = (value: string) => {
    setFromAmount(value)
    // Mock conversion rate
    if (value && !isNaN(parseFloat(value))) {
      const mockRate = 2000 // 1 ETH = 2000 USDC
      setToAmount((parseFloat(value) * mockRate).toFixed(2))
    } else {
      setToAmount('')
    }
  }

  const TokenSelector = ({ 
    token, 
    showList, 
    setShowList, 
    onSelectToken 
  }: { 
    token: typeof mockTokens[0], 
    showList: boolean, 
    setShowList: (show: boolean) => void,
    onSelectToken: (token: typeof mockTokens[0]) => void 
  }) => (
    <div className="relative">
      <button
        onClick={() => setShowList(!showList)}
        className="flex items-center gap-2 px-3 py-2 bg-secondary hover:bg-secondary/80 rounded-lg transition-colors"
      >
        <Image src={token.logo} alt={token.symbol} width={24} height={24} className="rounded-full" />
        <span className="font-medium">{token.symbol}</span>
        <ChevronDown className="h-4 w-4" />
      </button>

      {showList && (
        <div className="absolute top-full mt-2 left-0 right-0 w-64 bg-card border border-border rounded-lg shadow-lg z-10">
          <div className="p-3 border-b border-border">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search tokens..."
                className="w-full pl-10 pr-4 py-2 bg-background border border-input rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>
          </div>
          <div className="max-h-64 overflow-y-auto">
            {mockTokens.map((t) => (
              <button
                key={t.symbol}
                onClick={() => {
                  onSelectToken(t)
                  setShowList(false)
                }}
                className="w-full flex items-center justify-between p-3 hover:bg-accent transition-colors"
              >
                <div className="flex items-center gap-3">
                  <Image src={t.logo} alt={t.symbol} width={32} height={32} className="rounded-full" />
                  <div className="text-left">
                    <p className="font-medium">{t.symbol}</p>
                    <p className="text-sm text-muted-foreground">{t.name}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">{t.balance}</p>
                  <p className="text-xs text-muted-foreground">${t.value.toLocaleString()}</p>
                </div>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )

  return (
    <div className="p-6">
      <div className="max-w-xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold">Swap</h1>
          <p className="text-muted-foreground mt-1">Exchange tokens at the best rates across DEXs</p>
        </div>

        {/* Swap Card */}
        <Card className="p-6 space-y-4">
          {/* Settings Button */}
          <div className="flex justify-end">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 hover:bg-accent rounded-lg transition-colors"
            >
              <Settings className="h-5 w-5" />
            </button>
          </div>

          {/* Settings Panel */}
          {showSettings && (
            <Card className="p-4 bg-secondary/50 space-y-4">
              <div>
                <label className="text-sm font-medium">Slippage Tolerance</label>
                <div className="flex gap-2 mt-2">
                  {['0.1', '0.5', '1.0'].map((value) => (
                    <button
                      key={value}
                      onClick={() => setSlippage(value)}
                      className={`px-3 py-1 rounded-md text-sm transition-colors ${
                        slippage === value
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-background hover:bg-accent'
                      }`}
                    >
                      {value}%
                    </button>
                  ))}
                  <input
                    type="text"
                    value={slippage}
                    onChange={(e) => setSlippage(e.target.value)}
                    className="px-3 py-1 w-20 bg-background border border-input rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                    placeholder="Custom"
                  />
                </div>
              </div>
            </Card>
          )}

          {/* From Token */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">From</span>
              <span className="text-muted-foreground">
                Balance: {fromToken.balance} {fromToken.symbol}
              </span>
            </div>
            <div className="flex gap-3">
              <input
                type="text"
                value={fromAmount}
                onChange={(e) => handleFromAmountChange(e.target.value)}
                placeholder="0.0"
                className="flex-1 text-2xl bg-transparent focus:outline-none"
              />
              <TokenSelector
                token={fromToken}
                showList={showFromTokenList}
                setShowList={setShowFromTokenList}
                onSelectToken={setFromToken}
              />
            </div>
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>≈ ${fromAmount ? (parseFloat(fromAmount) * 2000).toLocaleString() : '0'}</span>
              <button className="hover:text-primary transition-colors">Max</button>
            </div>
          </div>

          {/* Swap Button */}
          <div className="flex justify-center">
            <button
              onClick={handleSwapTokens}
              className="p-2 bg-secondary hover:bg-secondary/80 rounded-lg transition-all hover:rotate-180"
            >
              <ArrowDownUp className="h-5 w-5" />
            </button>
          </div>

          {/* To Token */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">To</span>
              <span className="text-muted-foreground">
                Balance: {toToken.balance} {toToken.symbol}
              </span>
            </div>
            <div className="flex gap-3">
              <input
                type="text"
                value={toAmount}
                readOnly
                placeholder="0.0"
                className="flex-1 text-2xl bg-transparent focus:outline-none"
              />
              <TokenSelector
                token={toToken}
                showList={showToTokenList}
                setShowList={setShowToTokenList}
                onSelectToken={setToToken}
              />
            </div>
            <div className="text-sm text-muted-foreground">
              ≈ ${toAmount ? parseFloat(toAmount).toLocaleString() : '0'}
            </div>
          </div>

          {/* Exchange Rate */}
          {fromAmount && toAmount && (
            <Card className="p-4 bg-secondary/50">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Exchange Rate</span>
                <span>
                  1 {fromToken.symbol} = {(parseFloat(toAmount) / parseFloat(fromAmount)).toFixed(4)} {toToken.symbol}
                </span>
              </div>
            </Card>
          )}

          {/* Swap Button */}
          <button
            disabled={!fromAmount || !toAmount}
            className={`w-full py-4 rounded-lg font-medium transition-colors ${
              fromAmount && toAmount
                ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                : 'bg-secondary text-muted-foreground cursor-not-allowed'
            }`}
          >
            {!fromAmount || !toAmount ? 'Enter an amount' : 'Swap'}
          </button>
        </Card>

        {/* Info Card */}
        <Card className="p-4 bg-blue-500/10 border-blue-500/20">
          <div className="flex gap-3">
            <Info className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
            <div className="space-y-1 text-sm">
              <p className="font-medium">Powered by 1inch Aggregation Protocol</p>
              <p className="text-muted-foreground">
                We search across multiple DEXs to find you the best rates with the lowest gas fees.
              </p>
            </div>
          </div>
        </Card>

        {/* Route Info */}
        {fromAmount && toAmount && (
          <Card className="p-6 space-y-4">
            <h3 className="font-semibold">Route</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Protocol</span>
                <span>Uniswap V3 (60%) + SushiSwap (40%)</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Price Impact</span>
                <span className="text-green-500">{'<'}0.01%</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Network Fee</span>
                <span>~$12.34</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Minimum Received</span>
                <span>{(parseFloat(toAmount) * 0.995).toFixed(4)} {toToken.symbol}</span>
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  )
}