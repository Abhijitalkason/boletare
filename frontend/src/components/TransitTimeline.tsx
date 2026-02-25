import React from 'react'

interface TransitMonth {
  month: string
  jupiter_sign: string
  saturn_sign: string
  jupiter_in_favorable: boolean
  saturn_in_favorable: boolean
  double_transit_active: boolean
  transit_bav_score: number
}

interface TransitTimelineProps {
  timeline: TransitMonth[]
  peakMonth?: string | null
}

export default function TransitTimeline({ timeline, peakMonth }: TransitTimelineProps) {
  const months = timeline || []
  const bavScores = months.map((m) => m.transit_bav_score || 0)
  const maxVal = Math.max(...bavScores, 0.01)
  const activeCount = months.filter((m) => m.double_transit_active).length

  const container: React.CSSProperties = {
    background: 'var(--card-bg)',
    border: '1px solid var(--card-border)',
    borderRadius: 'var(--radius-lg)',
    padding: 20,
    boxShadow: 'var(--shadow-md)',
  }

  if (months.length === 0) {
    return (
      <div style={container}>
        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: 1 }}>Transit Windows</div>
        <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginTop: 4, marginBottom: 16 }}>24-Month Outlook</div>
        <div style={{ color: 'var(--text-tertiary)', fontSize: 13, textAlign: 'center', padding: '30px 0' }}>No transit timeline data available</div>
      </div>
    )
  }

  return (
    <div style={container}>
      <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: 1 }}>Transit Windows</div>
      <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginTop: 4, marginBottom: 16 }}>
        24-Month Outlook — {activeCount} Active Month{activeCount !== 1 ? 's' : ''}
        {peakMonth && <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--accent-primary)', marginLeft: 12 }}>Peak: {peakMonth}</span>}
      </div>

      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 2, height: 100, padding: '0 2px' }}>
        {months.map((m, i) => {
          const isPeak = m.month === peakMonth
          const isActive = m.double_transit_active
          const barH = isActive ? Math.max((m.transit_bav_score / maxVal) * 80, 16) + 4 : 4

          let clr = 'var(--bar-inactive)'
          if (isPeak) clr = 'var(--accent-primary)'
          else if (isActive) clr = 'var(--success)'
          else if (m.jupiter_in_favorable || m.saturn_in_favorable) clr = 'var(--warning)'

          return (
            <div
              key={i}
              style={{
                flex: '1 1 0',
                height: barH,
                background: clr,
                borderRadius: '3px 3px 0 0',
                transition: 'height 0.4s ease-out',
                position: 'relative',
                cursor: 'default',
                minWidth: 0,
                opacity: isActive || isPeak ? 1 : 0.5,
              }}
              title={`${m.month}: Jup ${m.jupiter_sign} | Sat ${m.saturn_sign}${isActive ? ' | DOUBLE TRANSIT' : ''}${isPeak ? ' (Peak)' : ''} | BAV: ${m.transit_bav_score.toFixed(2)}`}
            >
              {isPeak && (
                <div style={{ position: 'absolute', top: -10, left: '50%', transform: 'translateX(-50%)', width: 0, height: 0, borderLeft: '4px solid transparent', borderRight: '4px solid transparent', borderTop: '6px solid var(--accent-primary)' }} />
              )}
            </div>
          )
        })}
      </div>

      <div style={{ display: 'flex', gap: 2, padding: '4px 2px 0' }}>
        {months.map((m, i) => {
          const short = new Date(m.month + '-01').toLocaleDateString('en', { month: 'short', year: '2-digit' })
          return (
            <div key={i} style={{ flex: '1 1 0', fontSize: 7, color: 'var(--text-tertiary)', textAlign: 'center', minWidth: 0, overflow: 'hidden', whiteSpace: 'nowrap' }}>
              {i % 3 === 0 ? short : ''}
            </div>
          )
        })}
      </div>

      <div style={{ display: 'flex', gap: 16, marginTop: 14, fontSize: 11, color: 'var(--text-secondary)', alignItems: 'center', flexWrap: 'wrap' }}>
        {[
          { color: 'var(--success)', label: 'Double Transit' },
          { color: 'var(--warning)', label: 'Partial' },
          { color: 'var(--bar-inactive)', label: 'Inactive' },
          { color: 'var(--accent-primary)', label: 'Peak Month' },
        ].map((l) => (
          <span key={l.label} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <span style={{ width: 10, height: 10, borderRadius: 2, background: l.color, display: 'inline-block' }} />
            {l.label}
          </span>
        ))}
      </div>
    </div>
  )
}
