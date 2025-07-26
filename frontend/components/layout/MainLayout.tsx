'use client'

import { ReactNode, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { ConnectButton } from '@/components/wallet/ConnectButton'
import { 
  LayoutDashboard, 
  TrendingUp, 
  Wallet, 
  RefreshCw, 
  ArrowLeftRight,
  MessageSquare,
  ChevronLeft,
  Settings,
  HelpCircle,
  Bell,
  Menu,
  X
} from 'lucide-react'

interface MainLayoutProps {
  children: ReactNode
}

const navigation = [
  { name: 'Overview', href: '/', icon: LayoutDashboard },
  { name: 'Holdings', href: '/holdings', icon: Wallet },
  { name: 'Analytics', href: '/analytics', icon: TrendingUp },
  { name: 'Swap', href: '/swap', icon: ArrowLeftRight },
  { name: 'Rebalance', href: '/rebalance', icon: RefreshCw },
]

export function MainLayout({ children }: MainLayoutProps) {
  const pathname = usePathname()
  const [isChatCollapsed, setIsChatCollapsed] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  return (
    <div className="flex h-screen bg-background">
      {/* AI Chat Panel - Hidden on mobile, shown on desktop */}
      <div
        className={cn(
          'hidden lg:flex w-[350px] bg-card border-r border-border flex-col transition-all duration-300',
          isChatCollapsed && '-ml-[350px]'
        )}
      >
        <div className="px-5 py-6 border-b border-border flex justify-between items-center">
          <div>
            <h2 className="text-lg font-semibold">AI Assistant</h2>
            <p className="text-sm text-muted-foreground">Portfolio optimization help</p>
          </div>
          <button
            onClick={() => setIsChatCollapsed(!isChatCollapsed)}
            className="p-1 hover:bg-accent rounded-md transition-colors"
          >
            <ChevronLeft className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          <div className="space-y-4">
            <div className="bg-accent/50 p-3 rounded-lg">
              <p className="text-sm">Welcome! I can help you analyze your portfolio, suggest optimizations, and execute trades.</p>
            </div>
          </div>
        </div>

        <div className="px-5 py-4 border-t border-border">
          <div className="mb-4">
            <p className="text-sm font-medium text-muted-foreground mb-3">Suggested Actions</p>
            <div className="flex flex-wrap gap-2">
              <button className="px-3 py-1.5 text-xs bg-secondary hover:bg-primary hover:text-primary-foreground border border-border rounded-md transition-all">
                🔄 Quick Swap
              </button>
              <button className="px-3 py-1.5 text-xs bg-secondary hover:bg-primary hover:text-primary-foreground border border-border rounded-md transition-all">
                ⚡ AI Rebalance
              </button>
              <button className="px-3 py-1.5 text-xs bg-secondary hover:bg-primary hover:text-primary-foreground border border-border rounded-md transition-all">
                📊 Analyze Portfolio
              </button>
              <button className="px-3 py-1.5 text-xs bg-secondary hover:bg-primary hover:text-primary-foreground border border-border rounded-md transition-all">
                💰 Find Yield
              </button>
              <button className="px-3 py-1.5 text-xs bg-secondary hover:bg-primary hover:text-primary-foreground border border-border rounded-md transition-all">
                ⛽ Optimize Gas
              </button>
            </div>
          </div>
          <input
            type="text"
            placeholder="Ask me anything about your portfolio..."
            className="w-full px-4 py-2 bg-background border border-input rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-ring"
          />
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Top Navigation */}
        <header className="h-16 border-b border-border flex items-center justify-between px-4 lg:px-6">
          <div className="flex items-center gap-4 lg:gap-8">
            {/* Mobile menu button */}
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="lg:hidden p-2 hover:bg-accent rounded-md transition-colors"
            >
              {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>

            {/* Project Title */}
            <h1 className="app-title">Optimize DeFi</h1>

            {/* Desktop Navigation */}
            <nav className="hidden lg:flex items-center space-x-1">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-accent text-accent-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.name}
                </Link>
              )
            })}
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <ConnectButton />
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>

      {/* Mobile Navigation Menu */}
      {isMobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 z-50 bg-background/80 backdrop-blur-sm">
          <div className="fixed inset-y-0 left-0 w-64 bg-card border-r border-border p-4">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-semibold">Menu</h2>
              <button
                onClick={() => setIsMobileMenuOpen(false)}
                className="p-2 hover:bg-accent rounded-md transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <nav className="space-y-2">
              {navigation.map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={() => setIsMobileMenuOpen(false)}
                    className={cn(
                      'flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-accent text-accent-foreground'
                        : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
                    )}
                  >
                    <Icon className="h-5 w-5" />
                    {item.name}
                  </Link>
                )
              })}
            </nav>
          </div>
        </div>
      )}

      {/* Floating Chat Toggle (when collapsed) */}
      {isChatCollapsed && (
        <button
          onClick={() => setIsChatCollapsed(false)}
          className="fixed left-4 top-1/2 -translate-y-1/2 p-2 bg-card border border-border rounded-r-md hover:bg-accent transition-colors z-20"
        >
          <MessageSquare className="h-4 w-4" />
        </button>
      )}

      {/* Mobile Chat Button */}
      <button
        className="lg:hidden fixed right-4 bottom-4 p-3 bg-primary text-primary-foreground rounded-full shadow-lg hover:bg-primary/90 transition-colors"
      >
        <MessageSquare className="h-5 w-5" />
      </button>
    </div>
  )
}