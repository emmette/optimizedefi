import { Card } from '@/components/ui/card'

export function HoldingsPageSkeleton() {
  return (
    <div className="px-8 py-6 space-y-6">
      {/* Header */}
      <div>
        <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-32 animate-pulse mb-2" />
        <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-64 animate-pulse" />
      </div>

      {/* Chain Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-20 animate-pulse" />
              <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-16 animate-pulse" />
            </div>
            <div className="h-7 bg-gray-200 dark:bg-gray-700 rounded w-32 animate-pulse mb-2" />
            <div className="mt-2">
              <div className="flex justify-between text-sm mb-1">
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-20 animate-pulse" />
                <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-12 animate-pulse" />
              </div>
              <div className="w-full bg-background rounded-full h-2">
                <div className="bg-gray-200 dark:bg-gray-700 h-2 rounded-full animate-pulse" style={{ width: '60%' }} />
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Controls */}
      <Card className="p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 h-10 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
          <div className="w-32 h-10 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
          <div className="w-32 h-10 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse" />
        </div>
      </Card>

      {/* Holdings Table */}
      <Card className="overflow-hidden">
        <div className="bg-background border-b border-border px-6 py-4">
          <div className="flex justify-between">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16 animate-pulse" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16 animate-pulse" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16 animate-pulse" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16 animate-pulse" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16 animate-pulse" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20 animate-pulse" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20 animate-pulse" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16 animate-pulse" />
          </div>
        </div>
        {[...Array(5)].map((_, i) => (
          <div key={i} className="border-b border-border px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gray-200 dark:bg-gray-700 rounded-full animate-pulse" />
                <div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16 animate-pulse mb-1" />
                  <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-24 animate-pulse" />
                </div>
              </div>
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20 animate-pulse" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24 animate-pulse" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-20 animate-pulse" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24 animate-pulse" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-16 animate-pulse" />
              <div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-12 animate-pulse mb-1" />
                <div className="w-20 bg-background rounded-full h-1.5">
                  <div className="bg-gray-200 dark:bg-gray-700 h-1.5 rounded-full animate-pulse" style={{ width: '40%' }} />
                </div>
              </div>
              <div className="flex gap-2">
                <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-16 animate-pulse" />
                <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-16 animate-pulse" />
              </div>
            </div>
          </div>
        ))}
      </Card>

      {/* Summary */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-40 animate-pulse mb-2" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-48 animate-pulse" />
          </div>
          <div className="text-right">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-32 animate-pulse mb-2" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-36 animate-pulse" />
          </div>
        </div>
      </Card>
    </div>
  )
}