import React, { useState } from 'react'
import { DashaData } from '../api/client'
import { DASHA_PLANET_COLORS } from './chartConstants'

interface Props {
  dashaTree: DashaData[]
}

function parseDate(d: string): Date {
  return new Date(d)
}

function formatDate(d: string): string {
  const date = parseDate(d)
  return date.toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })
}

function formatFullDate(d: string): string {
  const date = parseDate(d)
  return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })
}

function isCurrentPeriod(start: string, end: string): boolean {
  const now = new Date()
  return parseDate(start) <= now && now <= parseDate(end)
}

function yearsDuration(start: string, end: string): string {
  const ms = parseDate(end).getTime() - parseDate(start).getTime()
  const years = ms / (1000 * 60 * 60 * 24 * 365.25)
  if (years >= 1) return `${years.toFixed(1)}y`
  const months = years * 12
  return `${months.toFixed(0)}m`
}

export default function DashaTimeline({ dashaTree }: Props) {
  const [expandedMD, setExpandedMD] = useState<number | null>(null)
  const [expandedAD, setExpandedAD] = useState<number | null>(null)

  if (!dashaTree || dashaTree.length === 0) {
    return <div style={{ color: 'var(--text-tertiary)', padding: 20, textAlign: 'center' }}>No dasha data available.</div>
  }

  // Calculate overall timeline span
  const allDates = dashaTree.flatMap((d) => [parseDate(d.start_date).getTime(), parseDate(d.end_date).getTime()])
  const minTime = Math.min(...allDates)
  const maxTime = Math.max(...allDates)
  const totalSpan = maxTime - minTime || 1
  const now = Date.now()
  const nowPercent = Math.max(0, Math.min(100, ((now - minTime) / totalSpan) * 100))

  return (
    <div>
      {/* Visual Timeline Bar */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>
          Mahadasha Timeline
        </div>
        <div style={{ position: 'relative', height: 40, borderRadius: 'var(--radius-md)', overflow: 'hidden', background: 'var(--bg-inset)', border: '1px solid var(--table-border)' }}>
          {dashaTree.map((d, i) => {
            const startPct = ((parseDate(d.start_date).getTime() - minTime) / totalSpan) * 100
            const endPct = ((parseDate(d.end_date).getTime() - minTime) / totalSpan) * 100
            const widthPct = endPct - startPct
            const color = DASHA_PLANET_COLORS[d.planet] || 'var(--text-tertiary)'
            const isCurrent = isCurrentPeriod(d.start_date, d.end_date)

            return (
              <div
                key={i}
                title={`${d.planet} Mahadasha: ${formatFullDate(d.start_date)} — ${formatFullDate(d.end_date)}`}
                onClick={() => setExpandedMD(expandedMD === i ? null : i)}
                style={{
                  position: 'absolute',
                  left: `${startPct}%`,
                  width: `${widthPct}%`,
                  top: 0,
                  bottom: 0,
                  background: color,
                  opacity: isCurrent ? 1 : 0.5,
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderRight: '1px solid var(--bg-primary)',
                  transition: 'opacity 0.2s',
                  boxShadow: isCurrent ? `0 0 12px ${color}60` : 'none',
                }}
              >
                {widthPct > 6 && (
                  <span style={{ fontSize: 10, fontWeight: 700, color: '#fff', textShadow: '0 1px 2px rgba(0,0,0,0.5)', whiteSpace: 'nowrap', overflow: 'hidden' }}>
                    {d.planet}
                  </span>
                )}
              </div>
            )
          })}

          {/* Current date marker */}
          {nowPercent > 0 && nowPercent < 100 && (
            <div style={{
              position: 'absolute',
              left: `${nowPercent}%`,
              top: -4,
              bottom: -4,
              width: 2,
              background: 'var(--danger)',
              zIndex: 2,
              boxShadow: '0 0 6px var(--danger)',
            }}>
              <div style={{
                position: 'absolute',
                top: -14,
                left: -12,
                fontSize: 8,
                fontWeight: 700,
                color: 'var(--danger)',
                whiteSpace: 'nowrap',
              }}>
                NOW
              </div>
            </div>
          )}
        </div>
        {/* Time axis labels */}
        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 4 }}>
          <span style={{ fontSize: 9, color: 'var(--text-tertiary)' }}>
            {formatDate(dashaTree[0].start_date)}
          </span>
          <span style={{ fontSize: 9, color: 'var(--text-tertiary)' }}>
            {formatDate(dashaTree[dashaTree.length - 1].end_date)}
          </span>
        </div>
      </div>

      {/* Expandable Dasha Periods */}
      <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>
        Dasha Periods
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {dashaTree.map((md, mdIdx) => {
          const isCurrent = isCurrentPeriod(md.start_date, md.end_date)
          const isExpanded = expandedMD === mdIdx
          const color = DASHA_PLANET_COLORS[md.planet] || 'var(--text-tertiary)'

          return (
            <div key={mdIdx}>
              {/* Mahadasha row */}
              <div
                onClick={() => { setExpandedMD(isExpanded ? null : mdIdx); setExpandedAD(null) }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '10px 14px',
                  borderRadius: 'var(--radius-md)',
                  background: isCurrent ? 'var(--accent-subtle)' : 'var(--bg-inset)',
                  borderLeft: `4px solid ${color}`,
                  cursor: 'pointer',
                  transition: 'all 0.15s',
                  boxShadow: isCurrent ? 'var(--shadow-glow)' : 'none',
                }}
              >
                <div style={{
                  width: 8, height: 8, borderRadius: '50%',
                  background: color,
                  boxShadow: isCurrent ? `0 0 6px ${color}` : 'none',
                }} />
                <div style={{ flex: 1 }}>
                  <span style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)' }}>
                    {md.planet}
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--text-tertiary)', marginLeft: 8 }}>
                    Mahadasha
                  </span>
                  {isCurrent && (
                    <span style={{
                      fontSize: 9, fontWeight: 700, color: 'var(--accent-primary)',
                      background: 'var(--accent-subtle)', padding: '2px 6px',
                      borderRadius: 'var(--radius-full)', marginLeft: 8,
                    }}>
                      ACTIVE
                    </span>
                  )}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-tertiary)', textAlign: 'right' }}>
                  <div>{formatDate(md.start_date)} — {formatDate(md.end_date)}</div>
                  <div style={{ fontSize: 10, marginTop: 1 }}>{yearsDuration(md.start_date, md.end_date)}</div>
                </div>
                <div style={{
                  transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
                  transition: 'transform 0.2s',
                  fontSize: 12,
                  color: 'var(--text-tertiary)',
                }}>
                  {'\u25B6'}
                </div>
              </div>

              {/* Antardasha sub-periods */}
              {isExpanded && md.sub_periods && md.sub_periods.length > 0 && (
                <div style={{ marginLeft: 24, marginTop: 4, display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {md.sub_periods.map((ad, adIdx) => {
                    const adCurrent = isCurrentPeriod(ad.start_date, ad.end_date)
                    const adExpanded = expandedAD === adIdx
                    const adColor = DASHA_PLANET_COLORS[ad.planet] || 'var(--text-tertiary)'

                    return (
                      <div key={adIdx}>
                        <div
                          onClick={() => setExpandedAD(adExpanded ? null : adIdx)}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: 8,
                            padding: '7px 12px',
                            borderRadius: 'var(--radius-sm)',
                            background: adCurrent ? 'var(--accent-subtle)' : 'transparent',
                            borderLeft: `3px solid ${adColor}`,
                            cursor: ad.sub_periods?.length ? 'pointer' : 'default',
                            transition: 'all 0.15s',
                          }}
                        >
                          <div style={{
                            width: 6, height: 6, borderRadius: '50%',
                            background: adColor, opacity: 0.7,
                          }} />
                          <div style={{ flex: 1 }}>
                            <span style={{ fontWeight: 600, fontSize: 12, color: 'var(--text-primary)' }}>
                              {ad.planet}
                            </span>
                            <span style={{ fontSize: 10, color: 'var(--text-tertiary)', marginLeft: 6 }}>
                              AD
                            </span>
                            {adCurrent && (
                              <span style={{
                                fontSize: 8, fontWeight: 700, color: 'var(--success)',
                                marginLeft: 6,
                              }}>
                                ACTIVE
                              </span>
                            )}
                          </div>
                          <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
                            {formatDate(ad.start_date)} — {formatDate(ad.end_date)} ({yearsDuration(ad.start_date, ad.end_date)})
                          </div>
                          {ad.sub_periods && ad.sub_periods.length > 0 && (
                            <div style={{
                              transform: adExpanded ? 'rotate(90deg)' : 'rotate(0deg)',
                              transition: 'transform 0.2s',
                              fontSize: 10,
                              color: 'var(--text-tertiary)',
                            }}>
                              {'\u25B6'}
                            </div>
                          )}
                        </div>

                        {/* Pratyantardasha */}
                        {adExpanded && ad.sub_periods && ad.sub_periods.length > 0 && (
                          <div style={{ marginLeft: 20, marginTop: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
                            {ad.sub_periods.map((pad2, padIdx) => {
                              const padCurrent = isCurrentPeriod(pad2.start_date, pad2.end_date)
                              return (
                                <div
                                  key={padIdx}
                                  style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 6,
                                    padding: '4px 10px',
                                    borderRadius: 'var(--radius-sm)',
                                    background: padCurrent ? 'var(--accent-subtle)' : 'transparent',
                                    fontSize: 11,
                                  }}
                                >
                                  <div style={{
                                    width: 4, height: 4, borderRadius: '50%',
                                    background: DASHA_PLANET_COLORS[pad2.planet] || 'var(--text-tertiary)',
                                    opacity: 0.6,
                                  }} />
                                  <span style={{ fontWeight: 600, color: 'var(--text-secondary)', minWidth: 55 }}>
                                    {pad2.planet}
                                  </span>
                                  <span style={{ color: 'var(--text-tertiary)', fontSize: 10 }}>
                                    PAD
                                  </span>
                                  {padCurrent && (
                                    <span style={{ fontSize: 8, fontWeight: 700, color: 'var(--success)' }}>
                                      ACTIVE
                                    </span>
                                  )}
                                  <span style={{ marginLeft: 'auto', fontSize: 10, color: 'var(--text-tertiary)' }}>
                                    {formatDate(pad2.start_date)} — {formatDate(pad2.end_date)}
                                  </span>
                                </div>
                              )
                            })}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
