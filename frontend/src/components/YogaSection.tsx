import React, { useState } from 'react'
import { YogaData } from '../api/client'
import { PLANET_COLORS } from './chartConstants'

interface Props {
  yogas: YogaData[]
}

function strengthColor(strength: number): string {
  if (strength >= 0.7) return 'var(--success)'
  if (strength >= 0.4) return 'var(--warning)'
  return 'var(--info)'
}

function strengthBg(strength: number): string {
  if (strength >= 0.7) return 'var(--success-bg)'
  if (strength >= 0.4) return 'var(--warning-bg)'
  return 'var(--info-bg)'
}

export default function YogaSection({ yogas }: Props) {
  const [showAbsent, setShowAbsent] = useState(false)

  const presentYogas = yogas.filter((y) => y.is_present)
  const absentYogas = yogas.filter((y) => !y.is_present)

  return (
    <div>
      <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>
        Yogas Found ({presentYogas.length} of {yogas.length})
      </div>

      {presentYogas.length === 0 && (
        <div style={{
          padding: 24,
          textAlign: 'center',
          color: 'var(--text-tertiary)',
          background: 'var(--bg-inset)',
          borderRadius: 'var(--radius-md)',
        }}>
          No classical yogas detected in this chart.
        </div>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {presentYogas.map((yoga, i) => {
          const color = strengthColor(yoga.strength)
          const bg = strengthBg(yoga.strength)
          return (
            <div
              key={i}
              style={{
                background: 'var(--bg-inset)',
                borderRadius: 'var(--radius-md)',
                borderLeft: `4px solid ${color}`,
                padding: '14px 18px',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
                  {yoga.name}
                </span>
                <span style={{
                  fontSize: 10,
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-full)',
                  background: bg,
                  color: color,
                  textTransform: 'uppercase',
                }}>
                  {yoga.yoga_type}
                </span>
              </div>

              {/* Strength bar */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                <span style={{ fontSize: 11, color: 'var(--text-tertiary)', minWidth: 55 }}>
                  Strength
                </span>
                <div style={{
                  flex: 1,
                  height: 6,
                  background: 'var(--bg-primary)',
                  borderRadius: 3,
                  overflow: 'hidden',
                }}>
                  <div style={{
                    width: `${yoga.strength * 100}%`,
                    height: '100%',
                    background: color,
                    borderRadius: 3,
                    transition: 'width 0.5s ease',
                  }} />
                </div>
                <span style={{ fontSize: 11, fontWeight: 700, color, minWidth: 35 }}>
                  {(yoga.strength * 100).toFixed(0)}%
                </span>
              </div>

              {/* Involved planets */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Planets:</span>
                {yoga.involved_planets.map((p) => (
                  <span
                    key={p}
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      color: PLANET_COLORS[p] || 'var(--text-secondary)',
                      background: 'var(--bg-primary)',
                      padding: '1px 6px',
                      borderRadius: 'var(--radius-sm)',
                    }}
                  >
                    {p}
                  </span>
                ))}
              </div>

              {/* Description */}
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                {yoga.description}
              </div>
            </div>
          )
        })}
      </div>

      {/* Absent yogas (collapsible) */}
      {absentYogas.length > 0 && (
        <div style={{ marginTop: 20 }}>
          <div
            onClick={() => setShowAbsent(!showAbsent)}
            style={{
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 600,
              color: 'var(--text-tertiary)',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
            }}
          >
            <span style={{
              transform: showAbsent ? 'rotate(90deg)' : 'rotate(0deg)',
              transition: 'transform 0.2s',
              fontSize: 10,
            }}>
              {'\u25B6'}
            </span>
            Not Found ({absentYogas.length})
          </div>

          {showAbsent && (
            <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
              {absentYogas.map((yoga, i) => (
                <div
                  key={i}
                  style={{
                    padding: '8px 14px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--bg-inset)',
                    opacity: 0.6,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                  }}
                >
                  <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)' }}>
                    {yoga.name}
                  </span>
                  <span style={{ fontSize: 10, color: 'var(--text-tertiary)', marginLeft: 'auto' }}>
                    Not present
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
