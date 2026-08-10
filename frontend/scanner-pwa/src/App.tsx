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
  const [credsOpen, setCredsOpen] = useState(
    () => !getToken() || !getTenantId(),
  )

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
    setCredsOpen(false)
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
        setCredsOpen(true)
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
    setCredsOpen(true)
  }

  const granted = result?.granted === true
  const denied = result != null && result.granted === false
  const hasSavedCreds = Boolean(getToken() && getTenantId())

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto max-w-lg px-4 py-8">
        <header className="mb-8 text-center">
          <div className="mx-auto mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-teal-600/20 ring-1 ring-teal-500/40">
            <span className="text-lg font-bold text-emerald-400" aria-hidden>
              G
            </span>
          </div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-emerald-400">
            GymClubNex · Access
          </p>
          <h1 className="mt-2 text-2xl font-bold tracking-tight text-white sm:text-3xl">
            Door scanner
          </h1>
          <p className="mt-2 text-sm text-slate-400">
            Scan or paste a member QR to grant entry.
          </p>
        </header>

        {/* Staff session credentials — softened / collapsible */}
        <section className="mb-6 rounded-xl border border-slate-800/80 bg-slate-900/50 p-3">
          <button
            type="button"
            onClick={() => setCredsOpen((o) => !o)}
            className="flex w-full items-center justify-between gap-2 rounded-lg px-1 py-1 text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/60"
            aria-expanded={credsOpen}
          >
            <div>
              <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                Staff session
              </h2>
              <p className="mt-0.5 text-xs text-slate-500">
                {hasSavedCreds
                  ? 'Credentials saved on this device'
                  : 'Required before validating'}
              </p>
            </div>
            <span className="text-xs text-slate-500" aria-hidden>
              {credsOpen ? 'Hide' : 'Show'}
            </span>
          </button>
          {credsOpen && (
            <form onSubmit={saveCredentials} className="mt-3 space-y-3 border-t border-slate-800/80 pt-3">
              <div>
                <label htmlFor="session" className="text-xs text-slate-500">
                  Session token
                </label>
                <input
                  id="session"
                  type="password"
                  autoComplete="off"
                  value={sessionToken}
                  onChange={(e) => setSessionToken(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950/80 px-3 py-2 text-sm text-slate-200 placeholder:text-slate-600 focus:border-teal-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/40"
                />
              </div>
              <div>
                <label htmlFor="tenant" className="text-xs text-slate-500">
                  Tenant ID
                </label>
                <input
                  id="tenant"
                  type="text"
                  autoComplete="off"
                  value={tenantId}
                  onChange={(e) => setTenantId(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-slate-800 bg-slate-950/80 px-3 py-2 font-mono text-sm text-slate-200 placeholder:text-slate-600 focus:border-teal-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/40"
                  placeholder="uuid"
                />
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  className="rounded-lg bg-slate-800 px-3 py-1.5 text-sm text-slate-200 hover:bg-slate-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/60"
                >
                  Save
                </button>
                <button
                  type="button"
                  onClick={logout}
                  className="rounded-lg border border-slate-800 px-3 py-1.5 text-sm text-slate-400 hover:bg-slate-900 hover:text-slate-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/60"
                >
                  Clear
                </button>
              </div>
            </form>
          )}
        </section>

        {/* Camera capture */}
        <section className="mb-4" aria-labelledby="camera-heading">
          <h2
            id="camera-heading"
            className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400"
          >
            Camera
          </h2>
          {!scanning ? (
            <button
              type="button"
              onClick={() => {
                setError(null)
                setResult(null)
                setScanning(true)
              }}
              className="w-full rounded-xl border border-teal-700/50 bg-teal-950/30 py-3.5 text-base font-semibold text-emerald-300 shadow-sm hover:bg-teal-900/40 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950"
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
          className="rounded-xl border border-slate-800 bg-slate-900/90 p-4 shadow-lg"
          aria-labelledby="paste-heading"
        >
          <h2
            id="paste-heading"
            className="text-xs font-semibold uppercase tracking-wide text-slate-400"
          >
            Paste token
          </h2>
          <div className="mt-3">
            <label htmlFor="qr" className="text-sm font-medium text-slate-200">
              QR token
            </label>
            <textarea
              id="qr"
              rows={4}
              value={qrToken}
              onChange={(e) => setQrToken(e.target.value)}
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-sm focus:border-teal-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/40"
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
              className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 font-mono text-sm focus:border-teal-600 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/40"
              placeholder="uuid"
            />
          </div>
          <label className="mt-3 flex items-center gap-2 text-sm text-slate-300">
            <input
              type="checkbox"
              checked={consume}
              onChange={(e) => setConsume(e.target.checked)}
              className="rounded border-slate-600 text-teal-600 focus:ring-emerald-400/40"
            />
            Consume entitlement
          </label>

          <button
            type="submit"
            disabled={busy}
            className="mt-4 w-full rounded-xl bg-teal-600 py-3 text-base font-semibold text-white shadow-sm hover:bg-teal-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 disabled:opacity-50"
          >
            {busy ? 'Validating…' : 'Validate entry'}
          </button>
        </form>

        {error && (
          <div
            className="mt-4 rounded-xl border border-red-800/80 bg-red-950/60 px-4 py-3 text-sm text-red-200"
            role="alert"
          >
            {error}
          </div>
        )}

        {result && (
          <div
            className={`mt-4 rounded-xl border-2 px-5 py-8 text-center ${
              granted
                ? 'border-emerald-500 bg-emerald-950/60'
                : 'border-red-600 bg-red-950/60'
            }`}
            role="status"
            aria-live="polite"
          >
            {/* Icon + text — not color alone (a11y) */}
            <div
              className={`mx-auto mb-3 flex h-16 w-16 items-center justify-center rounded-full ${
                granted
                  ? 'bg-emerald-500/20 text-emerald-400 ring-2 ring-emerald-400/50'
                  : 'bg-red-500/20 text-red-400 ring-2 ring-red-400/50'
              }`}
              aria-hidden
            >
              {granted ? (
                <svg
                  className="h-9 w-9"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg
                  className="h-9 w-9"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <path d="M6 6l12 12M18 6L6 18" />
                </svg>
              )}
            </div>
            <p
              className={`text-4xl font-extrabold tracking-widest ${
                granted ? 'text-emerald-400' : 'text-red-400'
              }`}
            >
              {granted ? 'GRANT' : 'DENY'}
            </p>
            <p
              className={`mt-1 text-sm font-medium ${
                granted ? 'text-emerald-200/90' : 'text-red-200/90'
              }`}
            >
              {granted ? 'Entry allowed' : 'Entry not allowed'}
            </p>
            {(result.reason || denied) && (
              <p className="mt-3 text-sm text-slate-300">
                Reason: {result.reason ?? '—'}
              </p>
            )}
            {result.member_id && (
              <p className="mt-2 font-mono text-xs text-slate-400">
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
