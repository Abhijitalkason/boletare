import React, { useState, useEffect } from 'react'
import { api, KundliData, PlanetData } from '../api/client'
import NorthIndianChart from '../components/NorthIndianChart'
import SouthIndianChart from '../components/SouthIndianChart'
import AshtakavargaGrid from '../components/AshtakavargaGrid'
import DashaTimeline from '../components/DashaTimeline'
import YogaSection from '../components/YogaSection'
import DoshaSection from '../components/DoshaSection'
import {
  SIGN_NAMES, SIGN_ABBR, SIGN_SYMBOLS, PLANET_COLORS, DIGNITY_COLORS,
  formatDegrees, normalizeSign, SIGN_NAME_TO_NUM,
} from '../components/chartConstants'

// ═══════════════════════════════════════════════════════════════
// KundliPage — AstroTalk-style Free Kundli Analysis
//
// Layout: Birth form (top) + Sidebar (left) + Content (right)
// Sections: Basic Details, Planets, Chart, Ashtakavarga, Dasha, Yogas, Doshas
// ═══════════════════════════════════════════════════════════════

type SectionId = 'basic' | 'planets' | 'chart' | 'ashtakavarga' | 'dasha' | 'yogas' | 'doshas'

const SECTIONS: { id: SectionId; label: string; icon: string }[] = [
  { id: 'basic',        label: 'Basic Details',  icon: '\u2139' },
  { id: 'planets',      label: 'Planets',        icon: '\u2609' },
  { id: 'chart',        label: 'Kundli Chart',   icon: '\u2B21' },
  { id: 'ashtakavarga', label: 'Ashtakavarga',   icon: '\u25A6' },
  { id: 'dasha',        label: 'Dasha',          icon: '\u29D7' },
  { id: 'yogas',        label: 'Yogas',          icon: '\u2605' },
  { id: 'doshas',       label: 'Doshas',         icon: '\u26A0' },
]

// ── Shared styles ───────────────────────────────────────────────
const card: React.CSSProperties = {
  background: 'var(--card-bg)',
  border: '1px solid var(--card-border)',
  borderRadius: 'var(--radius-lg)',
  padding: 24,
  boxShadow: 'var(--shadow-md)',
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

const lbl: React.CSSProperties = {
  display: 'block',
  fontSize: 11,
  fontWeight: 600,
  color: 'var(--text-tertiary)',
  marginBottom: 4,
  textTransform: 'uppercase',
  letterSpacing: 0.5,
}

const inp: React.CSSProperties = {
  width: '100%',
  padding: '8px 12px',
  borderRadius: 'var(--radius-md)',
  border: '1px solid var(--border-primary)',
  background: 'var(--bg-secondary)',
  color: 'var(--text-primary)',
  fontSize: 14,
  outline: 'none',
  boxSizing: 'border-box' as const,
}

function getAscSignNum(data: KundliData): number {
  if (typeof data.ascendant_sign === 'number') return data.ascendant_sign
  return SIGN_NAME_TO_NUM[data.ascendant_sign?.toUpperCase()] || 1
}

// ── Birth Data Form ─────────────────────────────────────────────
function BirthForm({ onComputed, loading }: {
  onComputed: (data: KundliData) => void
  loading: boolean
}) {
  const [name, setName] = useState('Abhijit')
  const [birthDate, setBirthDate] = useState('1990-01-15')
  const [birthTime, setBirthTime] = useState('14:30')
  const [birthPlace, setBirthPlace] = useState('Pune, India')
  const [latitude, setLatitude] = useState('18.5204')
  const [longitude, setLongitude] = useState('73.8567')
  const [timezone, setTimezone] = useState('5.5')
  const [ayanamsha, setAyanamsha] = useState('lahiri')
  const [error, setError] = useState('')

  const handleSubmit = async () => {
    setError('')
    if (!name.trim() || !birthDate) {
      setError('Name and birth date are required.')
      return
    }
    try {
      const result = await api.computeKundli({
        name: name.trim(),
        birth_date: birthDate,
        birth_time: birthTime || undefined,
        birth_place: birthPlace || undefined,
        latitude: parseFloat(latitude) || 28.6,
        longitude: parseFloat(longitude) || 77.2,
        timezone_offset: parseFloat(timezone) || 5.5,
        birth_time_tier: 2,
        ayanamsha,
      })
      onComputed(result)
    } catch (e: any) {
      setError(e.message || 'Computation failed')
    }
  }

  return (
    <div style={{ ...card, marginBottom: 24 }}>
      <div style={{ fontSize: 18, fontWeight: 800, color: 'var(--text-primary)', marginBottom: 16 }}>
        Free Kundli Analysis
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
        gap: 12,
        marginBottom: 16,
      }}>
        <div>
          <label style={lbl}>Name *</label>
          <input style={inp} value={name} onChange={(e) => setName(e.target.value)} placeholder="Full name" />
        </div>
        <div>
          <label style={lbl}>Birth Date *</label>
          <input style={inp} type="date" value={birthDate} onChange={(e) => setBirthDate(e.target.value)} />
        </div>
        <div>
          <label style={lbl}>Birth Time</label>
          <input style={inp} type="time" value={birthTime} onChange={(e) => setBirthTime(e.target.value)} />
        </div>
        <div>
          <label style={lbl}>Birth Place</label>
          <input style={inp} value={birthPlace} onChange={(e) => setBirthPlace(e.target.value)} placeholder="City, Country" />
        </div>
        <div>
          <label style={lbl}>Latitude</label>
          <input style={inp} type="number" step="0.01" value={latitude} onChange={(e) => setLatitude(e.target.value)} />
        </div>
        <div>
          <label style={lbl}>Longitude</label>
          <input style={inp} type="number" step="0.01" value={longitude} onChange={(e) => setLongitude(e.target.value)} />
        </div>
        <div>
          <label style={lbl}>Timezone (UTC)</label>
          <input style={inp} type="number" step="0.5" value={timezone} onChange={(e) => setTimezone(e.target.value)} />
        </div>
        <div>
          <label style={lbl}>Ayanamsha</label>
          <select style={inp} value={ayanamsha} onChange={(e) => setAyanamsha(e.target.value)}>
            <option value="lahiri">Lahiri</option>
            <option value="kp">Krishnamurti (KP)</option>
          </select>
        </div>
      </div>

      {error && (
        <div style={{
          fontSize: 13, color: 'var(--danger)', marginBottom: 12,
          padding: '8px 12px', background: 'var(--danger-bg)', borderRadius: 'var(--radius-md)',
        }}>
          {error}
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={loading}
        style={{
          background: loading ? 'var(--bg-tertiary)' : 'var(--accent-gradient)',
          color: '#fff',
          border: 'none',
          borderRadius: 'var(--radius-md)',
          padding: '10px 28px',
          fontSize: 14,
          fontWeight: 700,
          cursor: loading ? 'not-allowed' : 'pointer',
          transition: 'all 0.2s',
        }}
      >
        {loading ? 'Computing...' : 'Generate Kundli'}
      </button>
    </div>
  )
}

// ── Birth Summary Bar ───────────────────────────────────────────
function BirthSummary({ data, onEdit }: { data: KundliData; onEdit: () => void }) {
  return (
    <div style={{
      ...card,
      marginBottom: 24,
      display: 'flex',
      alignItems: 'center',
      gap: 16,
      padding: '14px 20px',
      flexWrap: 'wrap',
    }}>
      <div style={{ fontWeight: 700, fontSize: 16, color: 'var(--text-primary)' }}>
        {data.name}
      </div>
      <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
        {data.birth_date}
        {data.birth_time ? ` | ${data.birth_time}` : ''}
        {data.birth_place ? ` | ${data.birth_place}` : ''}
      </div>
      <div style={{
        fontSize: 12, fontWeight: 700, color: 'var(--accent-primary)',
        background: 'var(--accent-subtle)', padding: '3px 10px',
        borderRadius: 'var(--radius-full)',
      }}>
        {SIGN_NAMES[getAscSignNum(data)] || data.ascendant_sign} Ascendant
      </div>
      <button
        onClick={onEdit}
        style={{
          marginLeft: 'auto',
          background: 'var(--bg-tertiary)',
          border: '1px solid var(--border-primary)',
          borderRadius: 'var(--radius-md)',
          padding: '5px 14px',
          fontSize: 12,
          fontWeight: 600,
          color: 'var(--text-secondary)',
          cursor: 'pointer',
        }}
      >
        Edit
      </button>
    </div>
  )
}

// ── Planet Table ─────────────────────────────────────────────────
function PlanetTable({ planets, label }: { planets: PlanetData[]; label: string }) {
  return (
    <div>
      <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 12 }}>
        {label}
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 700 }}>
          <thead>
            <tr>
              {['Planet', 'Sign', 'House', 'Degrees', 'Nakshatra', 'Pada', 'Dignity', 'Score', 'R'].map((h) => (
                <th key={h} style={th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {planets.map((p) => {
              const signNum = normalizeSign(p.sign)
              const dignityColor = DIGNITY_COLORS[p.dignity] || 'var(--text-secondary)'
              const planetColor = PLANET_COLORS[p.planet] || 'var(--text-secondary)'
              return (
                <tr key={p.planet}>
                  <td style={{ ...td, fontWeight: 700, color: planetColor }}>{p.planet}</td>
                  <td style={td}>
                    {SIGN_SYMBOLS[signNum]} {SIGN_ABBR[signNum]}
                  </td>
                  <td style={{ ...td, fontWeight: 600 }}>{p.house}</td>
                  <td style={td}>{formatDegrees(p.sign_degrees)}</td>
                  <td style={td}>{p.nakshatra}</td>
                  <td style={{ ...td, textAlign: 'center' }}>{p.nakshatra_pada}</td>
                  <td style={{ ...td, color: dignityColor, fontWeight: 600, textTransform: 'capitalize' }}>{p.dignity}</td>
                  <td style={{ ...td, textAlign: 'center' }}>{p.dignity_score.toFixed(2)}</td>
                  <td style={{ ...td, color: p.is_retrograde ? 'var(--danger)' : 'var(--text-tertiary)', fontWeight: 700 }}>
                    {p.is_retrograde ? 'R' : '-'}
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

// ── Section Content Renderers ────────────────────────────────────

function BasicDetailsSection({ data }: { data: KundliData }) {
  const ascNum = getAscSignNum(data)
  const qf = data.quality_flags || {}

  const details = [
    { label: 'Name', value: data.name },
    { label: 'Birth Date', value: data.birth_date },
    { label: 'Birth Time', value: data.birth_time || 'Not provided' },
    { label: 'Birth Place', value: data.birth_place || 'Not provided' },
    { label: 'Ascendant', value: `${SIGN_NAMES[ascNum]} ${SIGN_SYMBOLS[ascNum]}` },
    { label: 'Ascendant Degrees', value: `${(data.ascendant_arcsec / 3600).toFixed(2)}\u00B0` },
    { label: 'Lagna Mode', value: data.lagna_mode === 'chandra' ? 'Chandra Lagna' : 'Standard' },
    { label: 'Birth Time Tier', value: qf.birth_time_tier ? `Tier ${qf.birth_time_tier}` : '-' },
    { label: 'Computed At', value: data.computed_at ? new Date(data.computed_at).toLocaleString() : '-' },
  ]

  return (
    <div>
      <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 16 }}>
        Basic Details
      </div>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
        gap: 12,
      }}>
        {details.map((d) => (
          <div
            key={d.label}
            style={{
              background: 'var(--bg-inset)',
              borderRadius: 'var(--radius-md)',
              padding: '10px 14px',
            }}
          >
            <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 2 }}>
              {d.label}
            </div>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)' }}>
              {d.value}
            </div>
          </div>
        ))}
      </div>

      {/* Quality Flags */}
      {qf && (
        <div style={{ marginTop: 20 }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-tertiary)', marginBottom: 8 }}>
            Quality Flags
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {Object.entries(qf).map(([key, val]) => (
              <span
                key={key}
                style={{
                  fontSize: 11,
                  padding: '3px 10px',
                  borderRadius: 'var(--radius-full)',
                  background: val === true ? 'var(--warning-bg)' : 'var(--bg-inset)',
                  color: val === true ? 'var(--warning-text)' : 'var(--text-tertiary)',
                  fontWeight: 600,
                }}
              >
                {key.replace(/_/g, ' ')}: {String(val)}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function ChartSection({ data }: { data: KundliData }) {
  const [chartStyle, setChartStyle] = useState<'north' | 'south'>('north')
  const ascNum = getAscSignNum(data)

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text-primary)' }}>
          Kundli Chart
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          {(['north', 'south'] as const).map((s) => (
            <button
              key={s}
              onClick={() => setChartStyle(s)}
              style={{
                background: chartStyle === s ? 'var(--accent-subtle)' : 'var(--bg-inset)',
                color: chartStyle === s ? 'var(--accent-primary)' : 'var(--text-tertiary)',
                border: 'none',
                borderRadius: 'var(--radius-md)',
                padding: '4px 12px',
                fontSize: 12,
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              {s === 'north' ? 'North Indian' : 'South Indian'}
            </button>
          ))}
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))',
        gap: 20,
      }}>
        <div>
          {chartStyle === 'north' ? (
            <NorthIndianChart planets={data.planets} ascendantSign={ascNum} title="Rasi Chart (D-1)" size={380} />
          ) : (
            <SouthIndianChart planets={data.planets} ascendantSign={ascNum} title="Rasi Chart (D-1)" size={380} />
          )}
        </div>
        <div>
          {chartStyle === 'north' ? (
            <NorthIndianChart planets={data.navamsha_planets} ascendantSign={ascNum} title="Navamsha (D-9)" size={380} />
          ) : (
            <SouthIndianChart planets={data.navamsha_planets} ascendantSign={ascNum} title="Navamsha (D-9)" size={380} />
          )}
        </div>
      </div>
    </div>
  )
}

// ── Main KundliPage ─────────────────────────────────────────────

export default function KundliPage() {
  const [data, setData] = useState<KundliData | null>(null)
  const [loading, setLoading] = useState(false)
  const [editing, setEditing] = useState(true)
  const [activeSection, setActiveSection] = useState<SectionId>('basic')
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768)

  useEffect(() => {
    const handler = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
  }, [])

  const handleComputed = (result: KundliData) => {
    setData(result)
    setEditing(false)
    setLoading(false)
    setActiveSection('basic')
  }

  const handleComputeStart = (result: KundliData) => {
    handleComputed(result)
  }

  const renderContent = () => {
    if (!data) return null

    switch (activeSection) {
      case 'basic':
        return <BasicDetailsSection data={data} />
      case 'planets':
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
            <PlanetTable planets={data.planets} label="Rasi Planets" />
            {data.navamsha_planets.length > 0 && (
              <PlanetTable planets={data.navamsha_planets} label="Navamsha Planets" />
            )}
          </div>
        )
      case 'chart':
        return <ChartSection data={data} />
      case 'ashtakavarga':
        return <AshtakavargaGrid ashtakavarga={data.ashtakavarga} />
      case 'dasha':
        return <DashaTimeline dashaTree={data.dasha_tree} />
      case 'yogas':
        return <YogaSection yogas={data.yogas} />
      case 'doshas':
        return <DoshaSection doshas={data.doshas} />
      default:
        return null
    }
  }

  return (
    <div>
      {/* Birth Form or Summary */}
      {editing ? (
        <BirthForm
          onComputed={(result) => {
            setLoading(true)
            handleComputeStart(result)
          }}
          loading={loading}
        />
      ) : data ? (
        <BirthSummary data={data} onEdit={() => setEditing(true)} />
      ) : null}

      {/* Sidebar + Content */}
      {data && (
        <div style={{
          display: isMobile ? 'block' : 'flex',
          gap: 20,
          alignItems: 'flex-start',
        }}>
          {/* Sidebar / Mobile tabs */}
          {isMobile ? (
            <div style={{
              display: 'flex',
              gap: 6,
              overflowX: 'auto',
              paddingBottom: 12,
              marginBottom: 16,
              scrollbarWidth: 'thin',
            }}>
              {SECTIONS.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setActiveSection(s.id)}
                  style={{
                    flexShrink: 0,
                    background: activeSection === s.id ? 'var(--accent-subtle)' : 'var(--bg-inset)',
                    color: activeSection === s.id ? 'var(--accent-primary)' : 'var(--text-secondary)',
                    border: activeSection === s.id ? '1px solid var(--accent-primary)' : '1px solid transparent',
                    borderRadius: 'var(--radius-md)',
                    padding: '8px 14px',
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                    transition: 'all 0.15s',
                  }}
                >
                  {s.icon} {s.label}
                </button>
              ))}
            </div>
          ) : (
            <div style={{
              width: 200,
              flexShrink: 0,
              position: 'sticky',
              top: 80,
            }}>
              <div style={{
                ...card,
                padding: 8,
                display: 'flex',
                flexDirection: 'column',
                gap: 2,
              }}>
                {SECTIONS.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => setActiveSection(s.id)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      padding: '10px 14px',
                      borderRadius: 'var(--radius-md)',
                      border: 'none',
                      background: activeSection === s.id ? 'var(--accent-subtle)' : 'transparent',
                      color: activeSection === s.id ? 'var(--accent-primary)' : 'var(--text-secondary)',
                      fontWeight: activeSection === s.id ? 700 : 500,
                      fontSize: 13,
                      cursor: 'pointer',
                      transition: 'all 0.15s',
                      textAlign: 'left',
                      width: '100%',
                    }}
                  >
                    <span style={{ fontSize: 16, width: 20, textAlign: 'center' }}>{s.icon}</span>
                    {s.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Content Area */}
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={card}>
              {renderContent()}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
