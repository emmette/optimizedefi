'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User } from 'lucide-react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

interface ChatPanelProps {
  onSuggestedAction?: (action: string) => void
}

export function ChatPanel({ onSuggestedAction }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Welcome! I can help you analyze your portfolio, suggest optimizations, and execute trades. How can I assist you today?',
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    // Simulate AI response
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: getAIResponse(input),
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
      setIsLoading(false)
    }, 1000)
  }

  const getAIResponse = (query: string): string => {
    const lowerQuery = query.toLowerCase()
    
    if (lowerQuery.includes('portfolio') && lowerQuery.includes('performance')) {
      return 'Your portfolio has shown strong performance over the past month with a 12.5% return. ETH has been your best performer (+15.2%), while MATIC has underperformed (-3.1%). Would you like me to suggest some rebalancing strategies?'
    }
    
    if (lowerQuery.includes('rebalance')) {
      return 'Based on your current allocation, I recommend reducing ETH exposure from 35.9% to 30% and increasing your stablecoin allocation for better risk management. This would involve swapping approximately $5,000 worth of ETH. Shall I prepare this rebalancing plan for you?'
    }
    
    if (lowerQuery.includes('yield') || lowerQuery.includes('apy')) {
      return 'I found several high-yield opportunities:\n\n1. Aave V3 on Ethereum: 18.5% APY on ETH deposits\n2. Compound on Polygon: 12.3% APY on USDC\n3. Yearn on Optimism: 9.8% APY on DAI\n\nWould you like me to help you allocate funds to these protocols?'
    }
    
    if (lowerQuery.includes('gas') || lowerQuery.includes('fee')) {
      return 'Current gas prices:\n• Ethereum: 45 gwei (~$12 for swap)\n• Polygon: 30 gwei (~$0.01)\n• Optimism: 0.001 gwei (~$0.05)\n• Arbitrum: 0.1 gwei (~$0.10)\n\nI recommend using Polygon or Arbitrum for smaller transactions to save on fees.'
    }
    
    return 'I understand you\'re asking about "' + query + '". Let me analyze your portfolio data to provide you with the best recommendations. What specific aspect would you like me to focus on?'
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const suggestedActions = [
    { icon: '🔄', label: 'Quick Swap', action: 'swap' },
    { icon: '⚡', label: 'AI Rebalance', action: 'rebalance' },
    { icon: '📊', label: 'Analyze Portfolio', action: 'analyze' },
    { icon: '💰', label: 'Find Yield', action: 'yield' },
    { icon: '⛽', label: 'Optimize Gas', action: 'gas' },
  ]

  return (
    <>
      <div className="px-5 py-6 border-b border-border flex justify-between items-center">
        <div>
          <h2 className="text-lg font-semibold">AI Assistant</h2>
          <p className="text-sm text-muted-foreground">Portfolio optimization help</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${
                message.role === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {message.role === 'assistant' && (
                <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
                  <Bot className="h-5 w-5 text-primary" />
                </div>
              )}
              <div
                className={`max-w-[80%] p-3 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-accent/50'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                <p className="text-xs opacity-70 mt-1">
                  {message.timestamp.toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>
              {message.role === 'user' && (
                <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center flex-shrink-0">
                  <User className="h-5 w-5 text-primary-foreground" />
                </div>
              )}
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-3">
              <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
                <Bot className="h-5 w-5 text-primary" />
              </div>
              <div className="bg-accent/50 p-3 rounded-lg">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce delay-100" />
                  <div className="w-2 h-2 bg-primary rounded-full animate-bounce delay-200" />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="px-5 py-4 border-t border-border">
        <div className="mb-4">
          <p className="text-sm font-medium text-muted-foreground mb-3">Suggested Actions</p>
          <div className="flex flex-wrap gap-2">
            {suggestedActions.map((action) => (
              <button
                key={action.action}
                onClick={() => {
                  setInput(`I want to ${action.label.toLowerCase()}`)
                  if (onSuggestedAction) {
                    onSuggestedAction(action.action)
                  }
                }}
                className="px-3 py-1.5 text-xs bg-secondary hover:bg-primary hover:text-primary-foreground border border-border rounded-md transition-all"
              >
                {action.icon} {action.label}
              </button>
            ))}
          </div>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything about your portfolio..."
            className="flex-1 px-4 py-2 bg-background border border-input rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className="p-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>
    </>
  )
}