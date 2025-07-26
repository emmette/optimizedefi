'use client'

import { useAccount, useConnect, useDisconnect, useEnsName } from 'wagmi'
import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/Card'
import { Wallet, ChevronDown, LogOut, Copy, ExternalLink, Shield } from 'lucide-react'
import { useSiwe } from '@/hooks/useSiwe'
import { useAuthStore } from '@/store/authStore'

export function ConnectButton() {
  const { address, isConnected, chain } = useAccount()
  const { connect, connectors, isPending } = useConnect()
  const { disconnect } = useDisconnect()
  const { data: ensName } = useEnsName({ address })
  const [showConnectors, setShowConnectors] = useState(false)
  const [showAccountMenu, setShowAccountMenu] = useState(false)
  
  // SIWE authentication
  const { signIn, signOut, isAuthenticated, isLoading: isAuthLoading } = useSiwe()
  const checkSession = useAuthStore(state => state.checkSession)
  
  // Check session on mount
  useEffect(() => {
    if (isConnected) {
      checkSession()
    }
  }, [isConnected, checkSession])
  
  // Auto-prompt for SIWE after wallet connection
  useEffect(() => {
    if (isConnected && !isAuthenticated && !isAuthLoading) {
      // Small delay to ensure wallet is fully connected
      const timer = setTimeout(() => {
        signIn()
      }, 500)
      return () => clearTimeout(timer)
    }
  }, [isConnected, isAuthenticated, isAuthLoading, signIn])

  const formatAddress = (addr: string) => {
    return `${addr.slice(0, 6)}...${addr.slice(-4)}`
  }

  const copyAddress = () => {
    if (address) {
      navigator.clipboard.writeText(address)
      // In production, show a toast notification
    }
  }

  if (isConnected && address) {
    return (
      <div className="relative">
        <button
          onClick={() => setShowAccountMenu(!showAccountMenu)}
          className="flex items-center gap-3 px-4 py-2 bg-background/50 border border-border rounded-lg hover:bg-accent transition-colors"
        >
          <div className="flex items-center gap-2">
            <div className="h-2 w-2 bg-green-500 rounded-full"></div>
            {isAuthenticated && <Shield className="h-4 w-4 text-green-500" />}
          </div>
          <span className="text-sm font-medium">
            {ensName || formatAddress(address)}
          </span>
          <ChevronDown className="h-4 w-4" />
        </button>

        {showAccountMenu && (
          <>
            <div
              className="fixed inset-0 z-40"
              onClick={() => setShowAccountMenu(false)}
            />
            <Card className="absolute right-0 top-full mt-2 w-64 p-4 z-50 space-y-3">
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Connected to</p>
                <p className="font-medium">{chain?.name || 'Unknown Chain'}</p>
              </div>
              
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Address</p>
                <div className="flex items-center gap-2">
                  <p className="font-mono text-sm">{formatAddress(address)}</p>
                  <button
                    onClick={copyAddress}
                    className="p-1 hover:bg-accent rounded transition-colors"
                  >
                    <Copy className="h-3 w-3" />
                  </button>
                  <a
                    href={`https://etherscan.io/address/${address}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-1 hover:bg-accent rounded transition-colors"
                  >
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              </div>

              {!isAuthenticated && (
                <button
                  onClick={async () => {
                    await signIn()
                    setShowAccountMenu(false)
                  }}
                  className="w-full flex items-center justify-center gap-2 py-2 bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-colors mb-2"
                  disabled={isAuthLoading}
                >
                  <Shield className="h-4 w-4" />
                  {isAuthLoading ? 'Signing...' : 'Sign In'}
                </button>
              )}

              <button
                onClick={async () => {
                  if (isAuthenticated) {
                    await signOut()
                  }
                  disconnect()
                  setShowAccountMenu(false)
                }}
                className="w-full flex items-center justify-center gap-2 py-2 bg-red-500/10 text-red-500 rounded-lg hover:bg-red-500/20 transition-colors"
              >
                <LogOut className="h-4 w-4" />
                Disconnect
              </button>
            </Card>
          </>
        )}
      </div>
    )
  }

  return (
    <div className="relative">
      <button
        onClick={() => setShowConnectors(!showConnectors)}
        disabled={isPending}
        className="flex items-center gap-2 px-5 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors text-sm font-medium disabled:opacity-50"
      >
        <Wallet className="h-4 w-4" />
        {isPending ? 'Connecting...' : 'Connect Wallet'}
      </button>

      {showConnectors && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setShowConnectors(false)}
          />
          <Card className="absolute right-0 top-full mt-2 w-64 p-4 z-50">
            <h3 className="font-medium mb-3">Connect a wallet</h3>
            <div className="space-y-2">
              {connectors.map((connector) => (
                <button
                  key={connector.id}
                  onClick={() => {
                    connect({ connector })
                    setShowConnectors(false)
                  }}
                  className="w-full flex items-center gap-3 p-3 bg-secondary hover:bg-secondary/80 rounded-lg transition-colors text-left"
                >
                  <Wallet className="h-5 w-5" />
                  <span className="font-medium">{connector.name}</span>
                </button>
              ))}
            </div>
          </Card>
        </>
      )}
    </div>
  )
}