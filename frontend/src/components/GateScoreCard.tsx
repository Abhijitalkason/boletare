import React from 'react'
import { GateScore } from '../api/client'

interface GateScoreCardProps {
  gate: GateScore
  gateNumber: number
}

const GATE_LABELS: Record<number, { title: string }> = {
  1: { title: 'Promise' },
  2: { title: 'Dasha' },
  3: { title: 'Transit' },
}

function barColor(s: number) {
  if (s >= 0.7) return 'var(--success)'
  if (s >= 0.4) return 'var(--warning)'
  return 'var(--danger)'
}

function fmtKey(k: string) {
  return k.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function fmtVal(v: any): string {
  if (v === null || v === undefined) return '-'
  if (typeof v === 'boolean') return v ? 'Yes' : 'No'
  if (typeof v === 'number') return v % 1 === 0 ? v.toString() : v.toFixed(3)
  if (typeof v === 'object') return JSON.stringify(v)
  return String(v)
}

export default function GateScoreCard({ gate, gateNumber }: GateScoreCardProps) {
  const color = barColor(gate.score)
  const info = GATE_LABELS[gateNumber] || { title: gate.gate_name }
  const details = Object.entries(gate.details || {}).filter(([, v]) => typeof v !== 'object' || v === null)

  return (
    <div
      style={{
        background: 'var(--card-bg)',
        border: '1px solid var(--card-border)',
        borderRadius: 'var(--radius-lg)',
        padding: 20,
        boxShadow: 'var(--shadow-md)',
        flex: '1 1 0',
        minWidth: 200,
        transition: 'transform 0.2s ease, box-shadow 0.2s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)'
        e.currentTarget.style.boxShadow = 'var(--shadow-lg)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = 'var(--shadow-md)'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
        <div>
          <div style={{ fontSize: 11, color: 'var(--text-tertiary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1 }}>
            Gate {gateNumber}
          </div>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)', marginTop: 2 }}>
            {info.title}
          </div>
        </div>
        <div style={{ width: 30, height: 30, borderRadius: 'var(--radius-sm)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 700, color: '#fff', background: color }}>
          G{gateNumber}
        </div>
      </div>

      <p style={{ fontSize: 28, fontWeight: 800, color, margin: '0 0 8px' }}>
        {gate.score.toFixed(2)}
      </p>

      <div style={{ width: '100%', height: 6, background: 'var(--gauge-track)', borderRadius: 3, overflow: 'hidden', marginBottom: 12 }}>
        <div style={{ width: `${Math.min(gate.score * 100, 100)}%`, height: '100%', background: color, borderRadius: 3, transition: 'width 0.6s ease-out' }} />
      </div>

      <span
        style={{
          display: 'inline-block',
          padding: '3px 12px',
          borderRadius: 'var(--radius-full)',
          fontSize: 11,
          fontWeight: 700,
          background: gate.is_sufficient ? 'var(--success-bg)' : 'var(--danger-bg)',
          color: gate.is_sufficient ? 'var(--success-text)' : 'var(--danger-text)',
          marginBottom: 12,
        }}
      >
        {gate.is_sufficient ? 'Sufficient' : 'Insufficient'}
      </span>

      {details.length > 0 && (
        <div style={{ marginTop: 8 }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--text-tertiary)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>
            Details
          </div>
          {details.map(([key, value]) => (
            <div key={key} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-secondary)', padding: '4px 0', borderBottom: '1px solid var(--border-secondary)' }}>
              <span>{fmtKey(key)}</span>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{fmtVal(value)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
