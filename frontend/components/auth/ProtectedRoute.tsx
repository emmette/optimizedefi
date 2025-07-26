'use client'

import { useEffect } from 'react'
import { useAuthStore } from '@/store/authStore'
import { useAccount } from 'wagmi'
import { useRouter } from 'next/navigation'
import { Card } from '@/components/ui/Card'
import { Shield, LogIn } from 'lucide-react'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireAuth?: boolean
  fallback?: React.ReactNode
}

export function ProtectedRoute({ 
  children, 
  requireAuth = true,
  fallback 
}: ProtectedRouteProps) {
  const { isAuthenticated, checkSession, isLoading } = useAuthStore()
  const { isConnected } = useAccount()
  const router = useRouter()

  useEffect(() => {
    // Check session on mount
    checkSession()
  }, [checkSession])

  // Loading state
  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Checking authentication...</p>
        </div>
      </div>
    )
  }

  // Not connected
  if (!isConnected) {
    return fallback || (
      <div className="flex h-full items-center justify-center">
        <Card className="p-8 text-center max-w-md">
          <Shield className="h-16 w-16 text-primary mx-auto mb-4" />
          <h2 className="text-2xl font-semibold mb-2">Connect Your Wallet</h2>
          <p className="text-muted-foreground mb-6">
            Please connect your wallet to access this feature
          </p>
        </Card>
      </div>
    )
  }

  // Connected but not authenticated
  if (requireAuth && !isAuthenticated) {
    return fallback || (
      <div className="flex h-full items-center justify-center">
        <Card className="p-8 text-center max-w-md">
          <LogIn className="h-16 w-16 text-primary mx-auto mb-4" />
          <h2 className="text-2xl font-semibold mb-2">Sign In Required</h2>
          <p className="text-muted-foreground mb-6">
            Please sign in with your wallet to access this feature
          </p>
          <button
            onClick={() => router.push('/')}
            className="px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
          >
            Go to Dashboard
          </button>
        </Card>
      </div>
    )
  }

  // Authenticated or auth not required
  return <>{children}</>
}