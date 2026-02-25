import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const card: React.CSSProperties = {
  background: 'var(--card-bg)',
  border: '1px solid var(--card-border)',
  borderRadius: 'var(--radius-xl)',
  padding: '36px 36px 28px',
  boxShadow: 'var(--shadow-lg)',
  maxWidth: 540,
  width: '100%',
}

const row: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '1fr 1fr',
  gap: 14,
  marginBottom: 14,
}

const field: React.CSSProperties = { display: 'flex', flexDirection: 'column', gap: 5 }
const fullField: React.CSSProperties = { ...field, marginBottom: 14 }

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
  transition: 'border-color 0.2s ease',
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
  transition: 'opacity 0.2s',
  boxShadow: 'var(--shadow-glow)',
}

const errBox: React.CSSProperties = {
  background: 'var(--danger-bg)',
  color: 'var(--danger-text)',
  padding: '10px 14px',
  borderRadius: 'var(--radius-md)',
  fontSize: 13,
  marginBottom: 14,
  border: '1px solid rgba(239,68,68,0.2)',
}

const sectionTitle: React.CSSProperties = {
  fontSize: 13,
  fontWeight: 700,
  color: 'var(--text-secondary)',
  margin: '4px 0 14px',
  paddingTop: 14,
  borderTop: '1px solid var(--border-primary)',
  letterSpacing: 0.5,
  textTransform: 'uppercase' as const,
}

export default function RegisterPage() {
  const navigate = useNavigate()
  const { register } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  // Auth fields
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPw, setConfirmPw] = useState('')

  // Birth data
  const [name, setName] = useState('')
  const [birthDate, setBirthDate] = useState('')
  const [birthTime, setBirthTime] = useState('')
  const [birthPlace, setBirthPlace] = useState('')
  const [latitude, setLatitude] = useState('')
  const [longitude, setLongitude] = useState('')
  const [timezoneOffset, setTimezoneOffset] = useState('5.5')
  const [birthTimeTier, setBirthTimeTier] = useState('2')

  // WhatsApp
  const [phone, setPhone] = useState('')
  const [deliveryPref, setDeliveryPref] = useState('api')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (password !== confirmPw) {
      setError('Passwords do not match')
      return
    }
    if (password.length < 6) {
      setError('Password must be at least 6 characters')
      return
    }
    if (!name.trim()) {
      setError('Name is required')
      return
    }
    if (!birthDate) {
      setError('Birth date is required')
      return
    }

    setLoading(true)
    try {
      const data: Record<string, any> = {
        email: email.trim().toLowerCase(),
        password,
        name: name.trim(),
        birth_date: birthDate,
        birth_time_tier: parseInt(birthTimeTier, 10),
        delivery_preference: deliveryPref,
      }
      if (birthTime) data.birth_time = birthTime
      if (birthPlace.trim()) data.birth_place = birthPlace.trim()
      if (latitude) data.latitude = parseFloat(latitude)
      if (longitude) data.longitude = parseFloat(longitude)
      if (timezoneOffset) data.timezone_offset = parseFloat(timezoneOffset)
      if (phone.trim()) data.phone_number = phone.trim()

      await register(data)
      navigate('/')
    } catch (err: any) {
      setError(err.message || 'Registration failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="animate-fade-in" style={{ display: 'flex', justifyContent: 'center', paddingTop: 24 }}>
      <form style={card} onSubmit={handleSubmit}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <h2 style={{ margin: '0 0 6px', fontSize: 22, fontWeight: 800, color: 'var(--text-primary)' }}>
            Create Account
          </h2>
          <p style={{ fontSize: 13, color: 'var(--text-tertiary)', margin: 0 }}>
            Register with your birth data for Vedic predictions
          </p>
        </div>

        {error && <div style={errBox}>{error}</div>}

        {/* Account Section */}
        <div style={sectionTitle}>Account</div>

        <div style={fullField}>
          <label style={lbl}>Email *</label>
          <input style={inp} type="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus />
        </div>

        <div style={row}>
          <div style={field}>
            <label style={lbl}>Password *</label>
            <input style={inp} type="password" placeholder="Min 6 characters" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>
          <div style={field}>
            <label style={lbl}>Confirm Password *</label>
            <input style={inp} type="password" placeholder="Re-enter password" value={confirmPw} onChange={(e) => setConfirmPw(e.target.value)} required />
          </div>
        </div>

        {/* Birth Data Section */}
        <div style={sectionTitle}>Birth Data</div>

        <div style={fullField}>
          <label style={lbl}>Full Name *</label>
          <input style={inp} type="text" placeholder="Enter your full name" value={name} onChange={(e) => setName(e.target.value)} required />
        </div>

        <div style={row}>
          <div style={field}>
            <label style={lbl}>Birth Date *</label>
            <input style={inp} type="date" value={birthDate} onChange={(e) => setBirthDate(e.target.value)} required />
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
            <input style={inp} type="number" step="any" placeholder="28.6139" value={latitude} onChange={(e) => setLatitude(e.target.value)} />
          </div>
          <div style={field}>
            <label style={lbl}>Longitude</label>
            <input style={inp} type="number" step="any" placeholder="77.2090" value={longitude} onChange={(e) => setLongitude(e.target.value)} />
          </div>
        </div>

        <div style={row}>
          <div style={field}>
            <label style={lbl}>Timezone (UTC offset)</label>
            <input style={inp} type="number" step="0.5" value={timezoneOffset} onChange={(e) => setTimezoneOffset(e.target.value)} />
          </div>
          <div style={field}>
            <label style={lbl}>Birth Time Accuracy</label>
            <select style={sel} value={birthTimeTier} onChange={(e) => setBirthTimeTier(e.target.value)}>
              <option value="1">Exact (hospital record)</option>
              <option value="2">Approximate (\u00B115 min)</option>
              <option value="3">Estimate / Unknown</option>
            </select>
          </div>
        </div>

        {/* Delivery Section */}
        <div style={sectionTitle}>Delivery Preference</div>

        <div style={row}>
          <div style={field}>
            <label style={lbl}>Phone Number (WhatsApp)</label>
            <input style={inp} type="tel" placeholder="+919876543210" value={phone} onChange={(e) => setPhone(e.target.value)} />
          </div>
          <div style={field}>
            <label style={lbl}>Delivery Channel</label>
            <select style={sel} value={deliveryPref} onChange={(e) => setDeliveryPref(e.target.value)}>
              <option value="api">Web App (API)</option>
              <option value="whatsapp">WhatsApp</option>
            </select>
          </div>
        </div>

        <button type="submit" style={{ ...btn, marginTop: 10 }} disabled={loading}>
          {loading ? 'Creating account...' : 'Create Account'}
        </button>

        <p style={{ textAlign: 'center', fontSize: 13, color: 'var(--text-tertiary)', marginTop: 18, marginBottom: 0 }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: 'var(--accent-primary)', fontWeight: 600, textDecoration: 'none' }}>
            Sign In
          </Link>
        </p>
      </form>
    </div>
  )
}
