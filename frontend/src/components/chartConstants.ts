// ═══════════════════════════════════════════════════════════════
// Jyotish AI — Chart Constants
// Shared lookup tables for Vedic astrology chart components
// ═══════════════════════════════════════════════════════════════

/** Sign int (1-12) → full English name */
export const SIGN_NAMES: Record<number, string> = {
  1: 'Aries', 2: 'Taurus', 3: 'Gemini', 4: 'Cancer',
  5: 'Leo', 6: 'Virgo', 7: 'Libra', 8: 'Scorpio',
  9: 'Sagittarius', 10: 'Capricorn', 11: 'Aquarius', 12: 'Pisces',
}

/** Sign int (1-12) → Hindi name */
export const SIGN_HINDI: Record<number, string> = {
  1: 'Mesh', 2: 'Vrishabh', 3: 'Mithun', 4: 'Kark',
  5: 'Simha', 6: 'Kanya', 7: 'Tula', 8: 'Vrishchik',
  9: 'Dhanu', 10: 'Makar', 11: 'Kumbh', 12: 'Meen',
}

/** Sign int (1-12) → 2-3 letter abbreviation */
export const SIGN_ABBR: Record<number, string> = {
  1: 'Ar', 2: 'Ta', 3: 'Ge', 4: 'Cn',
  5: 'Le', 6: 'Vi', 7: 'Li', 8: 'Sc',
  9: 'Sg', 10: 'Cp', 11: 'Aq', 12: 'Pi',
}

/** Sign int (1-12) → Unicode zodiac symbol */
export const SIGN_SYMBOLS: Record<number, string> = {
  1: '\u2648', 2: '\u2649', 3: '\u264A', 4: '\u264B',
  5: '\u264C', 6: '\u264D', 7: '\u264E', 8: '\u264F',
  9: '\u2650', 10: '\u2651', 11: '\u2652', 12: '\u2653',
}

/** Planet name → 2-letter abbreviation */
export const PLANET_ABBR: Record<string, string> = {
  Sun: 'Su', Moon: 'Mo', Mars: 'Ma', Mercury: 'Me',
  Jupiter: 'Ju', Venus: 'Ve', Saturn: 'Sa', Rahu: 'Ra', Ketu: 'Ke',
}

/** Planet name → display color */
export const PLANET_COLORS: Record<string, string> = {
  Sun: '#e6a817',
  Moon: '#c0c0c0',
  Mars: '#dc2626',
  Mercury: '#22c55e',
  Jupiter: '#f59e0b',
  Venus: '#ec4899',
  Saturn: '#6366f1',
  Rahu: '#64748b',
  Ketu: '#a78bfa',
}

/** Natural malefic planets */
export const MALEFIC_PLANETS = new Set(['Sun', 'Mars', 'Saturn', 'Rahu', 'Ketu'])

/** Natural benefic planets */
export const BENEFIC_PLANETS = new Set(['Moon', 'Mercury', 'Jupiter', 'Venus'])

/** Dignity → color (matches existing DIGNITY_COLORS in ChartPage) */
export const DIGNITY_COLORS: Record<string, string> = {
  exalted: 'var(--success)',
  own: 'var(--info)',
  moolatrikona: 'var(--accent-primary)',
  friend: '#8b5cf6',
  neutral: 'var(--text-tertiary)',
  enemy: 'var(--warning)',
  debilitated: 'var(--danger)',
}

/** Sign int (1-12) → ruling planet name */
export const SIGN_LORDS: Record<number, string> = {
  1: 'Mars', 2: 'Venus', 3: 'Mercury', 4: 'Moon',
  5: 'Sun', 6: 'Mercury', 7: 'Venus', 8: 'Mars',
  9: 'Jupiter', 10: 'Saturn', 11: 'Saturn', 12: 'Jupiter',
}

/** Sign name (API string) → sign number */
export const SIGN_NAME_TO_NUM: Record<string, number> = {
  ARIES: 1, TAURUS: 2, GEMINI: 3, CANCER: 4,
  LEO: 5, VIRGO: 6, LIBRA: 7, SCORPIO: 8,
  SAGITTARIUS: 9, CAPRICORN: 10, AQUARIUS: 11, PISCES: 12,
}

/** Dasha planet → color for timeline */
export const DASHA_PLANET_COLORS: Record<string, string> = {
  Sun: '#e6a817',
  Moon: '#94a3b8',
  Mars: '#dc2626',
  Mercury: '#22c55e',
  Jupiter: '#f59e0b',
  Venus: '#ec4899',
  Saturn: '#6366f1',
  Rahu: '#64748b',
  Ketu: '#a78bfa',
}

/** Format degrees as D°M' */
export function formatDegrees(deg: number): string {
  const d = Math.floor(deg)
  const m = Math.round((deg - d) * 60)
  return `${d}°${m.toString().padStart(2, '0')}'`
}

/** Get sign number from API sign value (handles both int and string) */
export function normalizeSign(sign: number | string): number {
  if (typeof sign === 'number') return sign
  return SIGN_NAME_TO_NUM[sign.toUpperCase()] || 1
}
