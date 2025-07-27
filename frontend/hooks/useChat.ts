import { useEffect, useRef, useState, useCallback } from 'react'
import { useAccount } from 'wagmi'
import { ChatWebSocketClient, ChatMessage, ChatWebSocketMessage } from '@/lib/api/chat'

export function useChat() {
  const { address } = useAccount()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const wsClient = useRef<ChatWebSocketClient | null>(null)

  useEffect(() => {
    if (!address) return

    // Create WebSocket client with wallet address as client ID
    wsClient.current = new ChatWebSocketClient(address)

    wsClient.current.onMessage((message: ChatWebSocketMessage) => {
      if (message.type === 'ai_response') {
        setIsTyping(false)
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          content: message.content,
          role: 'assistant',
          timestamp: message.timestamp
        }])
      }
    })

    wsClient.current.onError((error) => {
      console.error('Chat WebSocket error:', error)
      setIsConnected(false)
    })

    wsClient.current.onClose(() => {
      setIsConnected(false)
    })

    wsClient.current.onOpen(() => {
      console.log('Chat WebSocket connected')
      setIsConnected(true)
    })

    wsClient.current.connect()

    return () => {
      wsClient.current?.disconnect()
    }
  }, [address])

  const sendMessage = useCallback((content: string) => {
    if (!wsClient.current?.isConnected()) {
      console.error('Chat is not connected')
      return
    }

    // Add user message to chat
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content,
      role: 'user',
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])

    // Send message through WebSocket
    wsClient.current.sendMessage(content)
    
    // Show typing indicator
    setIsTyping(true)
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
  }, [])

  return {
    messages,
    isConnected,
    isTyping,
    sendMessage,
    clearMessages
  }
}