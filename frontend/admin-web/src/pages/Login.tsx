import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { isAuthenticated, setAuth } from '../api/client'

/**
 * MVP login: backend uses session cookies / Bearer stub.
 * Staff paste a session token + tenant UUID until a public login API exists.
 */
export default function Login() {
  const navigate = useNavigate()
  const [token, setToken] = useState('')
  const [tenantId, setTenantId] = useState('')
  const [error, setError] = useState<string | null>(null)

  if (isAuthenticated()) {
    return <Navigate to="/" replace />
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    const t = token.trim()
    const tid = tenantId.trim()
    if (!t || !tid) {
      setError('Token and Tenant ID are required.')
      return
    }
    // Basic UUID shape check (not cryptographic validation)
    if (
      !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
        tid,
      )
    ) {
      setError('Tenant ID must be a UUID.')
      return
    }
    setAuth(t, tid)
    navigate('/', { replace: true })
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-100 px-4">
      <div className="w-full max-w-md rounded-xl bg-white p-8 shadow-md">
        <h1 className="text-2xl font-bold text-gray-900">Admin sign-in</h1>
        <p className="mt-2 text-sm text-gray-600">
          Enter a session Bearer token and tenant ID. Values are stored in{' '}
          <code className="rounded bg-gray-100 px-1">localStorage</code> only
          (no secrets in the repo).
        </p>

        <form onSubmit={onSubmit} className="mt-6 space-y-4">
          <div>
            <label
              htmlFor="token"
              className="block text-sm font-medium text-gray-700"
            >
              Session token
            </label>
            <input
              id="token"
              type="password"
              autoComplete="off"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="Bearer token value (without prefix)"
            />
          </div>
          <div>
            <label
              htmlFor="tenant"
              className="block text-sm font-medium text-gray-700"
            >
              Tenant ID (X-Tenant-ID)
            </label>
            <input
              id="tenant"
              type="text"
              autoComplete="off"
              value={tenantId}
              onChange={(e) => setTenantId(e.target.value)}
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 font-mono text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            />
          </div>

          {error && (
            <p className="text-sm text-red-600" role="alert">
              {error}
            </p>
          )}

          <button
            type="submit"
            className="w-full rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            Continue
          </button>
        </form>
      </div>
    </div>
  )
}
