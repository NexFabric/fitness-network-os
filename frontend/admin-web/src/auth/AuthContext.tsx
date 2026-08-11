import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { api, ApiError, clearAuth, getTenantId } from '../api/client'
import type { RoleName } from './roles'

/** Mirrors MeSessionResponse in backend/app/api/v1/endpoints/me.py. */
export type Session = {
  user_id: string
  email: string | null
  tenant_id: string
  is_superuser: boolean
  roles: string[]
  permissions: string[]
  has_member_binding: boolean
}

type AuthState = {
  /** null until the first /me/session call settles. */
  session: Session | null
  loading: boolean
  error: string | null
  hasRole: (allowed: RoleName[]) => boolean
  hasPermission: (permission: string) => boolean
  refresh: () => Promise<void>
  signOut: () => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    // X-Tenant-ID is required by /me/session; without it there is nothing to ask.
    if (!getTenantId()) {
      setSession(null)
      setLoading(false)
      return
    }
    setLoading(true)
    setError(null)
    try {
      const data = await api<Session>('/api/v1/me/session')
      setSession(data)
    } catch (err) {
      setSession(null)
      // 401 is handled by the client (redirect to /login); anything else is
      // surfaced so guards fail closed with a visible reason instead of a
      // blank screen.
      if (err instanceof ApiError && err.status !== 401) {
        setError('Oturum bilgileri alınamadı. Sayfayı yenileyin.')
      }
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const signOut = useCallback(() => {
    clearAuth()
    setSession(null)
  }, [])

  const value = useMemo<AuthState>(
    () => ({
      session,
      loading,
      error,
      hasRole: (allowed) =>
        Boolean(
          session &&
            (session.is_superuser ||
              session.roles.some((r) => allowed.includes(r as RoleName))),
        ),
      hasPermission: (permission) =>
        Boolean(
          session &&
            (session.is_superuser || session.permissions.includes(permission)),
        ),
      refresh,
      signOut,
    }),
    [session, loading, error, refresh, signOut],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used inside <AuthProvider>')
  }
  return ctx
}
