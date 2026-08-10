import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { api, ApiError, isAuthenticated, setAuth } from '../api/client'

type LoginResponse = {
  user_id: string
  expires_at: string
  tenant_id: string | null
}

/**
 * Admin login via POST /api/v1/auth/login (email + password).
 * Stores Bearer token + tenant_id in localStorage.
 */
export default function Login() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [tenantOverride, setTenantOverride] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

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
      setError('Tenant ID (İsteğe bağlı) geçerli bir UUID olmalıdır.')
      return
    }

    setSubmitting(true)
    try {
      const data = await api<LoginResponse>('/api/v1/auth/login', {
        method: 'POST',
        body: { email: em, password },
        skipAuth: true,
      })

      const tenantId = override || data.tenant_id
      if (!tenantId) {
        setError(
          "Giriş başarılı ancak kullanıcıya atanmış bir tenant bulunamadı. Tenant ID girin veya seed_demo'yu tekrar çalıştırın.",
        )
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

  return (
    <div className="login-mesh flex min-h-screen items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        {/* Brand mark */}
        <div className="mb-8 text-center">
          <div
            className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-card bg-brand shadow-elevated"
            aria-hidden="true"
          >
            <span className="text-lg font-bold tracking-tight text-white">G</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            GymClubNex
          </h1>
          <p className="mt-1.5 text-sm font-medium text-teal-400/80">
            Operasyon Konsolu · Fitness Network OS
          </p>
        </div>

        <div className="rounded-card border border-slate-800/80 bg-slate-900/50 p-8 shadow-elevated backdrop-blur-md">
          <h2 className="text-lg font-semibold text-ink">Giriş Yap</h2>
          <p className="mt-1 text-sm text-slate-500">
            Operasyon personeli erişimi. 
            <code className="rounded bg-slate-800 ml-1 px-1 py-0.5 text-xs text-slate-300">
              seed_demo
            </code>
          </p>

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
                placeholder="demo.admin@demo.local"
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
            <div>
              <label htmlFor="tenant" className="label-text">
                Tenant ID{' '}
                <span className="font-normal text-slate-500">(İsteğe bağlı)</span>
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

            {error && (
              <p
                className="rounded-control border border-rose-800 bg-rose-950/30 px-3 py-2 text-sm text-rose-400"
                role="alert"
              >
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="btn-primary w-full py-2.5"
            >
              {submitting ? 'Giriş yapılıyor…' : 'Giriş Yap'}
            </button>
          </form>
        </div>

        <p className="mt-6 text-center text-xs text-slate-500">
          Tüketici uygulaması değildir — yalnızca operasyon konsolu
        </p>
      </div>
    </div>
  )
}
