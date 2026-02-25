import React from 'react'
import { ConfidenceLevel, CONFIDENCE_COLORS } from '../types'

interface ConfidenceGaugeProps {
  score: number
  confidenceLevel: string
  size?: number
}

export default function ConfidenceGauge({ score, confidenceLevel, size = 180 }: ConfidenceGaugeProps) {
  const color = CONFIDENCE_COLORS[confidenceLevel as ConfidenceLevel] || '#94a3b8'
  const maxScore = 3
  const fraction = Math.min(score / maxScore, 1)

  const cx = size / 2
  const cy = size / 2
  const strokeWidth = 14
  const radius = (size - strokeWidth) / 2 - 4

  const startAngle = 135
  const endAngle = 405
  const sweepAngle = endAngle - startAngle
  const filledAngle = startAngle + sweepAngle * fraction
  const toRad = (d: number) => (d * Math.PI) / 180

  const arc = (from: number, to: number) => {
    const x1 = cx + radius * Math.cos(toRad(from))
    const y1 = cy + radius * Math.sin(toRad(from))
    const x2 = cx + radius * Math.cos(toRad(to))
    const y2 = cy + radius * Math.sin(toRad(to))
    return `M ${x1} ${y1} A ${radius} ${radius} 0 ${to - from > 180 ? 1 : 0} 1 ${x2} ${y2}`
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        background: 'var(--card-bg)',
        border: '1px solid var(--card-border)',
        borderRadius: 'var(--radius-xl)',
        padding: 24,
        boxShadow: 'var(--shadow-md)',
      }}
    >
      <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 8 }}>
        Convergence Score
      </div>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <path d={arc(startAngle, endAngle)} fill="none" stroke="var(--gauge-track)" strokeWidth={strokeWidth} strokeLinecap="round" />
        {fraction > 0 && (
          <path d={arc(startAngle, filledAngle)} fill="none" stroke={color} strokeWidth={strokeWidth} strokeLinecap="round" />
        )}
        <text x={cx} y={cy - 6} textAnchor="middle" dominantBaseline="central" style={{ fontSize: 36, fontWeight: 800, fill: color }}>
          {score.toFixed(2)}
        </text>
        <text x={cx} y={cy + 24} textAnchor="middle" dominantBaseline="central" style={{ fontSize: 12, fontWeight: 600, fill: 'var(--text-tertiary)' }}>
          out of {maxScore}
        </text>
        <text x={cx + radius * Math.cos(toRad(startAngle)) - 8} y={cy + radius * Math.sin(toRad(startAngle)) + 16} textAnchor="middle" style={{ fontSize: 10, fill: 'var(--text-tertiary)' }}>0</text>
        <text x={cx + radius * Math.cos(toRad(endAngle)) + 8} y={cy + radius * Math.sin(toRad(endAngle)) + 16} textAnchor="middle" style={{ fontSize: 10, fill: 'var(--text-tertiary)' }}>3</text>
      </svg>
      <span
        style={{
          display: 'inline-block',
          padding: '5px 18px',
          borderRadius: 'var(--radius-full)',
          fontSize: 12,
          fontWeight: 700,
          color: '#fff',
          background: color,
          marginTop: 8,
          textTransform: 'uppercase',
          letterSpacing: 1,
        }}
      >
        {confidenceLevel}
      </span>
    </div>
  )
}
