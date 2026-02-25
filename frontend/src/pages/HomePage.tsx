import React from 'react'
import BirthDataForm from '../components/BirthDataForm'

const FEATURES = [
  {
    icon: '\u2727',
    title: 'Gate 1: Promise',
    desc: 'Birth chart promise analysis using house lord dignity, occupants, Navamsha, and SAV scores.',
  },
  {
    icon: '\u29BF',
    title: 'Gate 2: Dasha',
    desc: 'Vimshottari Dasha period alignment with event-specific planetary significators.',
  },
  {
    icon: '\u2726',
    title: 'Gate 3: Transit',
    desc: 'Jupiter-Saturn double transit window detection with Ashtakavarga strength scoring.',
  },
]

export default function HomePage() {
  return (
    <div className="animate-fade-in">
      {/* Hero */}
      <div style={{ textAlign: 'center', marginBottom: 40, paddingTop: 16 }}>
        <div
          style={{
            display: 'inline-block',
            padding: '4px 14px',
            borderRadius: 'var(--radius-full)',
            background: 'var(--accent-subtle)',
            color: 'var(--accent-text)',
            fontSize: 12,
            fontWeight: 700,
            letterSpacing: 0.5,
            marginBottom: 16,
          }}
        >
          VEDIC ASTROLOGY ENGINE v0.1
        </div>
        <h1
          style={{
            fontSize: 38,
            fontWeight: 900,
            color: 'var(--text-primary)',
            margin: '0 0 12px',
            letterSpacing: -1,
            lineHeight: 1.15,
          }}
        >
          Predict Life Events with
          <br />
          <span style={{ color: 'var(--accent-primary)' }}>Classical Jyotish</span>
        </h1>
        <p
          style={{
            fontSize: 16,
            color: 'var(--text-secondary)',
            maxWidth: 540,
            margin: '0 auto',
            lineHeight: 1.7,
          }}
        >
          Deterministic computation engine combining Dasha, double transit,
          and Ashtakavarga analysis. No AI guesswork — pure Vedic math.
        </p>
      </div>

      {/* Feature cards */}
      <div
        className="stagger-children"
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: 16,
          marginBottom: 40,
          maxWidth: 720,
          marginLeft: 'auto',
          marginRight: 'auto',
        }}
      >
        {FEATURES.map((f) => (
          <div
            key={f.title}
            style={{
              background: 'var(--card-bg)',
              border: '1px solid var(--card-border)',
              borderRadius: 'var(--radius-lg)',
              padding: '20px 18px',
              textAlign: 'center',
              boxShadow: 'var(--shadow-sm)',
              transition: 'transform 0.2s ease, box-shadow 0.2s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px)'
              e.currentTarget.style.boxShadow = 'var(--shadow-lg)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.boxShadow = 'var(--shadow-sm)'
            }}
          >
            <div style={{ fontSize: 28, marginBottom: 10, opacity: 0.85 }}>{f.icon}</div>
            <div
              style={{
                fontSize: 14,
                fontWeight: 700,
                color: 'var(--text-primary)',
                marginBottom: 6,
              }}
            >
              {f.title}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-tertiary)', lineHeight: 1.5 }}>
              {f.desc}
            </div>
          </div>
        ))}
      </div>

      {/* Form */}
      <div style={{ display: 'flex', justifyContent: 'center' }}>
        <BirthDataForm />
      </div>
    </div>
  )
}
