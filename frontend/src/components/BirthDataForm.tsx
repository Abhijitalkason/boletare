import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { EVENT_TYPES } from '../types'

const card: React.CSSProperties = {
  background: 'var(--card-bg)',
  border: '1px solid var(--card-border)',
  borderRadius: 'var(--radius-xl)',
  padding: '32px 32px 28px',
  boxShadow: 'var(--shadow-lg)',
  maxWidth: 620,
  width: '100%',
}

const row: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '1fr 1fr',
  gap: 16,
  marginBottom: 16,
}

const field: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: 5,
}

const fullField: React.CSSProperties = { ...field, marginBottom: 16 }

const lbl: React.CSSProperties = {
  fontSize: 12,
  fontWeight: 600,
  color: 'var(--text-secondary)',
  letterSpacing: 0.3,
}

const inp: React.CSSProperties = {
  padding: '10px 14px',
  borderRadius: 'var(--radius-md)',
  border: '1px solid var(--input-border)',
  fontSize: 14,
  outline: 'none',
  background: 'var(--input-bg)',
  color: 'var(--input-text)',
  transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
}

const sel: React.CSSProperties = { ...inp, appearance: 'auto' as any }

const btn: React.CSSProperties = {
  padding: '12px 32px',
  borderRadius: 'var(--radius-md)',
  border: 'none',
  background: 'var(--accent-gradient)',
  color: '#fff',
  fontSize: 15,
  fontWeight: 700,
  cursor: 'pointer',
  width: '100%',
  transition: 'opacity 0.2s, transform 0.1s',
  boxShadow: 'var(--shadow-glow)',
}

const errBox: React.CSSProperties = {
  background: 'var(--danger-bg)',
  color: 'var(--danger-text)',
  padding: '10px 14px',
  borderRadius: 'var(--radius-md)',
  fontSize: 13,
  marginBottom: 16,
  border: '1px solid rgba(239,68,68,0.2)',
}

export default function BirthDataForm() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [name, setName] = useState('')
  const [birthDate, setBirthDate] = useState('')
  const [birthTime, setBirthTime] = useState('')
  const [birthPlace, setBirthPlace] = useState('')
  const [latitude, setLatitude] = useState('')
  const [longitude, setLongitude] = useState('')
  const [timezoneOffset, setTimezoneOffset] = useState('5.5')
  const [birthTimeTier, setBirthTimeTier] = useState('1')
  const [eventType, setEventType] = useState('marriage')
  const [queryDate, setQueryDate] = useState('')
  const [isRetrospective, setIsRetrospective] = useState(false)
  const [existingUserId, setExistingUserId] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      let userId: number

      if (existingUserId.trim()) {
        userId = parseInt(existingUserId, 10)
        if (isNaN(userId)) throw new Error('Invalid user ID')
      } else {
        if (!name.trim()) throw new Error('Name is required')
        if (!birthDate) throw new Error('Birth date is required')

        const userData: Record<string, any> = {
          name: name.trim(),
          birth_date: birthDate,
        }
        if (birthTime) userData.birth_time = birthTime
        if (birthPlace.trim()) userData.birth_place = birthPlace.trim()
        if (latitude) userData.latitude = parseFloat(latitude)
        if (longitude) userData.longitude = parseFloat(longitude)
        if (timezoneOffset) userData.timezone_offset = parseFloat(timezoneOffset)
        if (birthTimeTier) userData.birth_time_tier = parseInt(birthTimeTier, 10)

        const user = await api.createUser(userData)
        userId = user.id
      }

      const predictionData: {
        user_id: number
        event_type: string
        query_date?: string
        is_retrospective?: boolean
      } = { user_id: userId, event_type: eventType }
      if (queryDate) predictionData.query_date = queryDate
      if (isRetrospective) predictionData.is_retrospective = true

      const result = await api.runPrediction(predictionData)
      if (result.id) {
        navigate(`/prediction/${result.id}`)
      } else {
        navigate('/prediction/result', { state: { prediction: result } })
      }
    } catch (err: any) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form style={card} onSubmit={handleSubmit} className="animate-slide-up">
      <h2 style={{ margin: '0 0 4px', fontSize: 20, fontWeight: 800, color: 'var(--text-primary)' }}>
        Birth Data &amp; Prediction
      </h2>
      <p style={{ fontSize: 13, color: 'var(--text-tertiary)', margin: '0 0 24px' }}>
        Enter birth details to compute a Vedic prediction.
      </p>

      {error && <div style={errBox}>{error}</div>}

      <div style={fullField}>
        <label style={lbl}>Existing User ID (leave blank to create new)</label>
        <input style={inp} type="text" placeholder="e.g. 1" value={existingUserId} onChange={(e) => setExistingUserId(e.target.value)} />
      </div>

      {!existingUserId.trim() && (
        <>
          <div style={fullField}>
            <label style={lbl}>Full Name *</label>
            <input style={inp} type="text" placeholder="Enter full name" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div style={row}>
            <div style={field}>
              <label style={lbl}>Birth Date *</label>
              <input style={inp} type="date" value={birthDate} onChange={(e) => setBirthDate(e.target.value)} />
            </div>
            <div style={field}>
              <label style={lbl}>Birth Time</label>
              <input style={inp} type="time" step="1" value={birthTime} onChange={(e) => setBirthTime(e.target.value)} />
            </div>
          </div>
          <div style={fullField}>
            <label style={lbl}>Birth Place</label>
            <input style={inp} type="text" placeholder="City, Country" value={birthPlace} onChange={(e) => setBirthPlace(e.target.value)} />
          </div>
          <div style={row}>
            <div style={field}>
              <label style={lbl}>Latitude</label>
              <input style={inp} type="number" step="any" placeholder="e.g. 28.6139" value={latitude} onChange={(e) => setLatitude(e.target.value)} />
            </div>
            <div style={field}>
              <label style={lbl}>Longitude</label>
              <input style={inp} type="number" step="any" placeholder="e.g. 77.2090" value={longitude} onChange={(e) => setLongitude(e.target.value)} />
            </div>
          </div>
          <div style={row}>
            <div style={field}>
              <label style={lbl}>Timezone (UTC offset)</label>
              <input style={inp} type="number" step="0.5" value={timezoneOffset} onChange={(e) => setTimezoneOffset(e.target.value)} />
            </div>
            <div style={field}>
              <label style={lbl}>Birth Time Tier</label>
              <select style={sel} value={birthTimeTier} onChange={(e) => setBirthTimeTier(e.target.value)}>
                <option value="1">Tier 1 — Exact (record)</option>
                <option value="2">Tier 2 — Approx (\u00B115 min)</option>
                <option value="3">Tier 3 — Estimate / Unknown</option>
              </select>
            </div>
          </div>
        </>
      )}

      <div style={{ borderTop: '1px solid var(--border-primary)', margin: '20px 0', paddingTop: 20 }}>
        <h3 style={{ margin: '0 0 16px', fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
          Prediction Parameters
        </h3>
        <div style={row}>
          <div style={field}>
            <label style={lbl}>Event Type *</label>
            <select style={sel} value={eventType} onChange={(e) => setEventType(e.target.value)}>
              {EVENT_TYPES.map((et) => (
                <option key={et.value} value={et.value}>{et.icon} {et.label}</option>
              ))}
            </select>
          </div>
          <div style={field}>
            <label style={lbl}>Query Date (optional)</label>
            <input style={inp} type="date" value={queryDate} onChange={(e) => setQueryDate(e.target.value)} />
          </div>
        </div>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 20, cursor: 'pointer', fontSize: 13, color: 'var(--text-secondary)' }}>
          <input type="checkbox" checked={isRetrospective} onChange={(e) => setIsRetrospective(e.target.checked)} style={{ width: 16, height: 16, accentColor: 'var(--accent-primary)' }} />
          Retrospective analysis (event already happened)
        </label>
      </div>

      {loading ? (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, padding: '14px 0', color: 'var(--accent-primary)', fontWeight: 600, fontSize: 14 }}>
          <svg width="20" height="20" viewBox="0 0 20 20" className="animate-spin">
            <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="2" fill="none" strokeDasharray="40 20" />
          </svg>
          Computing prediction...
        </div>
      ) : (
        <button type="submit" style={btn} disabled={loading}>
          Run Prediction
        </button>
      )}
    </form>
  )
}
