import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const card: React.CSSProperties = {
  background: 'var(--card-bg)',
  border: '1px solid var(--card-border)',
  borderRadius: 'var(--radius-xl)',
  padding: '40px 36px 32px',
  boxShadow: 'var(--shadow-lg)',
  maxWidth: 420,
  width: '100%',
}

const field: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: 5,
  marginBottom: 18,
}

const lbl: React.CSSProperties = {
  fontSize: 12,
  fontWeight: 600,
  color: 'var(--text-secondary)',
  letterSpacing: 0.3,
}

const inp: React.CSSProperties = {
  padding: '11px 14px',
  borderRadius: 'var(--radius-md)',
  border: '1px solid var(--input-border)',
  fontSize: 14,
  outline: 'none',
  background: 'var(--input-bg)',
  color: 'var(--input-text)',
  transition: 'border-color 0.2s ease',
}

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
  marginBottom: 16,
  border: '1px solid rgba(239,68,68,0.2)',
}

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(email, password)
      navigate('/')
    } catch (err: any) {
      setError(err.message || 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="animate-fade-in" style={{ display: 'flex', justifyContent: 'center', paddingTop: 40 }}>
      <form style={card} onSubmit={handleSubmit}>
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div
            style={{
              width: 48,
              height: 48,
              borderRadius: 'var(--radius-lg)',
              background: 'var(--accent-gradient)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontSize: 22,
              fontWeight: 900,
              marginBottom: 14,
            }}
          >
            J
          </div>
          <h2 style={{ margin: '0 0 6px', fontSize: 22, fontWeight: 800, color: 'var(--text-primary)' }}>
            Welcome Back
          </h2>
          <p style={{ fontSize: 13, color: 'var(--text-tertiary)', margin: 0 }}>
            Sign in to your Jyotish AI account
          </p>
        </div>

        {error && <div style={errBox}>{error}</div>}

        <div style={field}>
          <label style={lbl}>Email</label>
          <input
            style={inp}
            type="email"
            placeholder="you@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />
        </div>

        <div style={field}>
          <label style={lbl}>Password</label>
          <input
            style={inp}
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <button type="submit" style={{ ...btn, marginTop: 6 }} disabled={loading}>
          {loading ? 'Signing in...' : 'Sign In'}
        </button>

        <p style={{ textAlign: 'center', fontSize: 13, color: 'var(--text-tertiary)', marginTop: 20, marginBottom: 0 }}>
          Don't have an account?{' '}
          <Link to="/register" style={{ color: 'var(--accent-primary)', fontWeight: 600, textDecoration: 'none' }}>
            Register
          </Link>
        </p>
      </form>
    </div>
  )
}
