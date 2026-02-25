export type EventType = 'marriage' | 'career' | 'child' | 'property' | 'health'
export type ConfidenceLevel = 'HIGH' | 'MEDIUM' | 'LOW' | 'NEGATIVE' | 'INSUFFICIENT'

export const EVENT_TYPES: { value: EventType; label: string; icon: string }[] = [
  { value: 'marriage', label: 'Marriage', icon: '\uD83D\uDC8D' },
  { value: 'career', label: 'Career', icon: '\uD83D\uDCBC' },
  { value: 'child', label: 'Child', icon: '\uD83D\uDC76' },
  { value: 'property', label: 'Property', icon: '\uD83C\uDFE0' },
  { value: 'health', label: 'Health', icon: '\uD83C\uDFE5' },
]

export const CONFIDENCE_COLORS: Record<ConfidenceLevel, string> = {
  HIGH: '#10b981',
  MEDIUM: '#f59e0b',
  LOW: '#f97316',
  NEGATIVE: '#ef4444',
  INSUFFICIENT: '#94a3b8',
}

export const EVENT_ICONS: Record<string, string> = {
  marriage: '\uD83D\uDC8D',
  career: '\uD83D\uDCBC',
  child: '\uD83D\uDC76',
  property: '\uD83C\uDFE0',
  health: '\uD83C\uDFE5',
}
