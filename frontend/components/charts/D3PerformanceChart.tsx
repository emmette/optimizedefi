'use client'

import { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import { Card } from '@/components/ui/Card'
import { ChartExportButton } from './ChartExportButton'

interface DataPoint {
  date: Date
  value: number
}

interface D3PerformanceChartProps {
  data: DataPoint[]
  height?: number
}

export function D3PerformanceChart({ data, height = 400 }: D3PerformanceChartProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const tooltipRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!svgRef.current || data.length === 0) return

    // Clear previous chart
    d3.select(svgRef.current).selectAll('*').remove()

    // Set dimensions
    const margin = { top: 20, right: 30, bottom: 40, left: 60 }
    const width = svgRef.current.clientWidth - margin.left - margin.right
    const actualHeight = height - margin.top - margin.bottom

    // Create SVG
    const svg = d3.select(svgRef.current)
      .attr('width', width + margin.left + margin.right)
      .attr('height', height)

    // Create clip path for zoom
    svg.append('defs').append('clipPath')
      .attr('id', 'clip')
      .append('rect')
      .attr('width', width)
      .attr('height', actualHeight)

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`)

    // Create scales
    const xScale = d3.scaleTime()
      .domain(d3.extent(data, d => d.date) as [Date, Date])
      .range([0, width])

    const yScale = d3.scaleLinear()
      .domain([
        d3.min(data, d => d.value) * 0.95,
        d3.max(data, d => d.value) * 1.05
      ] as [number, number])
      .range([actualHeight, 0])

    // Create line generator
    const line = d3.line<DataPoint>()
      .x(d => xScale(d.date))
      .y(d => yScale(d.value))
      .curve(d3.curveMonotoneX)

    // Create area generator for gradient
    const area = d3.area<DataPoint>()
      .x(d => xScale(d.date))
      .y0(actualHeight)
      .y1(d => yScale(d.value))
      .curve(d3.curveMonotoneX)

    // Add gradient
    const gradient = svg.append('defs').append('linearGradient')
      .attr('id', 'area-gradient')
      .attr('gradientUnits', 'userSpaceOnUse')
      .attr('x1', 0).attr('y1', yScale(d3.min(data, d => d.value)!))
      .attr('x2', 0).attr('y2', yScale(d3.max(data, d => d.value)!))

    gradient.append('stop')
      .attr('offset', '0%')
      .attr('stop-color', 'hsl(142, 70%, 45%)')
      .attr('stop-opacity', 0.3)

    gradient.append('stop')
      .attr('offset', '100%')
      .attr('stop-color', 'hsl(142, 70%, 45%)')
      .attr('stop-opacity', 0)

    // Create axes
    const xAxis = d3.axisBottom(xScale)
      .tickFormat(d3.timeFormat('%b %d'))
      .ticks(6)

    const yAxis = d3.axisLeft(yScale)
      .tickFormat(d => `$${d.toLocaleString()}`)
      .ticks(5)

    // Add X axis
    const xAxisG = g.append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0,${actualHeight})`)
      .call(xAxis)

    // Add Y axis
    const yAxisG = g.append('g')
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
      .attr('transform', `translate(0,${actualHeight})`)
      .call(d3.axisBottom(xScale)
        .tickSize(-actualHeight)
        .tickFormat(() => '')
      )
      .style('stroke-dasharray', '3,3')
      .style('opacity', 0.3)

    g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yScale)
        .tickSize(-width)
        .tickFormat(() => '')
      )
      .style('stroke-dasharray', '3,3')
      .style('opacity', 0.3)

    // Create chart area group with clip path
    const chartArea = g.append('g')
      .attr('clip-path', 'url(#clip)')

    // Add area
    chartArea.append('path')
      .datum(data)
      .attr('class', 'area')
      .attr('fill', 'url(#area-gradient)')
      .attr('d', area)

    // Add line
    const path = chartArea.append('path')
      .datum(data)
      .attr('class', 'line')
      .attr('fill', 'none')
      .attr('stroke', 'hsl(142, 70%, 45%)')
      .attr('stroke-width', 2)
      .attr('d', line)

    // Animate line drawing
    const totalLength = path.node()?.getTotalLength() || 0
    path
      .attr('stroke-dasharray', totalLength + ' ' + totalLength)
      .attr('stroke-dashoffset', totalLength)
      .transition()
      .duration(1500)
      .ease(d3.easeLinear)
      .attr('stroke-dashoffset', 0)

    // Add dots
    const dots = chartArea.selectAll('.dot')
      .data(data)
      .enter().append('circle')
      .attr('class', 'dot')
      .attr('cx', d => xScale(d.date))
      .attr('cy', d => yScale(d.value))
      .attr('r', 0)
      .attr('fill', 'hsl(142, 70%, 45%)')
      .style('cursor', 'pointer')

    // Animate dots
    dots.transition()
      .delay((d, i) => i * 30)
      .duration(300)
      .attr('r', 4)

    // Add hover line
    const hoverLine = chartArea.append('line')
      .attr('class', 'hover-line')
      .attr('y1', 0)
      .attr('y2', actualHeight)
      .style('stroke', 'hsl(var(--muted-foreground))')
      .style('stroke-width', 1)
      .style('stroke-dasharray', '3,3')
      .style('opacity', 0)

    // Add overlay for mouse events
    const overlay = chartArea.append('rect')
      .attr('width', width)
      .attr('height', actualHeight)
      .style('fill', 'none')
      .style('pointer-events', 'all')
      .on('mousemove', function(event) {
        const [mouseX] = d3.pointer(event)
        const bisect = d3.bisector((d: DataPoint) => d.date).left
        const x0 = xScale.invert(mouseX)
        const i = bisect(data, x0, 1)
        const d0 = data[i - 1]
        const d1 = data[i]
        const d = d1 && x0.getTime() - d0.date.getTime() > d1.date.getTime() - x0.getTime() ? d1 : d0

        if (d && tooltipRef.current) {
          hoverLine
            .attr('x1', xScale(d.date))
            .attr('x2', xScale(d.date))
            .style('opacity', 1)

          tooltipRef.current.innerHTML = `
            <div class="font-semibold">${d.date.toLocaleDateString()}</div>
            <div class="text-sm text-muted-foreground">
              Value: $${d.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}
            </div>
          `
          tooltipRef.current.style.display = 'block'
          tooltipRef.current.style.left = `${event.pageX + 10}px`
          tooltipRef.current.style.top = `${event.pageY - 10}px`
        }
      })
      .on('mouseout', function() {
        hoverLine.style('opacity', 0)
        if (tooltipRef.current) {
          tooltipRef.current.style.display = 'none'
        }
      })

    // Add zoom behavior
    const zoom = d3.zoom<SVGRectElement, unknown>()
      .scaleExtent([0.5, 10])
      .translateExtent([[0, 0], [width, actualHeight]])
      .extent([[0, 0], [width, actualHeight]])
      .on('zoom', function(event) {
        const newXScale = event.transform.rescaleX(xScale)
        const newYScale = event.transform.rescaleY(yScale)

        // Update axes
        xAxisG.call(xAxis.scale(newXScale))
        yAxisG.call(yAxis.scale(newYScale))

        // Update line and area
        chartArea.select('.line')
          .attr('d', line.x(d => newXScale(d.date)).y(d => newYScale(d.value)))
        chartArea.select('.area')
          .attr('d', area.x(d => newXScale(d.date)).y1(d => newYScale(d.value)))

        // Update dots
        dots
          .attr('cx', d => newXScale(d.date))
          .attr('cy', d => newYScale(d.value))

        // Update grid
        g.select('.grid').call(d3.axisBottom(newXScale)
          .tickSize(-actualHeight)
          .tickFormat(() => '')
        )
      })

    overlay.call(zoom)

    // Add reset button
    const resetButton = svg.append('g')
      .attr('transform', `translate(${width + margin.left - 50}, ${margin.top})`)
      .style('cursor', 'pointer')
      .on('click', function() {
        overlay.transition()
          .duration(750)
          .call(zoom.transform, d3.zoomIdentity)
      })

    resetButton.append('rect')
      .attr('width', 40)
      .attr('height', 20)
      .attr('rx', 4)
      .attr('fill', 'hsl(var(--primary))')

    resetButton.append('text')
      .attr('x', 20)
      .attr('y', 14)
      .attr('text-anchor', 'middle')
      .attr('fill', 'white')
      .style('font-size', '12px')
      .text('Reset')

    // Cleanup
    return () => {
      d3.select(svgRef.current).selectAll('*').remove()
    }
  }, [data, height])

  // Generate sample data if none provided
  const sampleData = data.length > 0 ? data : Array.from({ length: 30 }, (_, i) => ({
    date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000),
    value: 10000 + Math.random() * 5000 + i * 100 + Math.sin(i / 3) * 1000
  }))

  return (
    <Card className="p-6 relative">
      <ChartExportButton svgRef={svgRef} filename="portfolio-performance" />
      <h3 className="text-lg font-semibold mb-4">Portfolio Performance</h3>
      <p className="text-sm text-muted-foreground mb-4">Drag to pan, scroll to zoom</p>
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