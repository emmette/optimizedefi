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
  accessToken: string | null
  eulaAccepted: boolean
  eulaVersion: string | null
  eulaAcceptedAt: string | null
  
  // Actions
  setAuth: (data: {
    address: Address
    chainId: number
    issuedAt: string
    expirationTime?: string
    accessToken?: string
  }) => void
  clearAuth: () => void
  setLoading: (loading: boolean) => void
  checkSession: () => Promise<void>
  login: (message: string, signature: string) => Promise<boolean>
  logout: () => Promise<void>
  setEULAAccepted: (version: string) => void
  checkEULAVersion: (currentVersion: string) => boolean
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
      accessToken: null,
      eulaAccepted: false,
      eulaVersion: null,
      eulaAcceptedAt: null,
      
      // Set authentication data
      setAuth: (data) => {
        set({
          isAuthenticated: true,
          address: data.address,
          chainId: data.chainId,
          issuedAt: data.issuedAt,
          expirationTime: data.expirationTime || null,
          accessToken: data.accessToken || null,
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
          accessToken: null,
        })
      },
      
      // Set loading state
      setLoading: (loading) => set({ isLoading: loading }),
      
      // Check current session
      checkSession: async () => {
        try {
          set({ isLoading: true })
          const accessToken = get().accessToken
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/me`, {
            headers: accessToken ? { 'Authorization': `Bearer ${accessToken}` } : {}
          })
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
          
          // Extract address from SIWE message
          const addressMatch = message.match(/0x[a-fA-F0-9]{40}/)
          const address = addressMatch ? addressMatch[0] : null
          
          if (!address) {
            throw new Error('Invalid SIWE message: no address found')
          }
          
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, signature, address })
          })
          
          const data = await response.json()
          
          if (response.ok && data.access_token) {
            // Store the access token
            set({ accessToken: data.access_token })
            
            // Set authenticated state with the address
            get().setAuth({
              address: address as Address,
              chainId: 1, // Default to mainnet, will be updated on next check
              issuedAt: new Date().toISOString(),
              accessToken: data.access_token
            })
            
            return true
          } else {
            console.error('Login failed:', data.error || data.detail)
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
          
          const accessToken = get().accessToken
          await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/logout`, {
            method: 'POST',
            headers: accessToken ? { 'Authorization': `Bearer ${accessToken}` } : {}
          })
          
          get().clearAuth()
        } catch (error) {
          console.error('Logout error:', error)
        } finally {
          set({ isLoading: false })
        }
      },
      
      // Set EULA accepted
      setEULAAccepted: (version: string) => {
        set({
          eulaAccepted: true,
          eulaVersion: version,
          eulaAcceptedAt: new Date().toISOString()
        })
      },
      
      // Check if current EULA version is accepted
      checkEULAVersion: (currentVersion: string) => {
        const state = get()
        return state.eulaAccepted && state.eulaVersion === currentVersion
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        // Only persist basic auth state, not loading state
        isAuthenticated: state.isAuthenticated,
        address: state.address,
        chainId: state.chainId,
        accessToken: state.accessToken,
        eulaAccepted: state.eulaAccepted,
        eulaVersion: state.eulaVersion,
        eulaAcceptedAt: state.eulaAcceptedAt,
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