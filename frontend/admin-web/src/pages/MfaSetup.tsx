import QRCode from 'qrcode'
import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { homeRouteFor } from '../auth/roles'

type SetupResponse = {
  secret: string
  provisioning_uri: string
  recovery_codes: string[]
}

type SessionResponse = {
  roles: string[]
  is_superuser: boolean
}

type VerifyResponse = {
  success: boolean
  password_change_required: boolean
}

export default function MfaSetup() {
  const navigate = useNavigate()
  const { refresh } = useAuth()
  const [setup, setSetup] = useState<SetupResponse | null>(null)
  const [qrDataUrl, setQrDataUrl] = useState<string | null>(null)
  const [code, setCode] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!setup) {
      setQrDataUrl(null)
      return
    }
    let active = true
    void QRCode.toDataURL(setup.provisioning_uri, {
      width: 220,
      margin: 1,
      errorCorrectionLevel: 'M',
    }).then((url) => {
      if (active) setQrDataUrl(url)
    })
    return () => {
      active = false
    }
  }, [setup])

  async function begin() {
    setBusy(true)
    setError(null)
    try {
      const data = await api<SetupResponse>('/api/v1/auth/mfa/setup', {
        method: 'POST',
        body: {},
        skipAuth: true,
      })
      setSetup(data)
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 401
          ? 'Kurulum oturumu sona erdi. Yeniden giriş yapın.'
          : 'MFA kurulumu başlatılamadı. Tekrar deneyin.',
      )
    } finally {
      setBusy(false)
    }
  }

  async function verify(event: FormEvent) {
    event.preventDefault()
    if (!code.trim()) {
      setError('Doğrulama kodunu girin.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      const result = await api<VerifyResponse>('/api/v1/auth/mfa/verify', {
        method: 'POST',
        body: { code: code.trim() },
        skipAuth: true,
      })

      // Enrollment is not always the last gate: an account provisioned with a
      // one-time password still owes a rotation before it can be used.
      if (result.password_change_required) {
        navigate('/password/change', { replace: true })
        return
      }

      const session = await api<SessionResponse>('/api/v1/me/session')
      await refresh()
      navigate(homeRouteFor(session.roles, session.is_superuser), {
        replace: true,
      })
    } catch (err) {
      setError(
        err instanceof ApiError && err.status === 400
          ? 'Doğrulama kodu geçersiz. Yeni kodla tekrar deneyin.'
          : 'Doğrulama tamamlanamadı. Tekrar deneyin.',
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="login-mesh flex min-h-screen items-center justify-center px-4 py-10">
      <section className="w-full max-w-lg rounded-card border border-slate-800/80 bg-slate-900/70 p-8 shadow-elevated">
        <h1 className="text-xl font-semibold text-ink">İki adımlı doğrulama</h1>
        <p className="mt-2 text-sm text-ink-muted">
          Yetkili hesabınızı kullanmadan önce doğrulama uygulamanızı bağlayın.
        </p>

        {!setup ? (
          <button
            type="button"
            className="btn-primary mt-6 w-full"
            disabled={busy}
            onClick={() => void begin()}
          >
            {busy ? 'Hazırlanıyor…' : 'Kurulumu başlat'}
          </button>
        ) : (
          <form onSubmit={verify} className="mt-6 space-y-5">
            <div className="rounded-card bg-white p-4 text-center">
              {qrDataUrl ? (
                <img
                  src={qrDataUrl}
                  alt="Doğrulama uygulaması kurulum QR kodu"
                  className="mx-auto"
                />
              ) : (
                <p className="text-sm text-slate-700">QR kodu hazırlanıyor…</p>
              )}
            </div>

            <div>
              <p className="label-text">Kurtarma kodları</p>
              <p className="mb-2 text-xs text-ink-muted">
                Bu kodları güvenli bir yerde saklayın. Her kod yalnız bir kez kullanılabilir.
              </p>
              <div className="grid grid-cols-2 gap-2 rounded-card bg-slate-950 p-3 font-mono text-xs text-ink">
                {setup.recovery_codes.map((recoveryCode) => (
                  <span key={recoveryCode}>{recoveryCode}</span>
                ))}
              </div>
            </div>

            <div>
              <label htmlFor="setup-code" className="label-text">
                Uygulamadaki 6 haneli kod
              </label>
              <input
                id="setup-code"
                className="input-field font-mono tracking-widest"
                inputMode="numeric"
                autoComplete="one-time-code"
                value={code}
                onChange={(event) => setCode(event.target.value)}
                disabled={busy}
                autoFocus
              />
            </div>

            <button type="submit" className="btn-primary w-full" disabled={busy}>
              {busy ? 'Doğrulanıyor…' : 'Doğrula ve devam et'}
            </button>
          </form>
        )}

        {error && (
          <p className="alert-error mt-4" role="alert">
            {error}
          </p>
        )}
      </section>
    </main>
  )
}
