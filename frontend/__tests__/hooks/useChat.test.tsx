import { renderHook, act, waitFor } from '@testing-library/react'
import { useChat } from '@/hooks/useChat'
import { ChatWebSocketClient } from '@/lib/api/chat'
import { useAccount } from 'wagmi'
import { useAuthStore } from '@/store/authStore'

// Mock dependencies
jest.mock('wagmi')
jest.mock('@/store/authStore')
jest.mock('@/lib/api/chat')

describe('useChat hook', () => {
  const mockAddress = '0x742d35Cc6634C0532925a3b844Bc9e7595f5b8e7'
  const mockAccessToken = 'test-token-123'
  let mockWsClient: any
  
  beforeEach(() => {
    // Reset mocks
    jest.clearAllMocks()
    
    // Mock wagmi useAccount
    ;(useAccount as jest.Mock).mockReturnValue({
      address: mockAddress,
    })
    
    // Mock auth store
    ;(useAuthStore as jest.Mock).mockReturnValue(mockAccessToken)
    
    // Mock WebSocket client
    mockWsClient = {
      connect: jest.fn(),
      disconnect: jest.fn(),
      sendMessage: jest.fn(),
      isConnected: jest.fn().mockReturnValue(true),
      onMessage: jest.fn(),
      onError: jest.fn(),
      onClose: jest.fn(),
      onOpen: jest.fn(),
    }
    
    ;(ChatWebSocketClient as jest.Mock).mockImplementation(() => mockWsClient)
  })
  
  it('should initialize with default values', () => {
    const { result } = renderHook(() => useChat())
    
    expect(result.current.messages).toEqual([])
    expect(result.current.isConnected).toBe(false)
    expect(result.current.isTyping).toBe(false)
  })
  
  it('should create WebSocket client when address is available', () => {
    renderHook(() => useChat())
    
    expect(ChatWebSocketClient).toHaveBeenCalledWith(mockAddress, mockAccessToken)
    expect(mockWsClient.connect).toHaveBeenCalled()
  })
  
  it('should not create WebSocket client without address', () => {
    ;(useAccount as jest.Mock).mockReturnValue({ address: null })
    
    renderHook(() => useChat())
    
    expect(ChatWebSocketClient).not.toHaveBeenCalled()
  })
  
  it('should handle connection open', () => {
    const { result } = renderHook(() => useChat())
    
    // Get the onOpen callback and call it
    const onOpenCallback = mockWsClient.onOpen.mock.calls[0][0]
    act(() => {
      onOpenCallback()
    })
    
    expect(result.current.isConnected).toBe(true)
  })
  
  it('should handle connection close', () => {
    const { result } = renderHook(() => useChat())
    
    // First set connected
    const onOpenCallback = mockWsClient.onOpen.mock.calls[0][0]
    act(() => {
      onOpenCallback()
    })
    
    // Then close connection
    const onCloseCallback = mockWsClient.onClose.mock.calls[0][0]
    act(() => {
      onCloseCallback()
    })
    
    expect(result.current.isConnected).toBe(false)
  })
  
  it('should handle connection error', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
    const { result } = renderHook(() => useChat())
    
    // Set connected first
    const onOpenCallback = mockWsClient.onOpen.mock.calls[0][0]
    act(() => {
      onOpenCallback()
    })
    
    // Trigger error
    const onErrorCallback = mockWsClient.onError.mock.calls[0][0]
    act(() => {
      onErrorCallback(new Error('Test error'))
    })
    
    expect(result.current.isConnected).toBe(false)
    expect(consoleSpy).toHaveBeenCalledWith('Chat WebSocket error:', expect.any(Error))
    
    consoleSpy.mockRestore()
  })
  
  it('should handle incoming AI messages', () => {
    const { result } = renderHook(() => useChat())
    
    const onMessageCallback = mockWsClient.onMessage.mock.calls[0][0]
    
    act(() => {
      onMessageCallback({
        type: 'ai_response',
        content: 'Hello from AI',
        timestamp: '2025-01-27T12:00:00Z',
        metadata: { agent: 'general' }
      })
    })
    
    expect(result.current.messages).toHaveLength(1)
    expect(result.current.messages[0]).toMatchObject({
      content: 'Hello from AI',
      role: 'assistant',
      timestamp: '2025-01-27T12:00:00Z'
    })
    expect(result.current.isTyping).toBe(false)
  })
  
  it('should send user messages', () => {
    const { result } = renderHook(() => useChat())
    
    // Set connected
    const onOpenCallback = mockWsClient.onOpen.mock.calls[0][0]
    act(() => {
      onOpenCallback()
    })
    
    // Send message
    act(() => {
      result.current.sendMessage('Hello AI')
    })
    
    // Check user message was added
    expect(result.current.messages).toHaveLength(1)
    expect(result.current.messages[0]).toMatchObject({
      content: 'Hello AI',
      role: 'user'
    })
    
    // Check message was sent through WebSocket
    expect(mockWsClient.sendMessage).toHaveBeenCalledWith('Hello AI')
    
    // Check typing indicator is shown
    expect(result.current.isTyping).toBe(true)
  })
  
  it('should not send message when not connected', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation()
    mockWsClient.isConnected.mockReturnValue(false)
    
    const { result } = renderHook(() => useChat())
    
    act(() => {
      result.current.sendMessage('Hello AI')
    })
    
    expect(mockWsClient.sendMessage).not.toHaveBeenCalled()
    expect(result.current.messages).toHaveLength(0)
    expect(consoleSpy).toHaveBeenCalledWith('Chat is not connected')
    
    consoleSpy.mockRestore()
  })
  
  it('should clear messages', () => {
    const { result } = renderHook(() => useChat())
    
    // Add some messages
    act(() => {
      result.current.sendMessage('Message 1')
      result.current.sendMessage('Message 2')
    })
    
    expect(result.current.messages).toHaveLength(2)
    
    // Clear messages
    act(() => {
      result.current.clearMessages()
    })
    
    expect(result.current.messages).toHaveLength(0)
  })
  
  it('should disconnect on unmount', () => {
    const { unmount } = renderHook(() => useChat())
    
    unmount()
    
    expect(mockWsClient.disconnect).toHaveBeenCalled()
  })
  
  it('should recreate WebSocket when address changes', () => {
    const { rerender } = renderHook(() => useChat())
    
    expect(ChatWebSocketClient).toHaveBeenCalledTimes(1)
    expect(mockWsClient.connect).toHaveBeenCalledTimes(1)
    
    // Change address
    const newAddress = '0x0000000000000000000000000000000000000001'
    ;(useAccount as jest.Mock).mockReturnValue({ address: newAddress })
    
    rerender()
    
    expect(mockWsClient.disconnect).toHaveBeenCalled()
    expect(ChatWebSocketClient).toHaveBeenCalledTimes(2)
    expect(ChatWebSocketClient).toHaveBeenLastCalledWith(newAddress, mockAccessToken)
  })
  
  it('should handle typing indicator for multiple messages', async () => {
    const { result } = renderHook(() => useChat())
    
    // Set connected
    const onOpenCallback = mockWsClient.onOpen.mock.calls[0][0]
    act(() => {
      onOpenCallback()
    })
    
    // Send message
    act(() => {
      result.current.sendMessage('First question')
    })
    
    expect(result.current.isTyping).toBe(true)
    
    // Receive AI response
    const onMessageCallback = mockWsClient.onMessage.mock.calls[0][0]
    act(() => {
      onMessageCallback({
        type: 'ai_response',
        content: 'First answer',
        timestamp: new Date().toISOString()
      })
    })
    
    expect(result.current.isTyping).toBe(false)
    
    // Send another message
    act(() => {
      result.current.sendMessage('Second question')
    })
    
    expect(result.current.isTyping).toBe(true)
  })
  
  it('should pass access token to WebSocket client', () => {
    renderHook(() => useChat())
    
    expect(ChatWebSocketClient).toHaveBeenCalledWith(mockAddress, mockAccessToken)
  })
  
  it('should work without access token', () => {
    ;(useAuthStore as jest.Mock).mockReturnValue(null)
    
    renderHook(() => useChat())
    
    expect(ChatWebSocketClient).toHaveBeenCalledWith(mockAddress, undefined)
  })
})