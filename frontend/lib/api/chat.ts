import { WS_BASE_URL, API_ENDPOINTS } from './config'

export interface ChatMessage {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: string
}

export interface ChatWebSocketMessage {
  type: 'user_message' | 'ai_response' | 'error'
  content: string
  timestamp: string
}

export class ChatWebSocketClient {
  private ws: WebSocket | null = null
  private clientId: string
  private accessToken?: string
  private onMessageCallback?: (message: ChatWebSocketMessage) => void
  private onErrorCallback?: (error: Event) => void
  private onCloseCallback?: () => void
  private onOpenCallback?: () => void
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000
  private isIntentionalDisconnect = false
  private connectionTimeout?: NodeJS.Timeout

  constructor(clientId: string, accessToken?: string) {
    this.clientId = clientId
    this.accessToken = accessToken
  }

  connect() {
    // Clear any existing connection first
    if (this.ws) {
      this.disconnect()
    }

    this.isIntentionalDisconnect = false
    
    let wsUrl = `${WS_BASE_URL}${API_ENDPOINTS.chatWebSocket(this.clientId)}`
    
    // Add token to query params if available
    if (this.accessToken) {
      wsUrl += `?token=${encodeURIComponent(this.accessToken)}`
    }
    
    try {
      this.ws = new WebSocket(wsUrl)
      
      // Set a connection timeout
      this.connectionTimeout = setTimeout(() => {
        if (this.ws && this.ws.readyState === WebSocket.CONNECTING) {
          console.log('WebSocket connection timeout, closing...')
          this.ws.close()
        }
      }, 10000) // 10 second timeout
      
      this.ws.onopen = () => {
        console.log('WebSocket connected')
        // Clear the connection timeout
        if (this.connectionTimeout) {
          clearTimeout(this.connectionTimeout)
        }
        this.reconnectAttempts = 0
        if (this.onOpenCallback) {
          this.onOpenCallback()
        }
      }
      
      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data) as ChatWebSocketMessage
          if (this.onMessageCallback) {
            this.onMessageCallback(message)
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        if (this.onErrorCallback) {
          this.onErrorCallback(error)
        }
      }
      
      this.ws.onclose = () => {
        console.log('WebSocket disconnected')
        // Clear the connection timeout
        if (this.connectionTimeout) {
          clearTimeout(this.connectionTimeout)
        }
        
        if (this.onCloseCallback) {
          this.onCloseCallback()
        }
        
        // Only attempt to reconnect if not intentionally disconnected
        if (!this.isIntentionalDisconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++
          const delay = Math.min(this.reconnectDelay * this.reconnectAttempts, 10000) // Max 10s delay
          console.log(`Attempting to reconnect in ${delay}ms... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
          setTimeout(() => {
            if (!this.isIntentionalDisconnect) {
              this.connect()
            }
          }, delay)
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
      if (this.connectionTimeout) {
        clearTimeout(this.connectionTimeout)
      }
    }
  }

  sendMessage(content: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      const message = {
        type: 'user_message',
        content,
        timestamp: new Date().toISOString()
      }
      this.ws.send(JSON.stringify(message))
    } else {
      console.error('WebSocket is not connected')
    }
  }

  disconnect() {
    this.isIntentionalDisconnect = true
    this.reconnectAttempts = 0
    
    if (this.connectionTimeout) {
      clearTimeout(this.connectionTimeout)
    }
    
    if (this.ws) {
      // Remove event handlers to prevent memory leaks
      this.ws.onopen = null
      this.ws.onmessage = null
      this.ws.onerror = null
      this.ws.onclose = null
      
      if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING) {
        this.ws.close()
      }
      this.ws = null
    }
  }

  onMessage(callback: (message: ChatWebSocketMessage) => void) {
    this.onMessageCallback = callback
  }

  onError(callback: (error: Event) => void) {
    this.onErrorCallback = callback
  }

  onClose(callback: () => void) {
    this.onCloseCallback = callback
  }

  onOpen(callback: () => void) {
    this.onOpenCallback = callback
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN
  }
}