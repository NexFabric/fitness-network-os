import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { api, ApiError, ensureCsrf, setAuth } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { homeRouteFor } from '../auth/roles'

type LoginResponse = {
  user_id: string
  expires_at: string
  tenant_id: string | null
  mfa_required: boolean
  mfa_enrollment_required: boolean
}

/**
 * Admin login via POST /api/v1/auth/login (email + password).
 * Session lives in HttpOnly cookie; only tenant_id is stored in localStorage.
 */
export default function Login() {
  const navigate = useNavigate()
  const { session, refresh } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [mfaCode, setMfaCode] = useState('')
  const [mfaRequired, setMfaRequired] = useState(false)
  const [tenantOverride, setTenantOverride] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [showAdvanced, setShowAdvanced] = useState(false)

  if (session) {
    return (
      <Navigate to={homeRouteFor(session.roles, session.is_superuser)} replace />
    )
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
        body: {
          email: em,
          password,
          ...(mfaCode.trim() ? { mfa_code: mfaCode.trim() } : {}),
        },
        skipAuth: true,
        skipCsrf: true,
      })

      // A federation/platform principal has no tenant — that is valid, so an
      // absent tenant_id must not be treated as a failed login.
      const tenantId = override || data.tenant_id
      if (tenantId) {
        setAuth(tenantId)
      }

      if (data.mfa_enrollment_required) {
        navigate('/mfa/setup', { replace: true })
        return
      }

      // Ask the server who this is, then land on the portal that matches.
      // Without this every role would be dropped into the ops console.
      const me = await api<{ roles: string[]; is_superuser: boolean }>(
        '/api/v1/me/session',
      )

      if (me.roles.length === 0 && !me.is_superuser) {
        setError(
          'Giriş başarılı ancak hesabınıza rol tanımlanmamış. Kulüp yöneticinizle iletişime geçin.',
        )
        setShowAdvanced(true)
        return
      }

      await refresh()
      navigate(homeRouteFor(me.roles, me.is_superuser), { replace: true })
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401 && err.message === 'mfa_required') {
          setMfaRequired(true)
          setError('Devam etmek için doğrulama kodunuzu girin.')
          return
        }
        setError(
          err.status === 401 && err.message === 'mfa_invalid'
            ? 'Doğrulama kodu geçersiz. Yeni kodla tekrar deneyin.'
            : err.status === 401 && err.message === 'mfa_locked_out'
              ? 'Çok fazla hatalı deneme yapıldı. 15 dakika sonra tekrar deneyin.'
              : err.status === 401
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

            {mfaRequired && (
              <div>
                <label htmlFor="mfa-code" className="label-text">
                  Doğrulama kodu
                </label>
                <input
                  id="mfa-code"
                  type="text"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  value={mfaCode}
                  onChange={(e) => setMfaCode(e.target.value)}
                  disabled={submitting}
                  className="input-field font-mono tracking-widest"
                  placeholder="000000"
                  autoFocus
                />
              </div>
            )}
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
