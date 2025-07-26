'use client'

import { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import { Card } from '@/components/ui/Card'
import { ChartExportButton } from './ChartExportButton'

interface ChainData {
  chainId: number
  name: string
  value: number
  percentage: number
}

interface D3ChainDistributionChartProps {
  data: ChainData[]
}

const chainColors: Record<number, string> = {
  1: '#627EEA',     // Ethereum - Blue
  137: '#8247E5',   // Polygon - Purple
  10: '#FF0420',    // Optimism - Red
  42161: '#2D374B', // Arbitrum - Dark Blue
  56: '#F3BA2F',    // BSC - Yellow
  43114: '#E84142', // Avalanche - Red
}

export function D3ChainDistributionChart({ data }: D3ChainDistributionChartProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!svgRef.current || data.length === 0) return

    // Clear previous chart
    d3.select(svgRef.current).selectAll('*').remove()

    // Set dimensions
    const margin = { top: 20, right: 30, bottom: 60, left: 60 }
    const width = svgRef.current.clientWidth - margin.left - margin.right
    const height = 300 - margin.top - margin.bottom

    // Create SVG
    const svg = d3.select(svgRef.current)
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Create scales
    const xScale = d3.scaleBand()
      .domain(data.map(d => d.name))
      .range([0, width])
      .padding(0.2)

    const yScale = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.value) as number * 1.1])
      .range([height, 0])

    // Create axes
    const xAxis = d3.axisBottom(xScale)
    const yAxis = d3.axisLeft(yScale)
      .tickFormat(d => `$${(d as number).toLocaleString()}`)
      .ticks(5)

    // Add X axis
    g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${height})`)
      .call(xAxis)
      .selectAll('text')
      .style('text-anchor', 'end')
      .attr('dx', '-.8em')
      .attr('dy', '.15em')
      .attr('transform', 'rotate(-45)')

    // Add Y axis
    g.append('g')
      .attr('class', 'y-axis')
      .call(yAxis)

    // Style axes
    g.selectAll('.domain, .tick line')
      .style('stroke', 'hsl(var(--border))')
    g.selectAll('.tick text')
      .style('fill', 'hsl(var(--muted-foreground))')

    // Add grid lines
    g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yScale)
        .tickSize(-width)
        .tickFormat(() => '')
      )
      .style('stroke-dasharray', '3,3')
      .style('opacity', 0.3)

    // Create bars
    const bars = g.selectAll('.bar')
      .data(data)
      .enter().append('rect')
      .attr('class', 'bar')
      .attr('x', d => xScale(d.name) as number)
      .attr('width', xScale.bandwidth())
      .attr('y', height)
      .attr('height', 0)
      .attr('fill', d => chainColors[d.chainId] || '#666')
      .style('cursor', 'pointer')

    // Animate bars
    bars.transition()
      .duration(800)
      .delay((d, i) => i * 100)
      .attr('y', d => yScale(d.value))
      .attr('height', d => height - yScale(d.value))

    // Add value labels on top of bars
    const labels = g.selectAll('.label')
      .data(data)
      .enter().append('text')
      .attr('class', 'label')
      .attr('x', d => (xScale(d.name) as number) + xScale.bandwidth() / 2)
      .attr('y', d => yScale(d.value) - 5)
      .attr('text-anchor', 'middle')
      .style('fill', 'hsl(var(--foreground))')
      .style('font-size', '12px')
      .style('font-weight', 'bold')
      .style('opacity', 0)
      .text(d => `${d.percentage.toFixed(1)}%`)

    // Animate labels
    labels.transition()
      .duration(300)
      .delay((d, i) => 800 + i * 100)
      .style('opacity', 1)

    // Add hover effects
    bars
      .on('mouseover', function(event, d) {
        // Highlight bar
        d3.select(this)
          .transition()
          .duration(200)
          .attr('opacity', 0.8)

        // Show tooltip
        if (tooltipRef.current) {
          tooltipRef.current.innerHTML = `
            <div class="font-semibold">${d.name}</div>
            <div class="text-sm text-muted-foreground">
              Value: $${d.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
            </div>
            <div class="text-sm text-muted-foreground">
              ${d.percentage.toFixed(1)}% of portfolio
            </div>
          `
          tooltipRef.current.style.display = 'block'
          tooltipRef.current.style.left = `${event.pageX + 10}px`
          tooltipRef.current.style.top = `${event.pageY - 10}px`
        }
      })
      .on('mouseout', function() {
        // Reset bar
        d3.select(this)
          .transition()
          .duration(200)
          .attr('opacity', 1)

        // Hide tooltip
        if (tooltipRef.current) {
          tooltipRef.current.style.display = 'none'
        }
      })

    // Add click interaction to toggle between value and percentage view
    let showPercentage = false
    
    bars.on('click', function() {
      showPercentage = !showPercentage
      
      if (showPercentage) {
        // Transition to percentage scale
        const percentScale = d3.scaleLinear()
          .domain([0, 100])
          .range([height, 0])

        bars.transition()
          .duration(500)
          .attr('y', d => percentScale(d.percentage))
          .attr('height', d => height - percentScale(d.percentage))

        labels.transition()
          .duration(500)
          .attr('y', d => percentScale(d.percentage) - 5)
          .text(d => `${d.percentage.toFixed(1)}%`)

        g.select('.y-axis')
          .transition()
          .duration(500)
          .call(d3.axisLeft(percentScale).tickFormat(d => `${d}%`))
      } else {
        // Transition back to value scale
        bars.transition()
          .duration(500)
          .attr('y', d => yScale(d.value))
          .attr('height', d => height - yScale(d.value))

        labels.transition()
          .duration(500)
          .attr('y', d => yScale(d.value) - 5)
          .text(d => `${d.percentage.toFixed(1)}%`)

        g.select('.y-axis')
          .transition()
          .duration(500)
          .call(yAxis)
      }
    })

    // Add legend
    const legend = svg.append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${width + margin.left - 100}, ${margin.top})`)

    const legendItems = legend.selectAll('.legend-item')
      .data(data)
      .enter().append('g')
      .attr('class', 'legend-item')
      .attr('transform', (d, i) => `translate(0, ${i * 20})`)

    legendItems.append('rect')
      .attr('width', 12)
      .attr('height', 12)
      .attr('fill', d => chainColors[d.chainId] || '#666')

    legendItems.append('text')
      .attr('x', 18)
      .attr('y', 9)
      .style('font-size', '12px')
      .style('fill', 'hsl(var(--muted-foreground))')
      .text(d => d.name)

    // Cleanup
    return () => {
      d3.select(svgRef.current).selectAll('*').remove()
    }
  }, [data])

  return (
    <Card className="p-6 relative">
      <ChartExportButton svgRef={svgRef} filename="chain-distribution" />
      <h3 className="text-lg font-semibold mb-4">Chain Distribution</h3>
      <p className="text-sm text-muted-foreground mb-4">Click bars to toggle between value and percentage view</p>
      <div className="relative">
        <svg ref={svgRef} className="w-full" />
        <div
          ref={tooltipRef}
          className="absolute z-10 p-2 bg-background border border-border rounded-lg shadow-lg"
          style={{ display: 'none', pointerEvents: 'none' }}
        />
      </div>
    </Card>
  )
}