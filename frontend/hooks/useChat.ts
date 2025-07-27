import { useEffect, useRef, useState, useCallback } from 'react'
import { useAccount } from 'wagmi'
import { ChatWebSocketClient, ChatMessage, ChatWebSocketMessage } from '@/lib/api/chat'
import { useAuthStore } from '@/store/authStore'

export function useChat() {
  const { address } = useAccount()
  const accessToken = useAuthStore((state) => state.accessToken)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const [isTyping, setIsTyping] = useState(false)
  const wsClient = useRef<ChatWebSocketClient | null>(null)

  useEffect(() => {
    if (!address) {
      // Clean up existing connection when wallet disconnects
      if (wsClient.current) {
        wsClient.current.disconnect()
        wsClient.current = null
      }
      return
    }

    // Only create new client if none exists or address changed
    const shouldCreateNewClient = !wsClient.current || 
      (wsClient.current && (wsClient.current as any).clientId !== address)
    
    if (shouldCreateNewClient) {
      // Clean up existing connection first
      if (wsClient.current) {
        wsClient.current.disconnect()
      }

      // Create WebSocket client with wallet address as client ID and access token
      wsClient.current = new ChatWebSocketClient(address, accessToken || undefined)

      wsClient.current.onMessage((message: ChatWebSocketMessage) => {
        if (message.type === 'ai_response') {
          setIsTyping(false)
          setMessages(prev => [...prev, {
            id: Date.now().toString(),
            content: message.content,
            role: 'assistant',
            timestamp: message.timestamp
          }])
        } else if (message.type === 'typing') {
          setIsTyping(true)
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
        setIsTyping(false)
      })

      wsClient.current.connect()
    }

    return () => {
      // Don't disconnect on cleanup, we'll manage lifecycle manually
      // to prevent unnecessary reconnections
    }
  }, [address]) // Remove accessToken from dependencies to prevent reconnects on token refresh

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