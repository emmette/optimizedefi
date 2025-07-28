import { useAccount, useSignMessage, useChainId } from 'wagmi'
import { useAuthStore } from '@/store/authStore'
import { generateSiweMessage } from '@/lib/auth/siwe'
import { useState, useCallback } from 'react'

export function useSiwe() {
  const { address } = useAccount()
  const chainId = useChainId()
  const { signMessageAsync } = useSignMessage()
  const { login, logout, isAuthenticated, isLoading } = useAuthStore()
  const [error, setError] = useState<string | null>(null)

  const signIn = useCallback(async () => {
    if (!address) {
      setError('No wallet connected')
      return false
    }

    try {
      setError(null)
      
      // Get nonce from backend
      const nonceResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/nonce`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address })
      })
      const { nonce } = await nonceResponse.json()
      
      if (!nonce) {
        throw new Error('Failed to get nonce')
      }
      
      // Generate SIWE message
      const message = generateSiweMessage(address, {
        domain: window.location.hostname,
        uri: window.location.origin,
        chainId,
        nonce,
        statement: 'Sign in to OptimizeDeFi to access your personalized DeFi dashboard'
      })
      
      // Request signature from wallet
      const signature = await signMessageAsync({ message })
      
      // Send to backend for verification
      const success = await login(message, signature)
      
      if (!success) {
        throw new Error('Authentication failed')
      }
      
      return true
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to sign in'
      setError(errorMessage)
      console.error('SIWE sign in error:', err)
      return false
    }
  }, [address, chainId, signMessageAsync, login])

  const signOut = useCallback(async () => {
    try {
      setError(null)
      await logout()
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to sign out'
      setError(errorMessage)
      console.error('SIWE sign out error:', err)
    }
  }, [logout])

  return {
    signIn,
    signOut,
    isAuthenticated,
    isLoading,
    error,
    address
  }
}