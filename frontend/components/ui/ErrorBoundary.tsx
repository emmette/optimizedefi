'use client'

import React from 'react'
import { Card } from './card'
import { AlertCircle, RefreshCw } from 'lucide-react'

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

interface ErrorBoundaryProps {
  children: React.ReactNode
  fallback?: React.ComponentType<{ error: Error; reset: () => void }>
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo)
  }

  reset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        const FallbackComponent = this.props.fallback
        return <FallbackComponent error={this.state.error} reset={this.reset} />
      }

      return (
        <div className="flex items-center justify-center min-h-[400px] p-8">
          <Card className="max-w-md w-full p-6 space-y-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-8 w-8 text-red-500" />
              <h2 className="text-xl font-semibold">Something went wrong</h2>
            </div>
            <p className="text-muted-foreground">
              {this.state.error.message || 'An unexpected error occurred'}
            </p>
            <button
              onClick={this.reset}
              className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
            >
              <RefreshCw className="h-4 w-4" />
              Try again
            </button>
          </Card>
        </div>
      )
    }

    return this.props.children
  }
}

// Error fallback component for portfolio-specific errors
export function PortfolioErrorFallback({ error, reset }: { error: Error; reset: () => void }) {
  const is1inchError = error.message.includes('1inch') || error.message.includes('API')
  
  return (
    <div className="flex items-center justify-center min-h-[400px] p-8">
      <Card className="max-w-md w-full p-6 space-y-4">
        <div className="flex items-center gap-3">
          <AlertCircle className="h-8 w-8 text-orange-500" />
          <h2 className="text-xl font-semibold">
            {is1inchError ? 'Unable to fetch portfolio data' : 'Something went wrong'}
          </h2>
        </div>
        <div className="space-y-2">
          <p className="text-muted-foreground">
            {is1inchError 
              ? 'We\'re having trouble connecting to the portfolio service. This might be due to:'
              : error.message || 'An unexpected error occurred'
            }
          </p>
          {is1inchError && (
            <ul className="text-sm text-muted-foreground space-y-1 ml-4">
              <li>• API rate limits</li>
              <li>• Network connectivity issues</li>
              <li>• Service temporarily unavailable</li>
            </ul>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={reset}
            className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            <RefreshCw className="h-4 w-4" />
            Try again
          </button>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors"
          >
            Refresh page
          </button>
        </div>
      </Card>
    </div>
  )
}