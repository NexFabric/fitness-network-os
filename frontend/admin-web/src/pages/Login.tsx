import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { api, ApiError, isAuthenticated, setAuth } from '../api/client'

type LoginResponse = {
  token: string
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
      setError('Email and password are required.')
      return
    }

    const override = tenantOverride.trim()
    if (
      override &&
      !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
        override,
      )
    ) {
      setError('Tenant override must be a UUID when provided.')
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
          'Login succeeded but no tenant is linked to this user. Set a tenant override or re-run seed_demo.',
        )
        return
      }

      setAuth(data.token, tenantId)
      navigate('/', { replace: true })
    } catch (err) {
      if (err instanceof ApiError) {
        setError(
          err.status === 401
            ? 'Invalid email or password.'
            : `${err.status}: ${err.message}`,
        )
      } else if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('Login failed.')
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
          <p className="mt-1.5 text-sm font-medium text-teal-200/80">
            Staff console · Fitness Network OS
          </p>
        </div>

        <div className="rounded-card border border-white/10 bg-white p-8 shadow-elevated">
          <h2 className="text-lg font-semibold text-ink">Sign in</h2>
          <p className="mt-1 text-sm text-slate-500">
            Staff access for gym operations. Demo credentials from{' '}
            <code className="rounded bg-surface px-1 py-0.5 text-xs text-slate-700">
              seed_demo
            </code>
            .
          </p>

          <form onSubmit={onSubmit} className="mt-6 space-y-4" noValidate>
            <div>
              <label htmlFor="email" className="label-text">
                Email
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
                Password
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
                Tenant ID override{' '}
                <span className="font-normal text-slate-400">(optional)</span>
              </label>
              <input
                id="tenant"
                type="text"
                autoComplete="off"
                value={tenantOverride}
                onChange={(e) => setTenantOverride(e.target.value)}
                disabled={submitting}
                className="input-field font-mono text-xs"
                placeholder="Uses tenant from login response if empty"
              />
            </div>

            {error && (
              <p
                className="rounded-control border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700"
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
              {submitting ? 'Signing in…' : 'Sign in'}
            </button>
          </form>
        </div>

        <p className="mt-6 text-center text-xs text-slate-400">
          Not a consumer app — ops console only
        </p>
      </div>
    </div>
  )
}
