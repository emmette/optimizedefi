'use client'

interface ChainData {
  name: string
  value: number
  percentage: number
}

interface PortfolioChartProps {
  data: ChainData[]
}

export function PortfolioChart({ data }: PortfolioChartProps) {
  // Calculate total for percentage calculation
  const total = data.reduce((sum, item) => sum + item.value, 0)
  
  // Define colors for each chain
  const chainColors: Record<string, string> = {
    Ethereum: '#627EEA',
    Polygon: '#8247E5',
    Optimism: '#FF0420',
    Arbitrum: '#28A0F0',
  }

  return (
    <div className="space-y-4">
      {/* Donut chart placeholder - will be replaced with D3.js */}
      <div className="relative h-48 flex items-center justify-center">
        <div className="text-center">
          <p className="text-2xl font-bold">${total.toLocaleString()}</p>
          <p className="text-sm text-muted-foreground">Total Value</p>
        </div>
        {/* Placeholder circle */}
        <svg className="absolute inset-0 w-full h-full">
          <circle
            cx="50%"
            cy="50%"
            r="70"
            fill="none"
            stroke="currentColor"
            strokeWidth="20"
            className="text-border"
          />
        </svg>
      </div>

      {/* Legend */}
      <div className="space-y-2">
        {data.map((chain) => (
          <div key={chain.name} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: chainColors[chain.name] || '#666' }}
              />
              <span className="text-sm">{chain.name}</span>
            </div>
            <div className="text-right">
              <span className="text-sm font-medium">${chain.value.toLocaleString()}</span>
              <span className="text-sm text-muted-foreground ml-2">{chain.percentage}%</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}