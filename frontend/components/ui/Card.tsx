import { forwardRef, HTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export type CardProps = HTMLAttributes<HTMLDivElement>

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={cn(
          'rounded-xl border border-border bg-card text-card-foreground shadow-sm',
          className
        )}
        {...props}
      />
    )
  }
)

Card.displayName = 'Card'

export { Card }