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
    <div className="flex min-h-screen items-center justify-center bg-gray-100 px-4">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow-md">
        <h1 className="text-2xl font-bold text-gray-900">Admin sign-in</h1>
        <p className="mt-2 text-sm text-gray-600">
          Use credentials from{' '}
          <code className="rounded bg-gray-100 px-1">
            uv run python scripts/seed_demo.py
          </code>
          . Default:{' '}
          <code className="rounded bg-gray-100 px-1">demo.admin@demo.local</code> /{' '}
          <code className="rounded bg-gray-100 px-1">DemoAdmin123!</code>
        </p>

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={submitting}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="demo.admin@demo.local"
            />
          </div>
          <div>
            <label
              htmlFor="password"
              className="block text-sm font-medium text-gray-700"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={submitting}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="••••••••"
            />
          </div>
          <div>
            <label
              htmlFor="tenant"
              className="block text-sm font-medium text-gray-700"
            >
              Tenant ID override{' '}
              <span className="font-normal text-gray-400">(optional)</span>
            </label>
            <input
              id="tenant"
              type="text"
              autoComplete="off"
              value={tenantOverride}
              onChange={(e) => setTenantOverride(e.target.value)}
              disabled={submitting}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 font-mono text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="Uses tenant from login response if empty"
            />
          </div>

          {error && (
            <p className="text-sm text-red-600" role="alert">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="w-full rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
