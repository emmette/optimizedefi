import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Address } from 'viem'

interface AuthState {
  // State
  isAuthenticated: boolean
  address: Address | null
  chainId: number | null
  issuedAt: string | null
  expirationTime: string | null
  isLoading: boolean
  
  // Actions
  setAuth: (data: {
    address: Address
    chainId: number
    issuedAt: string
    expirationTime?: string
  }) => void
  clearAuth: () => void
  setLoading: (loading: boolean) => void
  checkSession: () => Promise<void>
  login: (message: string, signature: string) => Promise<boolean>
  logout: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      isAuthenticated: false,
      address: null,
      chainId: null,
      issuedAt: null,
      expirationTime: null,
      isLoading: false,
      
      // Set authentication data
      setAuth: (data) => {
        set({
          isAuthenticated: true,
          address: data.address,
          chainId: data.chainId,
          issuedAt: data.issuedAt,
          expirationTime: data.expirationTime || null,
        })
      },
      
      // Clear authentication
      clearAuth: () => {
        set({
          isAuthenticated: false,
          address: null,
          chainId: null,
          issuedAt: null,
          expirationTime: null,
        })
      },
      
      // Set loading state
      setLoading: (loading) => set({ isLoading: loading }),
      
      // Check current session
      checkSession: async () => {
        try {
          set({ isLoading: true })
          const response = await fetch('/api/auth/me')
          const data = await response.json()
          
          if (data.authenticated) {
            get().setAuth({
              address: data.address,
              chainId: data.chainId,
              issuedAt: data.issuedAt,
              expirationTime: data.expirationTime
            })
          } else {
            get().clearAuth()
          }
        } catch (error) {
          console.error('Failed to check session:', error)
          get().clearAuth()
        } finally {
          set({ isLoading: false })
        }
      },
      
      // Login with SIWE
      login: async (message: string, signature: string) => {
        try {
          set({ isLoading: true })
          
          const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, signature })
          })
          
          const data = await response.json()
          
          if (response.ok && data.success) {
            // Fetch session data after successful login
            await get().checkSession()
            return true
          } else {
            console.error('Login failed:', data.error)
            return false
          }
        } catch (error) {
          console.error('Login error:', error)
          return false
        } finally {
          set({ isLoading: false })
        }
      },
      
      // Logout
      logout: async () => {
        try {
          set({ isLoading: true })
          
          await fetch('/api/auth/logout', {
            method: 'POST'
          })
          
          get().clearAuth()
        } catch (error) {
          console.error('Logout error:', error)
        } finally {
          set({ isLoading: false })
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        // Only persist basic auth state, not loading state
        isAuthenticated: state.isAuthenticated,
        address: state.address,
        chainId: state.chainId,
      }),
    }
  )
)

// Hook to check if session is expired
export function useIsSessionExpired() {
  const expirationTime = useAuthStore((state) => state.expirationTime)
  
  if (!expirationTime) return false
  
  const expiration = new Date(expirationTime)
  return expiration < new Date()
}