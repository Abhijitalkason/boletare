import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { api, type TokenData } from '../api/client'

interface AuthState {
  isAuthenticated: boolean
  user: TokenData | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  register: (data: Record<string, any>) => Promise<void>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthState>({
  isAuthenticated: false,
  user: null,
  token: null,
  login: async () => {},
  register: async () => {},
  logout: () => {},
  loading: true,
})

export function useAuth() {
  return useContext(AuthContext)
}

const TOKEN_KEY = 'jyotish_token'
const USER_KEY = 'jyotish_user'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<TokenData | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // Load from localStorage on mount
  useEffect(() => {
    const savedToken = localStorage.getItem(TOKEN_KEY)
    const savedUser = localStorage.getItem(USER_KEY)
    if (savedToken && savedUser) {
      try {
        setToken(savedToken)
        setUser(JSON.parse(savedUser))
      } catch {
        localStorage.removeItem(TOKEN_KEY)
        localStorage.removeItem(USER_KEY)
      }
    }
    setLoading(false)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const result = await api.login({ email, password })
    setToken(result.access_token)
    const userData: TokenData = {
      access_token: result.access_token,
      user_id: result.user_id,
      email: result.email,
      name: result.name,
    }
    setUser(userData)
    localStorage.setItem(TOKEN_KEY, result.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(userData))
  }, [])

  const register = useCallback(async (data: Record<string, any>) => {
    const result = await api.register(data)
    setToken(result.access_token)
    const userData: TokenData = {
      access_token: result.access_token,
      user_id: result.user_id,
      email: result.email,
      name: result.name,
    }
    setUser(userData)
    localStorage.setItem(TOKEN_KEY, result.access_token)
    localStorage.setItem(USER_KEY, JSON.stringify(userData))
  }, [])

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }, [])

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated: !!token,
        user,
        token,
        login,
        register,
        logout,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}
