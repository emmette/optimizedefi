'use client'

import { ReactNode, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
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
  Bell
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

  return (
    <div className="flex h-screen bg-background">
      {/* AI Chat Panel */}
      <div
        className={cn(
          'w-[350px] bg-card border-r border-border flex flex-col transition-all duration-300',
          isChatCollapsed && '-ml-[350px]'
        )}
      >
        <div className="p-5 border-b border-border flex justify-between items-center">
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

        <div className="flex-1 overflow-y-auto p-4">
          <div className="space-y-4">
            <div className="bg-accent/50 p-3 rounded-lg">
              <p className="text-sm">Welcome! I can help you analyze your portfolio, suggest optimizations, and execute trades.</p>
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-border">
          <div className="mb-4">
            <p className="text-sm font-medium text-muted-foreground mb-3">Suggested Actions</p>
            <div className="flex flex-wrap gap-2">
              <button className="px-3 py-1.5 text-xs bg-primary/10 hover:bg-primary/20 rounded-md transition-colors">
                Analyze portfolio
              </button>
              <button className="px-3 py-1.5 text-xs bg-primary/10 hover:bg-primary/20 rounded-md transition-colors">
                Find opportunities
              </button>
              <button className="px-3 py-1.5 text-xs bg-primary/10 hover:bg-primary/20 rounded-md transition-colors">
                Risk assessment
              </button>
            </div>
          </div>
          <div className="relative">
            <input
              type="text"
              placeholder="Ask me anything about your portfolio..."
              className="w-full px-4 py-2 pr-10 bg-background border border-input rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <button className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 hover:bg-accent rounded-md transition-colors">
              <MessageSquare className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Top Navigation */}
        <header className="h-16 border-b border-border flex items-center justify-between px-6">
          <nav className="flex items-center space-x-1">
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

          <div className="flex items-center gap-4">
            <button className="p-2 hover:bg-accent rounded-md transition-colors">
              <Bell className="h-5 w-5" />
            </button>
            <button className="p-2 hover:bg-accent rounded-md transition-colors">
              <HelpCircle className="h-5 w-5" />
            </button>
            <button className="p-2 hover:bg-accent rounded-md transition-colors">
              <Settings className="h-5 w-5" />
            </button>
            <div className="flex items-center gap-2 px-3 py-1.5 bg-accent rounded-md">
              <div className="h-2 w-2 bg-green-500 rounded-full"></div>
              <span className="text-sm font-medium">0x742d...3456</span>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>

      {/* Floating Chat Toggle (when collapsed) */}
      {isChatCollapsed && (
        <button
          onClick={() => setIsChatCollapsed(false)}
          className="fixed left-4 bottom-4 p-3 bg-primary text-primary-foreground rounded-full shadow-lg hover:bg-primary/90 transition-colors"
        >
          <MessageSquare className="h-5 w-5" />
        </button>
      )}
    </div>
  )
}