import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { homeRouteFor } from '../auth/roles'

/** Mirrors PasswordChangeResponse in backend/app/api/v1/endpoints/auth.py. */
type PasswordChangeResponse = {
  expires_at: string
  mfa_enrollment_required: boolean
}

type SessionResponse = {
  roles: string[]
  is_superuser: boolean
}

const MIN_LENGTH = 12

export default function PasswordChange() {
  const navigate = useNavigate()
  const { refresh } = useAuth()
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setError(null)

    if (newPassword.length < MIN_LENGTH) {
      setError(`Yeni parola en az ${MIN_LENGTH} karakter olmalı.`)
      return
    }
    if (newPassword !== confirmPassword) {
      setError('Yeni parola ile tekrarı aynı değil.')
      return
    }
    if (newPassword === currentPassword) {
      setError('Yeni parola eskisiyle aynı olamaz.')
      return
    }

    setBusy(true)
    try {
      const result = await api<PasswordChangeResponse>('/api/v1/auth/password', {
        method: 'POST',
        body: {
          current_password: currentPassword,
          new_password: newPassword,
        },
        skipAuth: true,
      })

      // A privileged account can still owe MFA enrollment after rotating.
      if (result.mfa_enrollment_required) {
        navigate('/mfa/setup', { replace: true })
        return
      }

      const session = await api<SessionResponse>('/api/v1/me/session')
      await refresh()
      navigate(homeRouteFor(session.roles, session.is_superuser), { replace: true })
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        setError('Mevcut parola hatalı ya da oturum sona erdi.')
      } else if (err instanceof ApiError && err.status === 400) {
        setError('Yeni parola eskisiyle aynı olamaz.')
      } else if (err instanceof ApiError && err.status === 422) {
        setError(`Yeni parola en az ${MIN_LENGTH} karakter olmalı.`)
      } else {
        setError('Parola değiştirilemedi. Tekrar deneyin.')
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="login-mesh flex min-h-screen items-center justify-center px-4 py-10">
      <section className="w-full max-w-lg rounded-card border border-slate-800/80 bg-slate-900/70 p-8 shadow-elevated">
        <h1 className="text-xl font-semibold text-ink">Parolanızı belirleyin</h1>
        <p className="mt-2 text-sm text-ink-muted">
          Hesabınız geçici bir parolayla açıldı. Devam etmeden önce kendi
          parolanızı belirleyin.
        </p>

        <form onSubmit={submit} className="mt-6 space-y-5" noValidate>
          <div>
            <label htmlFor="current_password" className="label-text">
              Geçici parola <span className="text-teal-500">*</span>
            </label>
            <input
              id="current_password"
              type="password"
              autoComplete="current-password"
              required
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="input-field"
              disabled={busy}
            />
          </div>

          <div>
            <label htmlFor="new_password" className="label-text">
              Yeni parola <span className="text-teal-500">*</span>
            </label>
            <input
              id="new_password"
              type="password"
              autoComplete="new-password"
              required
              minLength={MIN_LENGTH}
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="input-field"
              disabled={busy}
              aria-describedby="new_password_hint"
            />
            <p id="new_password_hint" className="mt-1 text-xs text-ink-muted">
              En az {MIN_LENGTH} karakter.
            </p>
          </div>

          <div>
            <label htmlFor="confirm_password" className="label-text">
              Yeni parola (tekrar) <span className="text-teal-500">*</span>
            </label>
            <input
              id="confirm_password"
              type="password"
              autoComplete="new-password"
              required
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="input-field"
              disabled={busy}
            />
          </div>

          {error && (
            <p role="alert" className="text-sm text-rose-300">
              {error}
            </p>
          )}

          <button type="submit" className="btn-primary w-full" disabled={busy}>
            {busy ? 'Kaydediliyor…' : 'Parolayı kaydet'}
          </button>
        </form>
      </section>
    </main>
  )
}
