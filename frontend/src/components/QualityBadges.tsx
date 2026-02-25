import React from 'react'

interface QualityBadgesProps {
  qualityFlags: Record<string, any>
  isRetrospective?: boolean
}

interface BadgeConfig {
  label: string
  color: string
  bgColor: string
}

function getBadges(flags: Record<string, any>, isRetrospective?: boolean): BadgeConfig[] {
  const badges: BadgeConfig[] = []

  const tier = flags.birth_time_tier ?? flags.birthTimeTier
  if (tier !== undefined) {
    const tierMap: Record<number, BadgeConfig> = {
      1: { label: 'Tier 1 — Exact', color: 'var(--success-text)', bgColor: 'var(--success-bg)' },
      2: { label: 'Tier 2 — Approx', color: 'var(--warning-text)', bgColor: 'var(--warning-bg)' },
      3: { label: 'Tier 3 — Estimate', color: 'var(--danger-text)', bgColor: 'var(--danger-bg)' },
    }
    badges.push(tierMap[tier] || tierMap[3])
  }

  const lagnaMode = flags.lagna_mode ?? flags.lagnaMode
  if (lagnaMode) {
    const isChandra = lagnaMode.toLowerCase().includes('chandra')
    badges.push({
      label: isChandra ? 'Chandra Lagna' : 'Standard Lagna',
      color: isChandra ? 'var(--accent-text)' : 'var(--info-text)',
      bgColor: isChandra ? 'var(--accent-subtle)' : 'var(--info-bg)',
    })
  }

  if (flags.placidus_distorted ?? flags.placidusDistorted) {
    badges.push({ label: 'Placidus Distorted', color: 'var(--warning-text)', bgColor: 'var(--warning-bg)' })
  }

  if (flags.dasha_boundary_sensitive ?? flags.dashaBoundarySensitive) {
    badges.push({ label: 'Dasha Boundary', color: 'var(--warning-text)', bgColor: 'var(--warning-bg)' })
  }

  if (flags.dasha_ambiguous ?? flags.dashaAmbiguous) {
    badges.push({ label: 'Dasha Ambiguous', color: 'var(--danger-text)', bgColor: 'var(--danger-bg)' })
  }

  if (isRetrospective) {
    badges.push({ label: 'Retrospective', color: 'var(--accent-text)', bgColor: 'var(--accent-subtle)' })
  }

  return badges
}

export default function QualityBadges({ qualityFlags, isRetrospective }: QualityBadgesProps) {
  const badges = getBadges(qualityFlags, isRetrospective)
  if (badges.length === 0) return null

  return (
    <div>
      <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 6 }}>
        Quality Flags
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
        {badges.map((b, i) => (
          <span
            key={i}
            style={{
              display: 'inline-block',
              padding: '4px 12px',
              borderRadius: 'var(--radius-full)',
              fontSize: 11,
              fontWeight: 700,
              color: b.color,
              background: b.bgColor,
              whiteSpace: 'nowrap',
            }}
          >
            {b.label}
          </span>
        ))}
      </div>
    </div>
  )
}
