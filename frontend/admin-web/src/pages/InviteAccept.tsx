import { useMemo, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api, ApiError } from '../api/client'

const MIN_LENGTH = 12

export default function InviteAccept() {
  const [params] = useSearchParams()
  const token = useMemo(() => params.get('token')?.trim() ?? '', [params])
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [email, setEmail] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (!token) {
      setError('Davet jetonu eksik.')
      return
    }
    if (password.length < MIN_LENGTH) {
      setError(`Parola en az ${MIN_LENGTH} karakter olmalı.`)
      return
    }
    if (password !== confirm) {
      setError('Parola ile tekrarı aynı değil.')
      return
    }
    setBusy(true)
    try {
      const res = await api<{ email: string }>('/api/v1/auth/invite/accept', {
        method: 'POST',
        body: { token, new_password: password },
        skipAuth: true,
        skipCsrf: true,
      })
      setEmail(res.email)
      window.history.replaceState({}, '', '/invite')
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setError('Bu davet zaten kullanılmış.')
      } else if (err instanceof ApiError && err.status === 404) {
        setError('Davet bulunamadı.')
      } else {
        setError('Davet kabul edilemedi. Jeton süresi dolmuş olabilir.')
      }
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
      <div className="card w-full max-w-md p-8">
        <h1 className="text-xl font-semibold text-slate-100">Daveti kabul et</h1>
        <p className="mt-2 text-sm text-slate-400">
          Size iletilen jetonla parolanızı belirleyin. Jeton bir kez kullanılır.
        </p>
        {email ? (
          <div className="mt-6 text-sm text-emerald-300">
            <p>
              <span className="font-mono">{email}</span> için parola ayarlandı.
            </p>
            <Link to="/login" className="mt-4 inline-block text-brand underline">
              Giriş yap
            </Link>
          </div>
        ) : (
          <form className="mt-6 space-y-4" onSubmit={submit}>
            <div>
              <label htmlFor="invite-pass" className="label-text">
                Yeni parola
              </label>
              <input
                id="invite-pass"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field"
                autoComplete="new-password"
                disabled={busy}
              />
            </div>
            <div>
              <label htmlFor="invite-confirm" className="label-text">
                Parola tekrar
              </label>
              <input
                id="invite-confirm"
                type="password"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className="input-field"
                autoComplete="new-password"
                disabled={busy}
              />
            </div>
            {error && (
              <p className="text-sm text-rose-400" role="alert">
                {error}
              </p>
            )}
            <button type="submit" className="btn-primary w-full" disabled={busy || !token}>
              {busy ? 'Kaydediliyor…' : 'Parolayı kaydet'}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
