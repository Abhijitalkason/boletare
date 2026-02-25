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

// ═══════════════════════════════════════════════════════════════
// North Indian Kundli — Diamond-in-Square Layout (SVG)
//
// Geometry (400x400, padding=8):
//   Outer square: TL(8,8) TR(392,8) BR(392,392) BL(8,392)
//   Side midpoints: TC(200,8) MR(392,200) BC(200,392) ML(8,200)
//   Center: MC(200,200)
//
//   Lines drawn:
//     - Outer square border
//     - Inner diamond: TC→MR→BC→ML
//     - Diagonals: TL→BR and TR→BL
//
//   Diagonal–diamond intersections:
//     P1(104,104)  P2(296,104)  P3(296,296)  P4(104,296)
//
//   12 houses (clockwise from top):
//     H1:  TC,  P2,  P1          (top diamond — Ascendant)
//     H2:  TC,  TR,  P2          (upper-right, upper triangle)
//     H3:  TR,  MR,  P2          (upper-right, lower triangle)
//     H4:  MR,  P3,  P2          (right diamond)
//     H5:  MR,  BR,  P3          (lower-right, upper triangle)
//     H6:  BR,  BC,  P3          (lower-right, lower triangle)
//     H7:  BC,  P4,  P3          (bottom diamond)
//     H8:  BC,  BL,  P4          (lower-left, upper triangle)
//     H9:  BL,  ML,  P4          (lower-left, lower triangle)
//     H10: ML,  P1,  P4          (left diamond)
//     H11: ML,  TL,  P1          (upper-left, lower triangle)
//     H12: TL,  TC,  P1          (upper-left, upper triangle)
// ═══════════════════════════════════════════════════════════════

const S = 400
const pad = 8
const M = S / 2

const TL: [number, number] = [pad, pad]
const TR: [number, number] = [S - pad, pad]
const BL: [number, number] = [pad, S - pad]
const BR: [number, number] = [S - pad, S - pad]
const TC: [number, number] = [M, pad]
const BC: [number, number] = [M, S - pad]
const ML: [number, number] = [pad, M]
const MR: [number, number] = [S - pad, M]
const P1: [number, number] = [104, 104]
const P2: [number, number] = [296, 104]
const P3: [number, number] = [296, 296]
const P4: [number, number] = [104, 296]

function centroid(...pts: [number, number][]): [number, number] {
  const cx = pts.reduce((s, p) => s + p[0], 0) / pts.length
  const cy = pts.reduce((s, p) => s + p[1], 0) / pts.length
  return [cx, cy]
}

const HOUSES: { vertices: [number, number][]; center: [number, number] }[] = [
  { vertices: [TC, P2, P1],   center: centroid(TC, P2, P1) },    // H1  Ascendant
  { vertices: [TC, TR, P2],   center: centroid(TC, TR, P2) },    // H2
  { vertices: [TR, MR, P2],   center: centroid(TR, MR, P2) },    // H3
  { vertices: [MR, P3, P2],   center: centroid(MR, P3, P2) },    // H4
  { vertices: [MR, BR, P3],   center: centroid(MR, BR, P3) },    // H5
  { vertices: [BR, BC, P3],   center: centroid(BR, BC, P3) },    // H6
  { vertices: [BC, P4, P3],   center: centroid(BC, P4, P3) },    // H7
  { vertices: [BC, BL, P4],   center: centroid(BC, BL, P4) },    // H8
  { vertices: [BL, ML, P4],   center: centroid(BL, ML, P4) },    // H9
  { vertices: [ML, P1, P4],   center: centroid(ML, P1, P4) },    // H10
  { vertices: [ML, TL, P1],   center: centroid(ML, TL, P1) },    // H11
  { vertices: [TL, TC, P1],   center: centroid(TL, TC, P1) },    // H12
]

function polyPoints(pts: [number, number][]): string {
  return pts.map(([x, y]) => `${x},${y}`).join(' ')
}

export default function NorthIndianChart({ planets, ascendantSign, title, size = 400 }: Props) {
  // Group planets by house number (1-12)
  const planetsByHouse: Record<number, PlanetData[]> = {}
  planets.forEach((p) => {
    const h = p.house || 1
    if (!planetsByHouse[h]) planetsByHouse[h] = []
    planetsByHouse[h].push(p)
  })

  // House N has sign = (ascendant + N - 2) % 12 + 1
  const houseSign = (houseNum: number): number =>
    ((ascendantSign - 1 + houseNum - 1) % 12) + 1

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
        {/* Outer square background */}
        <rect x={pad} y={pad} width={S - 2 * pad} height={S - 2 * pad}
          fill="var(--chart-fill)" stroke="var(--chart-line)" strokeWidth="2" rx="3" />

        {/* Diagonals */}
        <line x1={TL[0]} y1={TL[1]} x2={BR[0]} y2={BR[1]} stroke="var(--chart-line)" strokeWidth="1.2" />
        <line x1={TR[0]} y1={TR[1]} x2={BL[0]} y2={BL[1]} stroke="var(--chart-line)" strokeWidth="1.2" />

        {/* Inner diamond */}
        <polygon
          points={polyPoints([TC, MR, BC, ML])}
          fill="none"
          stroke="var(--chart-line)"
          strokeWidth="1.5"
        />

        {/* House contents */}
        {HOUSES.map((house, i) => {
          const houseNum = i + 1
          const sign = houseSign(houseNum)
          const planetsInHouse = planetsByHouse[houseNum] || []
          const [cx, cy] = house.center
          const isAsc = houseNum === 1

          // Adjust text vertical position based on planet count
          const signY = planetsInHouse.length > 0 ? cy - (planetsInHouse.length * 6) : cy

          return (
            <g key={houseNum}>
              {/* Sign label */}
              <text
                x={cx}
                y={signY}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize={isAsc ? 13 : 11}
                fontWeight={isAsc ? 800 : 600}
                fill={isAsc ? 'var(--accent-primary)' : 'var(--chart-sign-text)'}
              >
                {SIGN_ABBR[sign]}{' '}{SIGN_SYMBOLS[sign]}
                {isAsc ? ' \u2191' : ''}
              </text>

              {/* Planets */}
              {planetsInHouse.map((p, pi) => {
                const abbr = PLANET_ABBR[p.planet] || p.planet.slice(0, 2)
                const color = PLANET_COLORS[p.planet] || 'var(--text-secondary)'
                return (
                  <text
                    key={p.planet}
                    x={cx}
                    y={signY + 14 + pi * 13}
                    textAnchor="middle"
                    dominantBaseline="central"
                    fontSize={10}
                    fontWeight={600}
                    fill={color}
                  >
                    {abbr} {formatDegrees(p.sign_degrees)}
                    {p.is_retrograde ? ' R' : ''}
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
