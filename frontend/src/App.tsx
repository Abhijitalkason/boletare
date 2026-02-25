import React from 'react'
import { BrowserRouter, Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom'
import { ThemeProvider, useTheme } from './context/ThemeContext'
import { AuthProvider, useAuth } from './context/AuthContext'
import CosmicBackground from './components/CosmicBackground'
import HomePage from './pages/HomePage'
import PredictionPage from './pages/PredictionPage'
import ChartPage from './pages/ChartPage'
import HistoryPage from './pages/HistoryPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import KundliPage from './pages/KundliPage'

function ThemeToggle() {
  const { isDark, toggleTheme } = useTheme()

  return (
    <button
      onClick={toggleTheme}
      aria-label="Toggle theme"
      style={{
        background: 'var(--bg-tertiary)',
        border: '1px solid var(--border-primary)',
        borderRadius: 'var(--radius-full)',
        width: 40,
        height: 40,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        color: 'var(--text-secondary)',
        fontSize: 18,
        transition: 'all 0.3s ease',
        flexShrink: 0,
      }}
    >
      {isDark ? '\u2600\uFE0F' : '\uD83C\uDF19'}
    </button>
  )
}

function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  const location = useLocation()
  const isActive = location.pathname === to

  return (
    <Link
      to={to}
      style={{
        textDecoration: 'none',
        color: isActive ? 'var(--accent-primary)' : 'var(--text-secondary)',
        fontWeight: 600,
        fontSize: 14,
        padding: '6px 14px',
        borderRadius: 'var(--radius-md)',
        background: isActive ? 'var(--accent-subtle)' : 'transparent',
        transition: 'all 0.2s ease',
      }}
    >
      {children}
    </Link>
  )
}

function AuthButtons() {
  const { isAuthenticated, user, logout } = useAuth()
  const navigate = useNavigate()

  if (isAuthenticated && user) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span
          style={{
            fontSize: 12,
            color: 'var(--text-tertiary)',
            maxWidth: 120,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {user.name}
        </span>
        <button
          onClick={() => { logout(); navigate('/login') }}
          style={{
            background: 'var(--bg-tertiary)',
            border: '1px solid var(--border-primary)',
            borderRadius: 'var(--radius-md)',
            padding: '5px 12px',
            fontSize: 12,
            fontWeight: 600,
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            transition: 'all 0.2s ease',
          }}
        >
          Logout
        </button>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <Link
        to="/login"
        style={{
          textDecoration: 'none',
          fontSize: 13,
          fontWeight: 600,
          color: 'var(--text-secondary)',
          padding: '6px 14px',
          borderRadius: 'var(--radius-md)',
          transition: 'all 0.2s',
        }}
      >
        Login
      </Link>
      <Link
        to="/register"
        style={{
          textDecoration: 'none',
          fontSize: 13,
          fontWeight: 700,
          color: '#fff',
          padding: '6px 16px',
          borderRadius: 'var(--radius-md)',
          background: 'var(--accent-gradient)',
          transition: 'all 0.2s',
        }}
      >
        Register
      </Link>
    </div>
  )
}

function AppLayout() {
  return (
    <>
      <CosmicBackground />
      {/* Navigation */}
      <nav
        style={{
          position: 'sticky',
          top: 0,
          zIndex: 100,
          background: 'var(--nav-bg)',
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid var(--nav-border)',
          padding: '0 24px',
        }}
      >
        <div
          style={{
            maxWidth: 1200,
            margin: '0 auto',
            display: 'flex',
            alignItems: 'center',
            height: 60,
            gap: 8,
          }}
        >
          <Link
            to="/"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              textDecoration: 'none',
              marginRight: 'auto',
            }}
          >
            <div
              style={{
                width: 34,
                height: 34,
                borderRadius: 'var(--radius-md)',
                background: 'var(--accent-gradient)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#fff',
                fontSize: 16,
                fontWeight: 900,
              }}
            >
              J
            </div>
            <span
              style={{
                fontSize: 18,
                fontWeight: 800,
                color: 'var(--text-primary)',
                letterSpacing: -0.5,
              }}
            >
              Jyotish AI
            </span>
          </Link>

          <NavLink to="/">Home</NavLink>
          <NavLink to="/kundli">Free Kundli</NavLink>
          <NavLink to="/history">History</NavLink>

          <div style={{ marginLeft: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
            <AuthButtons />
            <ThemeToggle />
          </div>
        </div>
      </nav>

      <main
        style={{
          maxWidth: 1200,
          margin: '0 auto',
          padding: '32px 24px 64px',
          minHeight: 'calc(100vh - 60px)',
        }}
      >
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/prediction/:id" element={<PredictionPage />} />
          <Route path="/chart/:userId" element={<ChartPage />} />
          <Route path="/kundli" element={<KundliPage />} />
          <Route path="/history" element={<HistoryPage />} />
        </Routes>
      </main>

      <footer
        style={{
          borderTop: '1px solid var(--border-primary)',
          padding: '20px 24px',
          textAlign: 'center',
          fontSize: 12,
          color: 'var(--text-tertiary)',
        }}
      >
        Jyotish AI v0.1 — Deterministic Vedic Astrology Prediction Engine
      </footer>
    </>
  )
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <AppLayout />
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  )
}
