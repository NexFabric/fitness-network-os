import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import {
  api,
  ApiError,
  ensureCsrf,
  isAuthenticated,
  setAuth,
} from '../api/client'

type LoginResponse = {
  user_id: string
  expires_at: string
  tenant_id: string | null
}

/**
 * Admin login via POST /api/v1/auth/login (email + password).
 * Session lives in HttpOnly cookie; only tenant_id is stored in localStorage.
 */
export default function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [tenantOverride, setTenantOverride] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)

  if (isAuthenticated()) {
    return <Navigate to="/" replace />
  }

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    const em = email.trim()
    if (!em || !password) {
      setError('E-posta ve şifre gereklidir.')
      return
    }

    const override = tenantOverride.trim()
    if (
      override &&
      !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
        override,
      )
    ) {
      setError('Tenant ID geçerli bir UUID olmalıdır.')
      return
    }

    setSubmitting(true)
    try {
      // Warm CSRF cookie on API origin (login is CSRF-exempt but other POSTs are not)
      await ensureCsrf()
      const data = await api<LoginResponse>('/api/v1/auth/login', {
        method: 'POST',
        body: { email: em, password },
        skipAuth: true,
        skipCsrf: true,
      })

      const tenantId = override || data.tenant_id
      if (!tenantId) {
        setError(
          'Giriş başarılı ancak atanmış bir tenant bulunamadı. Gelişmiş seçeneklerden Tenant ID girin.',
        )
        setShowAdvanced(true)
        return
      }

      setAuth(tenantId)
      navigate('/', { replace: true })
    } catch (err) {
      if (err instanceof ApiError) {
        setError(
          err.status === 401
            ? 'Geçersiz e-posta veya şifre.'
            : `${err.status}: ${err.message}`,
        )
      } else if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Giriş başarısız oldu.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  const sessionExpired =
    typeof window !== 'undefined' &&
    new URLSearchParams(window.location.search).get('reason') === 'session'

  return (
    <div className="login-mesh flex min-h-screen items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div
            className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-card bg-brand shadow-elevated"
            aria-hidden="true"
          >
            <svg
              width="24"
              height="24"
              viewBox="0 0 24 24"
              fill="none"
              stroke="white"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            GymClubNex
          </h1>
          <p className="mt-1.5 text-sm font-medium text-teal-400/90">
            Operasyon Konsolu · Fitness Network OS
          </p>
        </div>

        <div className="rounded-card border border-slate-800/80 bg-slate-900/55 p-8 shadow-elevated backdrop-blur-md">
          <h2 className="text-lg font-semibold text-ink">Giriş yap</h2>
          <p className="mt-1 text-sm text-ink-muted">
            Operasyon personeli erişimi
          </p>
          {sessionExpired && (
            <p className="alert-error mt-4" role="status">
              Oturumunuz sona erdi veya geçersiz. Lütfen yeniden giriş yapın.
            </p>
          )}

          <form onSubmit={onSubmit} className="mt-6 space-y-4" noValidate>
            <div>
              <label htmlFor="email" className="label-text">
                E-posta
              </label>
              <input
                id="email"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={submitting}
                className="input-field"
                placeholder="ornek@kulup.com"
              />
            </div>
            <div>
              <label htmlFor="password" className="label-text">
                Şifre
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={submitting}
                className="input-field"
                placeholder="••••••••"
              />
            </div>

            <button
              type="button"
              className="text-xs font-medium text-ink-muted hover:text-brand-light"
              onClick={() => setShowAdvanced((v) => !v)}
            >
              {showAdvanced ? 'Gelişmiş seçenekleri gizle' : 'Gelişmiş seçenekler'}
            </button>

            {showAdvanced && (
              <div>
                <label htmlFor="tenant" className="label-text">
                  Tenant ID{' '}
                  <span className="font-normal text-ink-muted">(isteğe bağlı)</span>
                </label>
                <input
                  id="tenant"
                  type="text"
                  autoComplete="off"
                  value={tenantOverride}
                  onChange={(e) => setTenantOverride(e.target.value)}
                  disabled={submitting}
                  className="input-field font-mono text-xs"
                  placeholder="Boş bırakılırsa varsayılan tenant kullanılır"
                />
              </div>
            )}

            {error && (
              <p className="alert-error" role="alert">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="btn-primary w-full py-2.5"
            >
              {submitting ? 'Giriş yapılıyor…' : 'Giriş yap'}
            </button>
          </form>
        </div>

        <p className="mt-6 text-center text-xs text-ink-muted">
          Tüketici uygulaması değildir — yalnızca operasyon konsolu
        </p>
      </div>
    </div>
  )
}
