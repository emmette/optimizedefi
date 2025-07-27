// 1inch API client with rate limiting and error handling

interface RateLimitState {
  requests: number
  resetTime: number
}

export class OneInchAPIError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public response?: unknown
  ) {
    super(message)
    this.name = 'OneInchAPIError'
  }
}

export class OneInchAPIClient {
  private baseURL: string
  private apiKey: string
  private rateLimitState: Map<string, RateLimitState> = new Map()
  private readonly MAX_REQUESTS_PER_MINUTE = 30
  private readonly RATE_LIMIT_WINDOW = 60000 // 1 minute in ms
  private initError: Error | null = null

  constructor(apiKey?: string) {
    // In production, this would come from environment variables
    this.apiKey = apiKey || process.env.NEXT_PUBLIC_1INCH_API_KEY || ''
    this.baseURL = 'https://api.1inch.dev'
    
    // Check if API key is configured
    if (!this.apiKey) {
      this.initError = new OneInchAPIError(
        '1inch API key not configured. Please add NEXT_PUBLIC_1INCH_API_KEY to your .env.local file. ' +
        'You can get an API key from https://portal.1inch.dev/'
      )
    }
  }

  private checkInitialization(): void {
    if (this.initError) {
      throw this.initError
    }
  }

  private checkRateLimit(endpoint: string): void {
    const now = Date.now()
    const state = this.rateLimitState.get(endpoint)

    if (!state || now > state.resetTime) {
      // Reset rate limit window
      this.rateLimitState.set(endpoint, {
        requests: 1,
        resetTime: now + this.RATE_LIMIT_WINDOW
      })
      return
    }

    if (state.requests >= this.MAX_REQUESTS_PER_MINUTE) {
      const waitTime = Math.ceil((state.resetTime - now) / 1000)
      throw new OneInchAPIError(
        `Rate limit exceeded. Please wait ${waitTime} seconds.`,
        429
      )
    }

    state.requests++
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    // Check if client was initialized properly
    this.checkInitialization()
    
    this.checkRateLimit(endpoint)

    const url = `${this.baseURL}${endpoint}`
    const headers = {
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      ...options.headers
    }

    // Add API key if available
    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => null)
        throw new OneInchAPIError(
          errorData?.message || `HTTP error! status: ${response.status}`,
          response.status,
          errorData
        )
      }

      const data = await response.json()
      return data as T
    } catch (error) {
      if (error instanceof OneInchAPIError) {
        throw error
      }

      throw new OneInchAPIError(
        error instanceof Error ? error.message : 'Unknown error occurred'
      )
    }
  }

  // Helper method for GET requests
  async get<T>(endpoint: string, params?: Record<string, string | number | boolean>): Promise<T> {
    const queryString = params
      ? '?' + new URLSearchParams(params).toString()
      : ''
    
    return this.request<T>(`${endpoint}${queryString}`, {
      method: 'GET'
    })
  }

  // Helper method for POST requests
  async post<T>(
    endpoint: string,
    body?: unknown,
    params?: Record<string, string | number | boolean>
  ): Promise<T> {
    const queryString = params
      ? '?' + new URLSearchParams(params).toString()
      : ''
    
    return this.request<T>(`${endpoint}${queryString}`, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined
    })
  }

  // Get supported chains
  async getSupportedChains() {
    // 1inch supports multiple chains
    return {
      ethereum: 1,
      polygon: 137,
      optimism: 10,
      arbitrum: 42161,
      avalanche: 43114,
      bsc: 56,
      gnosis: 100,
      fantom: 250,
      base: 8453,
      aurora: 1313161554,
      klaytn: 8217
    }
  }

  // Check API health
  async checkHealth(): Promise<boolean> {
    try {
      // Try to fetch supported tokens for Ethereum as a health check
      await this.get('/swap/v6.0/1/tokens')
      return true
    } catch {
      return false
    }
  }
}

// Lazy initialization for the client
let _clientInstance: OneInchAPIClient | null = null
let _clientError: Error | null = null

export function getOneInchClient(): OneInchAPIClient | null {
  // Return cached instance if available
  if (_clientInstance !== null) {
    return _clientInstance
  }
  
  // Return null if we've already tried and failed
  if (_clientError !== null) {
    return null
  }
  
  try {
    _clientInstance = new OneInchAPIClient()
    return _clientInstance
  } catch (error) {
    _clientError = error as Error
    console.warn('Failed to initialize 1inch client:', error)
    return null
  }
}