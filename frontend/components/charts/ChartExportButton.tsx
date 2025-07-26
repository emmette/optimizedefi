'use client'

import { useRef } from 'react'
import { Download } from 'lucide-react'

interface ChartExportButtonProps {
  svgRef: React.RefObject<SVGSVGElement>
  filename?: string
}

export function ChartExportButton({ svgRef, filename = 'chart' }: ChartExportButtonProps) {
  const linkRef = useRef<HTMLAnchorElement>(null)

  const exportAsPNG = () => {
    if (!svgRef.current) return

    const svg = svgRef.current
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Get SVG data
    const svgData = new XMLSerializer().serializeToString(svg)
    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' })
    const url = URL.createObjectURL(svgBlob)

    // Create image
    const img = new Image()
    img.onload = () => {
      canvas.width = svg.clientWidth * 2 // 2x resolution
      canvas.height = svg.clientHeight * 2
      ctx.scale(2, 2)
      
      // White background
      ctx.fillStyle = 'white'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      
      // Draw image
      ctx.drawImage(img, 0, 0, svg.clientWidth, svg.clientHeight)
      
      // Convert to PNG
      canvas.toBlob((blob) => {
        if (blob) {
          const pngUrl = URL.createObjectURL(blob)
          if (linkRef.current) {
            linkRef.current.href = pngUrl
            linkRef.current.download = `${filename}.png`
            linkRef.current.click()
          }
          URL.revokeObjectURL(pngUrl)
        }
      }, 'image/png')
      
      URL.revokeObjectURL(url)
    }
    img.src = url
  }

  const exportAsSVG = () => {
    if (!svgRef.current) return

    const svg = svgRef.current
    const svgData = new XMLSerializer().serializeToString(svg)
    const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' })
    const url = URL.createObjectURL(svgBlob)

    if (linkRef.current) {
      linkRef.current.href = url
      linkRef.current.download = `${filename}.svg`
      linkRef.current.click()
    }
    
    URL.revokeObjectURL(url)
  }

  return (
    <>
      <div className="absolute top-4 right-4 flex gap-2">
        <button
          onClick={exportAsPNG}
          className="p-2 bg-background/80 hover:bg-background border border-border rounded-lg transition-colors"
          title="Export as PNG"
        >
          <Download className="h-4 w-4" />
          <span className="sr-only">Export as PNG</span>
        </button>
        <button
          onClick={exportAsSVG}
          className="p-2 bg-background/80 hover:bg-background border border-border rounded-lg transition-colors"
          title="Export as SVG"
        >
          <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <path d="M10 12l-2 2 2 2" />
            <path d="M14 12l2 2-2 2" />
          </svg>
          <span className="sr-only">Export as SVG</span>
        </button>
      </div>
      <a ref={linkRef} style={{ display: 'none' }} />
    </>
  )
}