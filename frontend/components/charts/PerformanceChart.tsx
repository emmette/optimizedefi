'use client'

interface PerformanceData {
  date: string
  value: number
}

interface PerformanceChartProps {
  data: PerformanceData[]
}

export function PerformanceChart({ data }: PerformanceChartProps) {
  // Calculate percentage change
  const startValue = data[0]?.value || 0
  const endValue = data[data.length - 1]?.value || 0
  const percentageChange = ((endValue - startValue) / startValue) * 100
  const isPositive = percentageChange > 0

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-2xl font-bold">${endValue.toLocaleString()}</p>
          <p className={`text-sm ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
            {isPositive ? '+' : ''}{percentageChange.toFixed(2)}% from start
          </p>
        </div>
      </div>

      {/* Line chart placeholder - will be replaced with D3.js */}
      <div className="h-48 relative">
        {/* Y-axis labels */}
        <div className="absolute left-0 top-0 bottom-0 flex flex-col justify-between text-xs text-muted-foreground">
          <span>${(endValue * 1.1 / 1000).toFixed(0)}k</span>
          <span>${(endValue / 1000).toFixed(0)}k</span>
          <span>${(endValue * 0.9 / 1000).toFixed(0)}k</span>
        </div>

        {/* Chart area */}
        <div className="ml-12 h-full border-l border-b border-border relative">
          {/* Placeholder line */}
          <svg className="absolute inset-0 w-full h-full">
            <polyline
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="text-primary"
              points={data.map((d, i) => {
                const x = (i / (data.length - 1)) * 100
                const y = 100 - ((d.value - startValue) / (endValue - startValue)) * 100
                return `${x},${y}`
              }).join(' ')}
            />
          </svg>
        </div>

        {/* X-axis labels */}
        <div className="ml-12 mt-2 flex justify-between text-xs text-muted-foreground">
          {data.filter((_, i) => i % 2 === 0).map((d) => (
            <span key={d.date}>{new Date(d.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
          ))}
        </div>
      </div>
    </div>
  )
}