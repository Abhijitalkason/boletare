import React, { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, PredictionListItem } from '../api/client'
import { ConfidenceLevel, CONFIDENCE_COLORS, EVENT_ICONS } from '../types'

export default function HistoryPage() {
  const [userId, setUserId] = useState('')
  const [predictions, setPredictions] = useState<PredictionListItem[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async () => {
    const id = parseInt(userId.trim(), 10)
    if (isNaN(id) || id <= 0) { setError('Please enter a valid user ID'); return }
    setError(null)
    setLoading(true)
    setPredictions(null)
    try {
      setPredictions(await api.getUserPredictions(id))
    } catch (err: any) {
      setError(err.message || 'Failed to fetch predictions')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ maxWidth: 720, margin: '0 auto' }} className="animate-fade-in">
      <h1 style={{ fontSize: 26, fontWeight: 800, color: 'var(--text-primary)', margin: '0 0 24px' }}>
        Prediction History
      </h1>

      {/* Search */}
      <div style={{ background: 'var(--card-bg)', border: '1px solid var(--card-border)', borderRadius: 'var(--radius-lg)', padding: 24, boxShadow: 'var(--shadow-md)', marginBottom: 24 }}>
        <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 5, flex: 1 }}>
            <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>User ID</label>
            <input
              style={{ padding: '10px 14px', borderRadius: 'var(--radius-md)', border: '1px solid var(--input-border)', fontSize: 14, outline: 'none', background: 'var(--input-bg)', color: 'var(--input-text)' }}
              type="number"
              min="1"
              placeholder="Enter user ID"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={loading}
            style={{ padding: '10px 24px', borderRadius: 'var(--radius-md)', border: 'none', background: 'var(--accent-gradient)', color: '#fff', fontSize: 14, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.6 : 1, whiteSpace: 'nowrap', boxShadow: 'var(--shadow-glow)' }}
          >
            {loading ? 'Searching...' : 'Look Up'}
          </button>
        </div>
      </div>

      {error && (
        <div style={{ background: 'var(--danger-bg)', color: 'var(--danger-text)', padding: '10px 14px', borderRadius: 'var(--radius-md)', fontSize: 13, marginBottom: 16, border: '1px solid rgba(239,68,68,0.2)' }}>
          {error}
        </div>
      )}

      {predictions !== null && predictions.length === 0 && (
        <div style={{ textAlign: 'center', padding: 48, color: 'var(--text-tertiary)', fontSize: 14 }}>
          No predictions found. Run one from the <Link to="/" style={{ color: 'var(--accent-text)', fontWeight: 600 }}>Home page</Link>.
        </div>
      )}

      {predictions && predictions.length > 0 && (
        <div>
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginBottom: 12 }}>
            {predictions.length} prediction{predictions.length !== 1 ? 's' : ''} found
          </div>
          <div className="stagger-children" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {predictions.map((p) => {
              const confColor = CONFIDENCE_COLORS[p.confidence_level as ConfidenceLevel] || '#94a3b8'
              const icon = EVENT_ICONS[p.event_type] || ''

              return (
                <Link
                  key={p.id}
                  to={`/prediction/${p.id}`}
                  style={{
                    background: 'var(--card-bg)',
                    border: '1px solid var(--card-border)',
                    borderRadius: 'var(--radius-lg)',
                    padding: '16px 20px',
                    boxShadow: 'var(--shadow-sm)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    textDecoration: 'none',
                    color: 'inherit',
                    transition: 'transform 0.15s ease, box-shadow 0.15s ease',
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-1px)'; e.currentTarget.style.boxShadow = 'var(--shadow-lg)' }}
                  onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = 'var(--shadow-sm)' }}
                >
                  <div>
                    <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', textTransform: 'capitalize' }}>{icon} {p.event_type}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-tertiary)', marginTop: 3 }}>
                      Query: {p.query_date}{p.created_at && ` \u00B7 ${new Date(p.created_at).toLocaleDateString()}`}
                    </div>
                    <div style={{ marginTop: 6, display: 'flex', gap: 6 }}>
                      <span style={{ display: 'inline-block', padding: '2px 10px', borderRadius: 'var(--radius-full)', fontSize: 10, fontWeight: 700, color: '#fff', background: confColor, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                        {p.confidence_level}
                      </span>
                      {p.is_retrospective && (
                        <span style={{ display: 'inline-block', padding: '2px 10px', borderRadius: 'var(--radius-full)', fontSize: 10, fontWeight: 700, color: 'var(--accent-text)', background: 'var(--accent-subtle)' }}>Retrospective</span>
                      )}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: 22, fontWeight: 800, color: confColor }}>{p.convergence_score.toFixed(2)}</div>
                    <div style={{ fontSize: 10, color: 'var(--text-tertiary)', marginTop: 2 }}>convergence</div>
                  </div>
                </Link>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
