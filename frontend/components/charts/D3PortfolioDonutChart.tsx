'use client'

import { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import { Card } from '@/components/ui/Card'
import { Token } from '@/types/portfolio'
import { ChartExportButton } from './ChartExportButton'

interface D3PortfolioDonutChartProps {
  tokens: Token[]
  totalValue: number
}

export function D3PortfolioDonutChart({ tokens, totalValue }: D3PortfolioDonutChartProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const svg = svgRef.current
    if (!svg || tokens.length === 0) return

    // Clear previous chart
    d3.select(svg).selectAll('*').remove()

    // Set dimensions
    const width = 400
    const height = 400
    const margin = 40
    const radius = Math.min(width, height) / 2 - margin
    const innerRadius = radius * 0.6

    // Create SVG
    const svgSelection = d3.select(svg)
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', `0 0 ${width} ${height}`)
      .attr('preserveAspectRatio', 'xMidYMid meet')

    const g = svgSelection.append('g')
      .attr('transform', `translate(${width / 2}, ${height / 2})`)

    // Prepare data - aggregate by symbol and take top 8
    const aggregatedTokens = d3.rollup(
      tokens,
      v => d3.sum(v, d => d.balance_usd),
      d => d.symbol
    )

    const topTokens = Array.from(aggregatedTokens.entries())
      .map(([symbol, value]) => ({ symbol, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 8)

    // Add "Other" category if needed
    const topValue = d3.sum(topTokens, d => d.value)
    if (totalValue > topValue) {
      topTokens.push({ symbol: 'Other', value: totalValue - topValue })
    }

    // Create color scale
    const color = d3.scaleOrdinal<string>()
      .domain(topTokens.map(d => d.symbol))
      .range(d3.schemeSet3)

    // Create pie generator
    const pie = d3.pie<{ symbol: string; value: number }>()
      .value(d => d.value)
      .sort(null)

    // Create arc generator
    const arc = d3.arc<d3.PieArcDatum<{ symbol: string; value: number }>>()
      .innerRadius(innerRadius)
      .outerRadius(radius)

    // Create label arc
    const labelArc = d3.arc<d3.PieArcDatum<{ symbol: string; value: number }>>()
      .innerRadius(radius * 0.8)
      .outerRadius(radius * 0.8)

    // Draw pie slices
    const slices = g.selectAll('.slice')
      .data(pie(topTokens))
      .enter()
      .append('g')
      .attr('class', 'slice')

    // Add paths with animation
    slices.append('path')
      .attr('d', arc)
      .attr('fill', d => color(d.data.symbol))
      .attr('stroke', 'white')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('mouseover', function(event, d) {
        // Highlight slice
        d3.select(this)
          .transition()
          .duration(200)
          .attr('transform', function(d) {
            const [x, y] = arc.centroid(d)
            return `translate(${x * 0.1}, ${y * 0.1})`
          })
          .attr('opacity', 0.8)

        // Show tooltip
        if (tooltipRef.current) {
          const percentage = ((d.data.value / totalValue) * 100).toFixed(1)
          tooltipRef.current.innerHTML = `
            <div class="font-semibold">${d.data.symbol}</div>
            <div class="text-sm text-muted-foreground">
              $${d.data.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
            </div>
            <div class="text-sm text-muted-foreground">${percentage}%</div>
          `
          tooltipRef.current.style.display = 'block'
          tooltipRef.current.style.left = `${event.pageX + 10}px`
          tooltipRef.current.style.top = `${event.pageY - 10}px`
        }
      })
      .on('mouseout', function() {
        // Reset slice
        d3.select(this)
          .transition()
          .duration(200)
          .attr('transform', 'translate(0, 0)')
          .attr('opacity', 1)

        // Hide tooltip
        if (tooltipRef.current) {
          tooltipRef.current.style.display = 'none'
        }
      })
      .transition()
      .duration(800)
      .attrTween('d', function(d) {
        const interpolate = d3.interpolate({ startAngle: 0, endAngle: 0 }, d)
        return function(t) {
          return arc(interpolate(t)) || ''
        }
      })

    // Add labels for larger slices
    slices.append('text')
      .attr('transform', d => `translate(${labelArc.centroid(d)})`)
      .attr('text-anchor', 'middle')
      .style('fill', 'white')
      .style('font-size', '12px')
      .style('font-weight', 'bold')
      .style('pointer-events', 'none')
      .text(d => {
        const percentage = ((d.data.value / totalValue) * 100)
        return percentage > 5 ? d.data.symbol : ''
      })
      .style('opacity', 0)
      .transition()
      .delay(800)
      .duration(400)
      .style('opacity', 1)

    // Add center text
    const centerText = g.append('g')
      .attr('class', 'center-text')

    centerText.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '-0.2em')
      .style('font-size', '14px')
      .style('fill', 'hsl(var(--muted-foreground))')
      .text('Total Value')

    centerText.append('text')
      .attr('text-anchor', 'middle')
      .attr('dy', '1.2em')
      .style('font-size', '24px')
      .style('font-weight', 'bold')
      .style('fill', 'hsl(var(--foreground))')
      .text(`$${totalValue.toLocaleString(undefined, { maximumFractionDigits: 0 })}`)

    // Cleanup
    return () => {
      d3.select(svg).selectAll('*').remove()
    }
  }, [tokens, totalValue])

  return (
    <Card className="p-6 relative">
      <ChartExportButton svgRef={svgRef} filename="portfolio-distribution" />
      <h3 className="text-lg font-semibold mb-4">Portfolio Distribution</h3>
      <div className="relative flex justify-center">
        <svg ref={svgRef} className="w-full max-w-md" />
        <div
          ref={tooltipRef}
          className="absolute z-10 p-2 bg-background border border-border rounded-lg shadow-lg"
          style={{ display: 'none', pointerEvents: 'none' }}
        />
      </div>
    </Card>
  )
}