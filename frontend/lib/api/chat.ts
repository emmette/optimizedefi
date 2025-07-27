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
  private onMessageCallback?: (message: ChatWebSocketMessage) => void
  private onErrorCallback?: (error: Event) => void
  private onCloseCallback?: () => void
  private onOpenCallback?: () => void
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  constructor(clientId: string) {
    this.clientId = clientId
  }

  connect() {
    const wsUrl = `${WS_BASE_URL}${API_ENDPOINTS.chatWebSocket(this.clientId)}`
    
    try {
      this.ws = new WebSocket(wsUrl)
      
      this.ws.onopen = () => {
        console.log('WebSocket connected')
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
        if (this.onCloseCallback) {
          this.onCloseCallback()
        }
        
        // Attempt to reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++
          setTimeout(() => {
            console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`)
            this.connect()
          }, this.reconnectDelay * this.reconnectAttempts)
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error)
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
    if (this.ws) {
      this.ws.close()
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