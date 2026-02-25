import React, { useEffect, useState } from 'react'
import { useParams, useLocation, Link } from 'react-router-dom'
import { api, PredictionResult } from '../api/client'
import { EVENT_ICONS } from '../types'
import ConfidenceGauge from '../components/ConfidenceGauge'
import GateScoreCard from '../components/GateScoreCard'
import TransitTimeline from '../components/TransitTimeline'
import QualityBadges from '../components/QualityBadges'

const linkBtn: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: 6,
  padding: '8px 18px',
  borderRadius: 'var(--radius-md)',
  background: 'var(--accent-gradient)',
  color: '#fff',
  textDecoration: 'none',
  fontSize: 13,
  fontWeight: 600,
}

const linkBtnSecondary: React.CSSProperties = {
  ...linkBtn,
  background: 'var(--bg-tertiary)',
  color: 'var(--text-secondary)',
  border: '1px solid var(--border-primary)',
}

export default function PredictionPage() {
  const { id } = useParams<{ id: string }>()
  const location = useLocation()
  const stateData = (location.state as { prediction?: PredictionResult } | null)?.prediction
  const [prediction, setPrediction] = useState<PredictionResult | null>(stateData || null)
  const [loading, setLoading] = useState(!stateData)
  const [error, setError] = useState<string | null>(null)
  const [vectorExpanded, setVectorExpanded] = useState(false)

  useEffect(() => {
    if (stateData) return
    if (!id || id === 'result') return
    const numId = parseInt(id, 10)
    if (isNaN(numId)) { setError('Invalid prediction ID'); setLoading(false); return }
    setLoading(true)
    setError(null)
    api.getPrediction(numId).then(setPrediction).catch((err) => setError(err.message)).finally(() => setLoading(false))
  }, [id, stateData])

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 80, color: 'var(--text-tertiary)', fontSize: 15 }}>
        <svg width="24" height="24" viewBox="0 0 24 24" className="animate-spin" style={{ display: 'inline-block', marginBottom: 12 }}>
          <circle cx="12" cy="12" r="10" stroke="var(--accent-primary)" strokeWidth="2" fill="none" strokeDasharray="50 25" />
        </svg>
        <div>Loading prediction results...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{ background: 'var(--danger-bg)', color: 'var(--danger-text)', padding: 24, borderRadius: 'var(--radius-lg)', textAlign: 'center', maxWidth: 500, margin: '60px auto' }}>
        <p style={{ margin: '0 0 16px', fontWeight: 600 }}>Failed to load prediction: {error}</p>
        <Link to="/" style={linkBtn}>Back to Home</Link>
      </div>
    )
  }

  if (!prediction) {
    return <div style={{ textAlign: 'center', padding: 80, color: 'var(--text-tertiary)' }}>Prediction not found.</div>
  }

  const eventLabel = prediction.event_type.charAt(0).toUpperCase() + prediction.event_type.slice(1)
  const icon = EVENT_ICONS[prediction.event_type] || ''

  return (
    <div style={{ maxWidth: 960, margin: '0 auto' }} className="animate-fade-in">
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 800, color: 'var(--text-primary)', margin: 0 }}>
            {icon} {eventLabel} Prediction
          </h1>
          <div style={{ fontSize: 13, color: 'var(--text-tertiary)', marginTop: 6 }}>
            Query Date: {prediction.query_date} &middot; User ID: {prediction.user_id}
            {prediction.created_at && ` \u00B7 ${new Date(prediction.created_at).toLocaleString()}`}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Link to={`/chart/${prediction.user_id}`} style={linkBtn}>View Chart</Link>
          <Link to="/" style={linkBtnSecondary}>New Prediction</Link>
        </div>
      </div>

      {/* Quality badges */}
      <div style={{ marginBottom: 20 }}>
        <QualityBadges qualityFlags={prediction.quality_flags || {}} isRetrospective={prediction.is_retrospective} />
      </div>

      {/* Gauge + Timeline */}
      <div style={{ display: 'grid', gridTemplateColumns: '240px 1fr', gap: 20, marginBottom: 20, alignItems: 'start' }}>
        <ConfidenceGauge score={prediction.convergence_score} confidenceLevel={prediction.confidence_level} />
        <TransitTimeline timeline={prediction.gate3?.details?.timeline || []} peakMonth={prediction.peak_month} />
      </div>

      {/* Gate cards */}
      <div className="stagger-children" style={{ display: 'flex', gap: 16, marginBottom: 24, flexWrap: 'wrap' }}>
        <GateScoreCard gate={prediction.gate1} gateNumber={1} />
        <GateScoreCard gate={prediction.gate2} gateNumber={2} />
        <GateScoreCard gate={prediction.gate3} gateNumber={3} />
      </div>

      {/* Narration */}
      {prediction.narration_text && (
        <div
          style={{
            background: 'var(--card-bg)',
            border: '1px solid var(--card-border)',
            borderRadius: 'var(--radius-lg)',
            padding: 24,
            boxShadow: 'var(--shadow-md)',
            marginBottom: 24,
            lineHeight: 1.75,
            fontSize: 14,
            color: 'var(--text-secondary)',
            whiteSpace: 'pre-wrap',
          }}
        >
          <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10 }}>
            Analysis Narration
          </div>
          {prediction.narration_text}
        </div>
      )}

      {/* Feature vector */}
      {prediction.feature_vector && prediction.feature_vector.length > 0 && (
        <div
          style={{
            background: 'var(--card-bg)',
            border: '1px solid var(--card-border)',
            borderRadius: 'var(--radius-lg)',
            padding: 20,
            boxShadow: 'var(--shadow-sm)',
            marginBottom: 24,
          }}
        >
          <div
            onClick={() => setVectorExpanded(!vectorExpanded)}
            style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer', userSelect: 'none' }}
          >
            <div>
              <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: 1 }}>Feature Vector</span>
              <span style={{ fontSize: 12, color: 'var(--text-tertiary)', marginLeft: 8 }}>({prediction.feature_vector.length} dim)</span>
            </div>
            <span style={{ fontSize: 16, color: 'var(--text-tertiary)', fontWeight: 300 }}>
              {vectorExpanded ? '\u25B2' : '\u25BC'}
            </span>
          </div>
          {vectorExpanded && (
            <div style={{ marginTop: 12, maxHeight: 200, overflow: 'auto', background: 'var(--code-bg)', borderRadius: 'var(--radius-md)', padding: 12, fontSize: 11, fontFamily: 'monospace', color: 'var(--text-secondary)', wordBreak: 'break-all' }}>
              [{prediction.feature_vector.map((v, i) => (
                <span key={i}>{v.toFixed(4)}{i < prediction.feature_vector.length - 1 ? ', ' : ''}</span>
              ))}]
            </div>
          )}
        </div>
      )}
    </div>
  )
}
