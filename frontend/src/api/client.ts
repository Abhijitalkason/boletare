const BASE_URL = '/api/v1'

function getAuthHeaders(): Record<string, string> {
  const token = localStorage.getItem('jyotish_token')
  if (token) {
    return { Authorization: `Bearer ${token}` }
  }
  return {}
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
      ...options?.headers,
    },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export interface User {
  id: number
  name: string
  email?: string
  birth_date: string
  birth_time?: string
  birth_place?: string
  latitude?: number
  longitude?: number
  timezone_offset?: number
  birth_time_tier?: number
  phone_number?: string
  delivery_preference?: string
  whatsapp_opted_in?: boolean
}

export interface TokenData {
  access_token: string
  token_type?: string
  user_id: number
  email: string
  name: string
}

export interface GateScore {
  gate_name: string
  score: number
  is_sufficient: boolean
  details: Record<string, any>
}

export interface PredictionResult {
  id?: number
  user_id: number
  event_type: string
  query_date: string
  gate1: GateScore
  gate2: GateScore
  gate3: GateScore
  convergence_score: number
  confidence_level: string
  quality_flags: Record<string, any>
  peak_month?: string
  feature_vector: number[]
  narration_text?: string
  is_retrospective: boolean
  created_at?: string
}

export interface PredictionListItem {
  id: number
  event_type: string
  query_date: string
  convergence_score: number
  confidence_level: string
  is_retrospective: boolean
  created_at?: string
}

export interface PlanetData {
  planet: string
  longitude_arcsec: number
  sign: number
  sign_degrees: number
  nakshatra: string
  nakshatra_pada: number
  house: number
  dignity: string
  dignity_score: number
  is_retrograde: boolean
}

export interface HouseData {
  house_number: number
  cusp_arcsec: number
  sign: number
  sign_degrees: number
  span_degrees: number
}

export interface DashaData {
  level: string
  planet: string
  start_date: string
  end_date: string
  duration_days: number
  sub_periods: DashaData[]
}

export interface AshtakavargaData {
  bav: Record<string, Record<string, number>>
  sav: Record<string, number>
  sav_trikona_reduced: Record<string, number>
}

export interface ChartData {
  ascendant_sign: string
  ascendant_arcsec: number
  lagna_mode: string
  planets: PlanetData[]
  houses: HouseData[]
  dasha_tree: DashaData[]
  ashtakavarga: AshtakavargaData
  navamsha_planets: PlanetData[]
  quality_flags: Record<string, any>
  computed_at: string
}

export interface YogaData {
  name: string
  yoga_type: string
  is_present: boolean
  strength: number
  involved_planets: string[]
  description: string
}

export interface DoshaData {
  name: string
  is_present: boolean
  severity: string
  involved_planets: string[]
  affected_houses: number[]
  description: string
  cancellation_factors: string[]
}

export interface KundliData {
  name: string
  birth_date: string
  birth_time?: string
  birth_place?: string
  ascendant_sign: string
  ascendant_arcsec: number
  lagna_mode: string
  planets: PlanetData[]
  houses: HouseData[]
  dasha_tree: DashaData[]
  ashtakavarga: AshtakavargaData
  navamsha_planets: PlanetData[]
  quality_flags: Record<string, any>
  computed_at: string
  yogas: YogaData[]
  doshas: DoshaData[]
}

export const api = {
  // Auth
  register: (data: Record<string, any>) =>
    request<TokenData>('/auth/register', { method: 'POST', body: JSON.stringify(data) }),

  login: (data: { email: string; password: string }) =>
    request<TokenData>('/auth/login', { method: 'POST', body: JSON.stringify(data) }),

  getMe: () => request<User>('/auth/me'),

  // Users
  createUser: (data: Record<string, any>) =>
    request<User>('/users', { method: 'POST', body: JSON.stringify(data) }),

  getUser: (id: number) => request<User>(`/users/${id}`),

  // Predictions
  runPrediction: (data: {
    user_id: number
    event_type: string
    query_date?: string
    is_retrospective?: boolean
    ayanamsha?: string
  }) => request<PredictionResult>('/predictions', { method: 'POST', body: JSON.stringify(data) }),

  getPrediction: (id: number) => request<PredictionResult>(`/predictions/${id}`),

  getUserPredictions: (userId: number) =>
    request<PredictionListItem[]>(`/predictions/user/${userId}`),

  // Charts
  getChart: (userId: number, ayanamsha?: string) =>
    request<ChartData>(`/charts/user/${userId}?ayanamsha=${ayanamsha || 'lahiri'}`),

  // Kundli (Free Chart Analysis)
  computeKundli: (data: Record<string, any>) =>
    request<KundliData>('/kundli/compute', { method: 'POST', body: JSON.stringify(data) }),

  // Health
  getHealth: () => request<{ status: string; version: string }>('/health'),
}
