import React from 'react'
import { PlanetData } from '../api/client'
import {
  SIGN_ABBR, SIGN_SYMBOLS, PLANET_ABBR, PLANET_COLORS,
  formatDegrees, normalizeSign,
} from './chartConstants'

interface Props {
  planets: PlanetData[]
  ascendantSign: number
  title?: string
  size?: number
}

// South Indian chart: fixed 4x4 grid with 12 outer cells
// Signs are FIXED in position (Pisces=top-left, Aries=top-2nd, etc.)
// The ascendant house gets a diagonal marker.

const S = 400
const pad = 8
const cellW = (S - 2 * pad) / 4
const cellH = (S - 2 * pad) / 4

// South Indian sign positions (row, col) — signs are fixed
// Standard layout: Pisces(12) starts at top-left, going clockwise
const SIGN_POSITIONS: Record<number, [number, number]> = {
  12: [0, 0], // Pisces — top-left
  1:  [0, 1], // Aries — top-2nd
  2:  [0, 2], // Taurus — top-3rd
  3:  [0, 3], // Gemini — top-right
  4:  [1, 3], // Cancer — right-2nd
  5:  [2, 3], // Leo — right-3rd
  6:  [3, 3], // Virgo — bottom-right
  7:  [3, 2], // Libra — bottom-3rd
  8:  [3, 1], // Scorpio — bottom-2nd
  9:  [3, 0], // Sagittarius — bottom-left
  10: [2, 0], // Capricorn — left-3rd
  11: [1, 0], // Aquarius — left-2nd
}

// Center cells (not used for signs)
const CENTER_CELLS: [number, number][] = [[1, 1], [1, 2], [2, 1], [2, 2]]

function getCellRect(row: number, col: number): { x: number; y: number; w: number; h: number } {
  return {
    x: pad + col * cellW,
    y: pad + row * cellH,
    w: cellW,
    h: cellH,
  }
}

export default function SouthIndianChart({ planets, ascendantSign, title, size = 400 }: Props) {
  // Group planets by sign
  const planetsBySign: Record<number, PlanetData[]> = {}
  planets.forEach((p) => {
    const sign = normalizeSign(p.sign)
    if (!planetsBySign[sign]) planetsBySign[sign] = []
    planetsBySign[sign].push(p)
  })

  const scale = size / S

  return (
    <div style={{ textAlign: 'center' }}>
      {title && (
        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
          {title}
        </div>
      )}
      <svg
        viewBox={`0 0 ${S} ${S}`}
        width={size}
        height={size}
        style={{ maxWidth: '100%', height: 'auto' }}
      >
        {/* Background */}
        <rect x={pad} y={pad} width={S - 2 * pad} height={S - 2 * pad}
          fill="var(--chart-fill)" stroke="var(--chart-line)" strokeWidth="1.5" rx="4" />

        {/* Grid lines */}
        {[1, 2, 3].map((i) => (
          <React.Fragment key={`grid-${i}`}>
            <line
              x1={pad + i * cellW} y1={pad}
              x2={pad + i * cellW} y2={S - pad}
              stroke="var(--chart-line)" strokeWidth="1"
            />
            <line
              x1={pad} y1={pad + i * cellH}
              x2={S - pad} y2={pad + i * cellH}
              stroke="var(--chart-line)" strokeWidth="1"
            />
          </React.Fragment>
        ))}

        {/* Center area (merge 4 center cells) */}
        <rect
          x={pad + cellW}
          y={pad + cellH}
          width={cellW * 2}
          height={cellH * 2}
          fill="var(--chart-fill)"
          stroke="var(--chart-line)"
          strokeWidth="1"
        />
        <text
          x={S / 2}
          y={S / 2 - 8}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={12}
          fontWeight={700}
          fill="var(--text-tertiary)"
        >
          South Indian
        </text>
        <text
          x={S / 2}
          y={S / 2 + 10}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={11}
          fill="var(--text-tertiary)"
        >
          Chart
        </text>

        {/* Sign cells */}
        {Object.entries(SIGN_POSITIONS).map(([signStr, [row, col]]) => {
          const sign = parseInt(signStr, 10)
          const cell = getCellRect(row, col)
          const planetsInSign = planetsBySign[sign] || []
          const isAscendant = sign === ascendantSign

          return (
            <g key={sign}>
              {/* Ascendant marker — diagonal line in cell */}
              {isAscendant && (
                <line
                  x1={cell.x + 2}
                  y1={cell.y + cell.h - 2}
                  x2={cell.x + 18}
                  y2={cell.y + cell.h - 18}
                  stroke="var(--accent-primary)"
                  strokeWidth="2"
                />
              )}

              {/* Sign abbreviation */}
              <text
                x={cell.x + 6}
                y={cell.y + 14}
                fontSize={10}
                fontWeight={isAscendant ? 800 : 600}
                fill={isAscendant ? 'var(--accent-primary)' : 'var(--chart-sign-text)'}
              >
                {SIGN_ABBR[sign]} {SIGN_SYMBOLS[sign]}
              </text>

              {/* Planet labels */}
              {planetsInSign.map((p, pi) => {
                const abbr = PLANET_ABBR[p.planet] || p.planet.slice(0, 2)
                const color = PLANET_COLORS[p.planet] || 'var(--text-secondary)'
                return (
                  <text
                    key={p.planet}
                    x={cell.x + cell.w / 2}
                    y={cell.y + 30 + pi * 13}
                    textAnchor="middle"
                    fontSize={9.5}
                    fontWeight={600}
                    fill={color}
                  >
                    {abbr} {formatDegrees(p.sign_degrees)}
                    {p.is_retrograde ? '(R)' : ''}
                  </text>
                )
              })}
            </g>
          )
        })}
      </svg>
    </div>
  )
}
