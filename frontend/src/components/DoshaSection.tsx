import React from 'react'
import { DoshaData } from '../api/client'

interface Props {
  doshas: DoshaData[]
}

function severityColor(severity: string): string {
  switch (severity) {
    case 'severe': return 'var(--danger)'
    case 'moderate': return 'var(--warning)'
    case 'mild': return '#d97706'
    case 'none': return 'var(--success)'
    default: return 'var(--text-tertiary)'
  }
}

function severityBg(severity: string): string {
  switch (severity) {
    case 'severe': return 'var(--danger-bg)'
    case 'moderate': return 'var(--warning-bg)'
    case 'mild': return 'rgba(217, 119, 6, 0.12)'
    case 'none': return 'var(--success-bg)'
    default: return 'var(--bg-inset)'
  }
}

function severityLabel(severity: string): string {
  switch (severity) {
    case 'severe': return 'Severe'
    case 'moderate': return 'Moderate'
    case 'mild': return 'Mild'
    case 'none': return 'Not Present'
    default: return severity
  }
}

export default function DoshaSection({ doshas }: Props) {
  const presentDoshas = doshas.filter((d) => d.is_present)
  const absentDoshas = doshas.filter((d) => !d.is_present)

  return (
    <div>
      <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>
        Dosha Analysis
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {doshas.map((dosha, i) => {
          const color = severityColor(dosha.severity)
          const bg = severityBg(dosha.severity)
          const isPresent = dosha.is_present

          return (
            <div
              key={i}
              style={{
                background: 'var(--bg-inset)',
                borderRadius: 'var(--radius-md)',
                borderLeft: `4px solid ${color}`,
                padding: '14px 18px',
                opacity: isPresent ? 1 : 0.7,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                <span style={{
                  fontSize: 16,
                  color: isPresent ? color : 'var(--success)',
                }}>
                  {isPresent ? '\u26A0' : '\u2713'}
                </span>
                <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
                  {dosha.name}
                </span>
                <span style={{
                  fontSize: 10,
                  fontWeight: 700,
                  padding: '2px 8px',
                  borderRadius: 'var(--radius-full)',
                  background: bg,
                  color: color,
                  textTransform: 'uppercase',
                  marginLeft: 'auto',
                }}>
                  {severityLabel(dosha.severity)}
                </span>
              </div>

              {/* Affected houses */}
              {isPresent && dosha.affected_houses.length > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                  <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                    Affected Houses:
                  </span>
                  {dosha.affected_houses.map((h) => (
                    <span
                      key={h}
                      style={{
                        fontSize: 11,
                        fontWeight: 700,
                        color: 'var(--text-secondary)',
                        background: 'var(--bg-primary)',
                        padding: '1px 6px',
                        borderRadius: 'var(--radius-sm)',
                      }}
                    >
                      House {h}
                    </span>
                  ))}
                </div>
              )}

              {/* Involved planets */}
              {dosha.involved_planets.length > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
                  <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Planets:</span>
                  {dosha.involved_planets.map((p) => (
                    <span
                      key={p}
                      style={{
                        fontSize: 11,
                        fontWeight: 600,
                        color: 'var(--text-secondary)',
                        background: 'var(--bg-primary)',
                        padding: '1px 6px',
                        borderRadius: 'var(--radius-sm)',
                      }}
                    >
                      {p}
                    </span>
                  ))}
                </div>
              )}

              {/* Description */}
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                {dosha.description}
              </div>

              {/* Cancellation factors */}
              {dosha.cancellation_factors.length > 0 && (
                <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid var(--table-border)' }}>
                  <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--success)', marginBottom: 4 }}>
                    Mitigating Factors:
                  </div>
                  {dosha.cancellation_factors.map((f, fi) => (
                    <div key={fi} style={{ fontSize: 11, color: 'var(--text-secondary)', paddingLeft: 12, lineHeight: 1.6 }}>
                      {'\u2022'} {f}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Summary */}
      <div style={{
        marginTop: 20,
        padding: '12px 16px',
        borderRadius: 'var(--radius-md)',
        background: presentDoshas.length === 0 ? 'var(--success-bg)' : 'var(--warning-bg)',
        fontSize: 13,
        fontWeight: 600,
        color: presentDoshas.length === 0 ? 'var(--success-text)' : 'var(--warning-text)',
      }}>
        {presentDoshas.length === 0
          ? 'No doshas detected in this chart.'
          : `${presentDoshas.length} dosha${presentDoshas.length > 1 ? 's' : ''} detected. Consult a qualified astrologer for personalized remedies.`
        }
      </div>
    </div>
  )
}
