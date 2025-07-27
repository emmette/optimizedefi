'use client'

import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User } from 'lucide-react'
import { useChat } from '@/hooks/useChat'
import { useAccount } from 'wagmi'

interface ChatPanelProps {
  onSuggestedAction?: (action: string) => void
}

export function ChatPanel({ onSuggestedAction }: ChatPanelProps) {
  const { isConnected: isWalletConnected } = useAccount()
  const { messages, isConnected, isTyping, sendMessage } = useChat()
  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSend = async () => {
    if (!input.trim() || !isConnected || isTyping) return

    setInput('')
    sendMessage(input)
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
          <p className="text-sm text-muted-foreground" suppressHydrationWarning>
            {isWalletConnected 
              ? (isConnected 
                  ? 'Portfolio optimization help' 
                  : 'Connecting to chat service...')
              : 'Connect wallet to start'}
          </p>
        </div>
        {isWalletConnected && (
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} suppressHydrationWarning />
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-4">
        <div className="space-y-4">
          {messages.length === 0 && isWalletConnected && (
            <div className="text-center py-8">
              <p className="text-muted-foreground">
                {isConnected ? 'Start a conversation about your portfolio!' : 'Connecting to AI assistant...'}
              </p>
            </div>
          )}
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
                  {new Date(message.timestamp).toLocaleTimeString([], {
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
          {isTyping && (
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
            disabled={!isConnected || isTyping || !isWalletConnected}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || !isConnected || isTyping || !isWalletConnected}
            className="p-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </div>
    </>
  )
}