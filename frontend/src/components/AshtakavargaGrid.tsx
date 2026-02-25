import React from 'react'
import { AshtakavargaData } from '../api/client'
import { SIGN_ABBR, SIGN_NAME_TO_NUM } from './chartConstants'

interface Props {
  ashtakavarga: AshtakavargaData
}

const PLANETS_ORDER = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
const SIGNS_ORDER = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
const SIGN_KEYS = ['ARIES', 'TAURUS', 'GEMINI', 'CANCER', 'LEO', 'VIRGO', 'LIBRA', 'SCORPIO', 'SAGITTARIUS', 'CAPRICORN', 'AQUARIUS', 'PISCES']

function bavColor(points: number): string {
  if (points >= 5) return 'var(--success-bg)'
  if (points >= 4) return 'var(--info-bg)'
  if (points >= 3) return 'var(--warning-bg)'
  return 'var(--danger-bg)'
}

function bavTextColor(points: number): string {
  if (points >= 5) return 'var(--success-text)'
  if (points >= 4) return 'var(--info-text)'
  if (points >= 3) return 'var(--warning-text)'
  return 'var(--danger-text)'
}

function savColor(points: number): string {
  if (points >= 30) return 'var(--success-bg)'
  if (points >= 27) return 'var(--info-bg)'
  if (points >= 25) return 'var(--warning-bg)'
  return 'var(--danger-bg)'
}

function savTextColor(points: number): string {
  if (points >= 30) return 'var(--success-text)'
  if (points >= 27) return 'var(--info-text)'
  if (points >= 25) return 'var(--warning-text)'
  return 'var(--danger-text)'
}

const cellStyle: React.CSSProperties = {
  padding: '6px 4px',
  textAlign: 'center',
  fontSize: 12,
  fontWeight: 600,
  borderBottom: '1px solid var(--table-border)',
  borderRight: '1px solid var(--table-border)',
  transition: 'background 0.15s',
}

const headerCell: React.CSSProperties = {
  ...cellStyle,
  fontSize: 10,
  fontWeight: 700,
  textTransform: 'uppercase',
  letterSpacing: 0.5,
  color: 'var(--text-tertiary)',
  background: 'var(--table-header-bg)',
  position: 'sticky' as const,
}

export default function AshtakavargaGrid({ ashtakavarga }: Props) {
  const { bav, sav, sav_trikona_reduced } = ashtakavarga

  return (
    <div>
      {/* BAV Heatmap */}
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>
          Bhinna Ashtakavarga (BAV)
        </div>
        <div style={{ overflowX: 'auto', borderRadius: 'var(--radius-md)', border: '1px solid var(--table-border)' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 600 }}>
            <thead>
              <tr>
                <th style={{ ...headerCell, left: 0, zIndex: 1 }}>Planet</th>
                {SIGNS_ORDER.map((s) => (
                  <th key={s} style={headerCell}>{SIGN_ABBR[s]}</th>
                ))}
                <th style={headerCell}>Total</th>
              </tr>
            </thead>
            <tbody>
              {PLANETS_ORDER.map((planet) => {
                const planetBav = bav[planet] || {}
                let total = 0
                return (
                  <tr key={planet}>
                    <td style={{ ...cellStyle, fontWeight: 700, color: 'var(--text-primary)', background: 'var(--table-header-bg)', position: 'sticky' as const, left: 0 }}>
                      {planet}
                    </td>
                    {SIGN_KEYS.map((signKey, i) => {
                      const points = planetBav[signKey] ?? 0
                      total += points
                      return (
                        <td
                          key={signKey}
                          style={{
                            ...cellStyle,
                            background: bavColor(points),
                            color: bavTextColor(points),
                          }}
                        >
                          {points}
                        </td>
                      )
                    })}
                    <td style={{ ...cellStyle, fontWeight: 700, color: 'var(--text-primary)' }}>
                      {total}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* SAV Summary */}
      <div>
        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>
          Sarva Ashtakavarga (SAV)
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(70px, 1fr))', gap: 8 }}>
          {SIGN_KEYS.map((signKey, i) => {
            const signNum = i + 1
            const points = sav[signKey] ?? 0
            const reduced = sav_trikona_reduced?.[signKey] ?? points
            return (
              <div
                key={signKey}
                style={{
                  background: savColor(points),
                  borderRadius: 'var(--radius-md)',
                  padding: '8px 6px',
                  textAlign: 'center',
                }}
              >
                <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>
                  {SIGN_ABBR[signNum]}
                </div>
                <div style={{ fontSize: 18, fontWeight: 800, color: savTextColor(points), marginTop: 2 }}>
                  {points}
                </div>
                {reduced !== points && (
                  <div style={{ fontSize: 9, color: 'var(--text-tertiary)', marginTop: 2 }}>
                    TR: {reduced}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* SAV Bar Chart */}
        <div style={{ marginTop: 20 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: 8 }}>
            SAV Distribution
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height: 120 }}>
            {SIGN_KEYS.map((signKey, i) => {
              const signNum = i + 1
              const points = sav[signKey] ?? 0
              const maxPoints = 56
              const height = (points / maxPoints) * 100
              return (
                <div key={signKey} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                  <div style={{ fontSize: 9, fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: 2 }}>
                    {points}
                  </div>
                  <div
                    style={{
                      width: '100%',
                      height: `${height}%`,
                      background: points >= 30 ? 'var(--success)' : points >= 27 ? 'var(--info)' : points >= 25 ? 'var(--warning)' : 'var(--danger)',
                      borderRadius: '3px 3px 0 0',
                      transition: 'height 0.5s ease',
                      minHeight: 4,
                      opacity: 0.8,
                    }}
                  />
                  <div style={{ fontSize: 8, fontWeight: 600, color: 'var(--text-tertiary)', marginTop: 3 }}>
                    {SIGN_ABBR[signNum]}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
