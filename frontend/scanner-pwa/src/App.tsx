import { useCallback, useState, type FormEvent } from 'react'
import {
  clearAuth,
  getTenantId,
  getToken,
  setAuth,
  validateQr,
  type ValidateQrResponse,
} from './api/client'
import { CameraQrScanner } from './components/CameraQrScanner'

export default function App() {
  const [sessionToken, setSessionToken] = useState(getToken() ?? '')
  const [tenantId, setTenantId] = useState(getTenantId() ?? '')
  const [qrToken, setQrToken] = useState('')
  const [locationId, setLocationId] = useState('')
  const [consume, setConsume] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ValidateQrResponse | null>(null)
  const [scanning, setScanning] = useState(false)

  function saveCredentials(e: FormEvent) {
    e.preventDefault()
    setError(null)
    const t = sessionToken.trim()
    const tid = tenantId.trim()
    if (!t || !tid) {
      setError('Session token and Tenant ID are required for validate.')
      return
    }
    setAuth(t, tid)
    setError(null)
  }

  const runValidate = useCallback(
    async (tokenRaw: string) => {
      setError(null)
      setResult(null)
      const token = tokenRaw.trim()
      if (!token) {
        setError('QR token is required.')
        return
      }
      // Persist credentials if filled
      if (sessionToken.trim() && tenantId.trim()) {
        setAuth(sessionToken.trim(), tenantId.trim())
      }
      if (!getToken() || !getTenantId()) {
        setError('Save session token and tenant ID first.')
        return
      }

      setBusy(true)
      try {
        const loc = locationId.trim() || null
        const res = await validateQr({
          token,
          location_id: loc,
          consume,
        })
        setResult(res)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Validation request failed')
      } finally {
        setBusy(false)
      }
    },
    [sessionToken, tenantId, locationId, consume],
  )

  async function onValidate(e: FormEvent) {
    e.preventDefault()
    await runValidate(qrToken)
  }

  const onCameraDecode = useCallback(
    (token: string) => {
      setScanning(false)
      setQrToken(token)
      setError(null)
      // Auto-validate when staff credentials are already present
      const hasCreds =
        Boolean(getToken() && getTenantId()) ||
        Boolean(sessionToken.trim() && tenantId.trim())
      if (hasCreds) {
        void runValidate(token)
      }
    },
    [runValidate, sessionToken, tenantId],
  )

  function logout() {
    clearAuth()
    setSessionToken('')
    setTenantId('')
    setResult(null)
  }

  const granted = result?.granted === true
  const denied = result != null && result.granted === false

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto max-w-lg px-4 py-8">
        <header className="mb-8 text-center">
          <p className="text-xs font-semibold uppercase tracking-widest text-emerald-400">
            GymClubNex
          </p>
          <h1 className="mt-1 text-3xl font-bold">Validate QR</h1>
          <p className="mt-2 text-sm text-slate-400">
            POST /api/v1/access/qr/validate · access:validate
          </p>
        </header>

        {/* Staff session credentials */}
        <section className="mb-6 rounded-xl border border-slate-800 bg-slate-900/80 p-4">
          <h2 className="text-sm font-semibold text-slate-200">
            Scanner credentials
          </h2>
          <form onSubmit={saveCredentials} className="mt-3 space-y-3">
            <div>
              <label htmlFor="session" className="text-xs text-slate-400">
                Session token (Bearer)
              </label>
              <input
                id="session"
                type="password"
                autoComplete="off"
                value={sessionToken}
                onChange={(e) => setSessionToken(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
              />
            </div>
            <div>
              <label htmlFor="tenant" className="text-xs text-slate-400">
                Tenant ID
              </label>
              <input
                id="tenant"
                type="text"
                autoComplete="off"
                value={tenantId}
                onChange={(e) => setTenantId(e.target.value)}
                className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-sm focus:border-emerald-500 focus:outline-none"
                placeholder="uuid"
              />
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                className="rounded-md bg-slate-700 px-3 py-1.5 text-sm hover:bg-slate-600"
              >
                Save
              </button>
              <button
                type="button"
                onClick={logout}
                className="rounded-md border border-slate-700 px-3 py-1.5 text-sm text-slate-300 hover:bg-slate-800"
              >
                Clear
              </button>
            </div>
          </form>
        </section>

        {/* Camera capture */}
        <section className="mb-4">
          {!scanning ? (
            <button
              type="button"
              onClick={() => {
                setError(null)
                setResult(null)
                setScanning(true)
              }}
              className="w-full rounded-lg border border-emerald-700/60 bg-emerald-950/40 py-3 text-base font-semibold text-emerald-300 hover:bg-emerald-900/50"
            >
              Scan with camera
            </button>
          ) : (
            <CameraQrScanner
              active={scanning}
              onDecode={onCameraDecode}
              onStop={() => setScanning(false)}
            />
          )}
        </section>

        {/* Validate form (paste fallback) */}
        <form
          onSubmit={onValidate}
          className="rounded-xl border border-slate-800 bg-slate-900 p-4 shadow-lg"
        >
          <div>
            <label htmlFor="qr" className="text-sm font-medium text-slate-200">
              QR token
            </label>
            <textarea
              id="qr"
              rows={4}
              value={qrToken}
              onChange={(e) => setQrToken(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-sm focus:border-emerald-500 focus:outline-none"
              placeholder="Paste signed QR token, or scan with camera…"
            />
          </div>
          <div className="mt-3">
            <label htmlFor="location" className="text-sm font-medium text-slate-200">
              Location ID (optional)
            </label>
            <input
              id="location"
              type="text"
              value={locationId}
              onChange={(e) => setLocationId(e.target.value)}
              className="mt-1 w-full rounded-md border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-sm focus:border-emerald-500 focus:outline-none"
              placeholder="uuid"
            />
          </div>
          <label className="mt-3 flex items-center gap-2 text-sm text-slate-300">
            <input
              type="checkbox"
              checked={consume}
              onChange={(e) => setConsume(e.target.checked)}
              className="rounded border-slate-600"
            />
            Consume entitlement
          </label>

          <button
            type="submit"
            disabled={busy}
            className="mt-4 w-full rounded-lg bg-emerald-600 py-3 text-base font-semibold hover:bg-emerald-500 disabled:opacity-50"
          >
            {busy ? 'Validating…' : 'Validate'}
          </button>
        </form>

        {error && (
          <div
            className="mt-4 rounded-lg border border-red-800 bg-red-950/60 px-4 py-3 text-sm text-red-200"
            role="alert"
          >
            {error}
          </div>
        )}

        {result && (
          <div
            className={`mt-4 rounded-xl border px-5 py-6 text-center ${
              granted
                ? 'border-emerald-600 bg-emerald-950/50'
                : 'border-red-700 bg-red-950/50'
            }`}
            role="status"
            aria-live="polite"
          >
            <p
              className={`text-3xl font-bold tracking-wide ${
                granted ? 'text-emerald-400' : 'text-red-400'
              }`}
            >
              {granted ? 'GRANTED' : 'DENIED'}
            </p>
            {(result.reason || denied) && (
              <p className="mt-2 text-sm text-slate-300">
                Reason: {result.reason ?? '—'}
              </p>
            )}
            {result.member_id && (
              <p className="mt-1 font-mono text-xs text-slate-400">
                member: {result.member_id}
              </p>
            )}
            {result.remaining != null && (
              <p className="mt-1 text-xs text-slate-400">
                remaining: {result.remaining}
              </p>
            )}
            {result.jti && (
              <p className="mt-1 font-mono text-xs text-slate-500">
                jti: {result.jti}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
