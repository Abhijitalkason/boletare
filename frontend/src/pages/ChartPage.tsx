import React, { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { api, ChartData, PlanetData } from '../api/client'
import NorthIndianChart from '../components/NorthIndianChart'
import SouthIndianChart from '../components/SouthIndianChart'
import AshtakavargaGrid from '../components/AshtakavargaGrid'
import DashaTimeline from '../components/DashaTimeline'
import {
  SIGN_NAMES, SIGN_ABBR, SIGN_SYMBOLS, PLANET_COLORS, DIGNITY_COLORS,
  formatDegrees, normalizeSign, SIGN_NAME_TO_NUM,
} from '../components/chartConstants'

// ═══════════════════════════════════════════════════════════════
// ChartPage — Tabbed birth chart viewer
// Tabs: Rasi | Navamsha | Ashtakavarga | Dasha | Details
// ═══════════════════════════════════════════════════════════════

type TabId = 'rasi' | 'navamsha' | 'ashtakavarga' | 'dasha' | 'details'

const TABS: { id: TabId; label: string; icon: string }[] = [
  { id: 'rasi', label: 'Rasi (D-1)', icon: '\u2609' },
  { id: 'navamsha', label: 'Navamsha (D-9)', icon: '\u2606' },
  { id: 'ashtakavarga', label: 'Ashtakavarga', icon: '\u25A6' },
  { id: 'dasha', label: 'Dasha', icon: '\u29D7' },
  { id: 'details', label: 'Details', icon: '\u2630' },
]

const section: React.CSSProperties = {
  background: 'var(--card-bg)',
  border: '1px solid var(--card-border)',
  borderRadius: 'var(--radius-lg)',
  padding: 24,
  boxShadow: 'var(--shadow-md)',
  marginBottom: 20,
}

const th: React.CSSProperties = {
  textAlign: 'left',
  padding: '10px 14px',
  borderBottom: '2px solid var(--border-primary)',
  fontWeight: 700,
  color: 'var(--text-secondary)',
  fontSize: 11,
  textTransform: 'uppercase',
  letterSpacing: 0.5,
  background: 'var(--table-header-bg)',
}

const td: React.CSSProperties = {
  padding: '10px 14px',
  borderBottom: '1px solid var(--table-border)',
  color: 'var(--text-secondary)',
  fontSize: 13,
}

function fmt(v: any): string {
  if (v === null || v === undefined) return '-'
  if (typeof v === 'number') return v % 1 === 0 ? v.toString() : v.toFixed(2)
  return String(v)
}

function getAscendantSignNum(chart: ChartData): number {
  if (typeof chart.ascendant_sign === 'number') return chart.ascendant_sign
  return SIGN_NAME_TO_NUM[chart.ascendant_sign?.toUpperCase()] || 1
}

// ── Planet Details Table ───────────────────────────────────────
function PlanetTable({ planets, label }: { planets: PlanetData[]; label: string }) {
  return (
    <div style={section}>
      <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>
        {label}
      </div>
      <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>
        Planet Positions
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              {['Planet', 'Sign', 'House', 'Degrees', 'Nakshatra', 'Pada', 'Dignity', 'Score', 'Retro'].map((h) => (
                <th key={h} style={th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {planets.map((p, i) => {
              const dignity = (p.dignity || '').toLowerCase()
              const dColor = DIGNITY_COLORS[dignity] || 'var(--text-tertiary)'
              const sign = normalizeSign(p.sign)
              return (
                <tr
                  key={i}
                  style={{ transition: 'background 0.15s' }}
                  onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--table-row-hover)' }}
                  onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent' }}
                >
                  <td style={{ ...td, fontWeight: 700, color: PLANET_COLORS[p.planet] || 'var(--text-primary)' }}>
                    {p.planet}
                  </td>
                  <td style={td}>
                    {SIGN_SYMBOLS[sign]} {SIGN_NAMES[sign] || '-'}
                  </td>
                  <td style={{ ...td, fontWeight: 600 }}>{fmt(p.house)}</td>
                  <td style={td}>{formatDegrees(p.sign_degrees)}</td>
                  <td style={td}>{p.nakshatra || '-'}</td>
                  <td style={td}>{p.nakshatra_pada || '-'}</td>
                  <td style={td}>
                    <span style={{ color: dColor, fontWeight: 600, textTransform: 'capitalize' }}>
                      {p.dignity || '-'}
                    </span>
                  </td>
                  <td style={td}>{p.dignity_score != null ? p.dignity_score.toFixed(2) : '-'}</td>
                  <td style={td}>
                    {p.is_retrograde
                      ? <span style={{ color: 'var(--danger)', fontWeight: 700 }}>R</span>
                      : <span style={{ color: 'var(--text-tertiary)' }}>-</span>}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── Tab Content Components ─────────────────────────────────────

function RasiTab({ chart }: { chart: ChartData }) {
  const ascSign = getAscendantSignNum(chart)
  return (
    <div className="animate-fade-in">
      {/* Charts side by side */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 20, marginBottom: 24 }}>
        <div style={section}>
          <NorthIndianChart
            planets={chart.planets}
            ascendantSign={ascSign}
            title="North Indian Style"
            size={380}
          />
        </div>
        <div style={section}>
          <SouthIndianChart
            planets={chart.planets}
            ascendantSign={ascSign}
            title="South Indian Style"
            size={380}
          />
        </div>
      </div>
      <PlanetTable planets={chart.planets} label="Rasi Chart" />
    </div>
  )
}

function NavamshaTab({ chart }: { chart: ChartData }) {
  if (!chart.navamsha_planets || chart.navamsha_planets.length === 0) {
    return (
      <div style={{ ...section, textAlign: 'center', color: 'var(--text-tertiary)', padding: 60 }}>
        Navamsha data not available.
      </div>
    )
  }

  // For navamsha, the ascendant sign is the navamsha sign of the rasi ascendant.
  // We approximate by finding the sign of the first house or using sign of first planet.
  // The navamsha planets have their own sign values.
  const navAscSign = normalizeSign(chart.navamsha_planets[0]?.sign || 1)

  return (
    <div className="animate-fade-in">
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 20, marginBottom: 24 }}>
        <div style={section}>
          <NorthIndianChart
            planets={chart.navamsha_planets}
            ascendantSign={navAscSign}
            title="Navamsha — North Indian"
            size={380}
          />
        </div>
        <div style={section}>
          <SouthIndianChart
            planets={chart.navamsha_planets}
            ascendantSign={navAscSign}
            title="Navamsha — South Indian"
            size={380}
          />
        </div>
      </div>
      <PlanetTable planets={chart.navamsha_planets} label="D-9 Navamsha" />
    </div>
  )
}

function AshtakavargaTab({ chart }: { chart: ChartData }) {
  if (!chart.ashtakavarga || !chart.ashtakavarga.bav) {
    return (
      <div style={{ ...section, textAlign: 'center', color: 'var(--text-tertiary)', padding: 60 }}>
        Ashtakavarga data not available.
      </div>
    )
  }
  return (
    <div className="animate-fade-in" style={section}>
      <AshtakavargaGrid ashtakavarga={chart.ashtakavarga} />
    </div>
  )
}

function DashaTab({ chart }: { chart: ChartData }) {
  if (!chart.dasha_tree || chart.dasha_tree.length === 0) {
    return (
      <div style={{ ...section, textAlign: 'center', color: 'var(--text-tertiary)', padding: 60 }}>
        Dasha data not available.
      </div>
    )
  }
  return (
    <div className="animate-fade-in" style={section}>
      <DashaTimeline dashaTree={chart.dasha_tree} />
    </div>
  )
}

function DetailsTab({ chart }: { chart: ChartData }) {
  const ascSign = getAscendantSignNum(chart)
  return (
    <div className="animate-fade-in">
      {/* Overview */}
      <div style={section}>
        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>
          Chart Overview
        </div>
        <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>
          Ascendant & Configuration
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(170px, 1fr))', gap: 12 }}>
          {[
            { label: 'Ascendant', value: `${SIGN_SYMBOLS[ascSign]} ${SIGN_NAMES[ascSign]}` },
            { label: 'Ascendant Arc', value: `${chart.ascendant_arcsec}"` },
            { label: 'Lagna Mode', value: chart.lagna_mode },
          ].map((item) => (
            <div key={item.label} style={{ background: 'var(--bg-inset)', borderRadius: 'var(--radius-md)', padding: '10px 14px' }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                {item.label}
              </div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginTop: 2 }}>
                {item.value}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Houses */}
      {chart.houses && chart.houses.length > 0 && (
        <div style={section}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>
            Bhava
          </div>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>
            House Cusps
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr>
                  {['House', 'Sign', 'Degrees', 'Span'].map((h) => (
                    <th key={h} style={th}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {chart.houses.map((h, i) => {
                  const sign = normalizeSign(h.sign)
                  return (
                    <tr
                      key={i}
                      onMouseEnter={(e) => { e.currentTarget.style.background = 'var(--table-row-hover)' }}
                      onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent' }}
                    >
                      <td style={{ ...td, fontWeight: 700, color: 'var(--text-primary)' }}>
                        {h.house_number || i + 1}
                      </td>
                      <td style={td}>{SIGN_SYMBOLS[sign]} {SIGN_NAMES[sign]}</td>
                      <td style={td}>{formatDegrees(h.sign_degrees)}</td>
                      <td style={td}>{h.span_degrees?.toFixed(1)}°</td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Quality Flags */}
      {chart.quality_flags && Object.keys(chart.quality_flags).length > 0 && (
        <div style={section}>
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 }}>
            Quality
          </div>
          <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>
            Chart Quality Flags
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {Object.entries(chart.quality_flags).map(([key, value]) => (
              <div key={key} style={{ background: 'var(--bg-inset)', borderRadius: 'var(--radius-md)', padding: '6px 14px', fontSize: 12 }}>
                <span style={{ color: 'var(--text-tertiary)' }}>{key.replace(/_/g, ' ')}:</span>{' '}
                <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{fmt(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ═══════════════════════════════════════════════════════════════
// Main ChartPage Component
// ═══════════════════════════════════════════════════════════════

export default function ChartPage() {
  const { userId } = useParams<{ userId: string }>()
  const [chart, setChart] = useState<ChartData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [ayanamsha, setAyanamsha] = useState('lahiri')
  const [activeTab, setActiveTab] = useState<TabId>('rasi')

  useEffect(() => {
    if (!userId) return
    setLoading(true)
    setError(null)
    api.getChart(parseInt(userId, 10), ayanamsha)
      .then(setChart)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false))
  }, [userId, ayanamsha])

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 80, color: 'var(--text-tertiary)' }}>
        <svg width="24" height="24" viewBox="0 0 24 24" className="animate-spin" style={{ display: 'inline-block', marginBottom: 12 }}>
          <circle cx="12" cy="12" r="10" stroke="var(--accent-primary)" strokeWidth="2" fill="none" strokeDasharray="50 25" />
        </svg>
        <div>Loading birth chart...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ background: 'var(--danger-bg)', color: 'var(--danger-text)', padding: 24, borderRadius: 'var(--radius-lg)', textAlign: 'center', maxWidth: 500, margin: '60px auto' }}>
        <p style={{ margin: '0 0 16px', fontWeight: 600 }}>Failed to load chart: {error}</p>
        <Link to="/" style={{ padding: '8px 18px', borderRadius: 'var(--radius-md)', background: 'var(--accent-gradient)', color: '#fff', textDecoration: 'none', fontSize: 13, fontWeight: 600 }}>
          Back to Home
        </Link>
      </div>
    )
  }

  if (!chart) {
    return <div style={{ textAlign: 'center', padding: 80, color: 'var(--text-tertiary)' }}>Chart not found.</div>
  }

  return (
    <div style={{ maxWidth: 1000, margin: '0 auto' }} className="animate-fade-in">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
            Birth Chart
          </h1>
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginTop: 4 }}>
            User ID: {userId} &middot; Computed: {new Date(chart.computed_at).toLocaleString()}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <select
            value={ayanamsha}
            onChange={(e) => setAyanamsha(e.target.value)}
            style={{
              padding: '8px 12px',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--input-border)',
              fontSize: 13,
              background: 'var(--input-bg)',
              color: 'var(--input-text)',
            }}
          >
            <option value="lahiri">Lahiri</option>
            <option value="krishnamurti">Krishnamurti</option>
            <option value="raman">Raman</option>
          </select>
          <Link
            to="/"
            style={{
              padding: '8px 18px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--accent-gradient)',
              color: '#fff',
              textDecoration: 'none',
              fontSize: 13,
              fontWeight: 600,
            }}
          >
            New Prediction
          </Link>
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex',
        gap: 4,
        marginBottom: 24,
        borderBottom: '2px solid var(--border-primary)',
        overflowX: 'auto',
        paddingBottom: 0,
      }}>
        {TABS.map((tab) => {
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                padding: '10px 18px',
                fontSize: 13,
                fontWeight: isActive ? 700 : 500,
                color: isActive ? 'var(--accent-primary)' : 'var(--text-tertiary)',
                background: isActive ? 'var(--accent-subtle)' : 'transparent',
                border: 'none',
                borderBottom: isActive ? '2px solid var(--accent-primary)' : '2px solid transparent',
                borderRadius: 'var(--radius-md) var(--radius-md) 0 0',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                whiteSpace: 'nowrap',
                marginBottom: -2,
              }}
            >
              <span style={{ marginRight: 6 }}>{tab.icon}</span>
              {tab.label}
            </button>
          )
        })}
      </div>

      {/* Tab Content */}
      {activeTab === 'rasi' && <RasiTab chart={chart} />}
      {activeTab === 'navamsha' && <NavamshaTab chart={chart} />}
      {activeTab === 'ashtakavarga' && <AshtakavargaTab chart={chart} />}
      {activeTab === 'dasha' && <DashaTab chart={chart} />}
      {activeTab === 'details' && <DetailsTab chart={chart} />}
    </div>
  )
}
