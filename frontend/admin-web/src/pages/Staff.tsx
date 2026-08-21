import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api, formatApiError } from '../api/client'
import { Alert, EmptyState, LoadingSkeleton, PageHeader } from '../components/ui'

type Staff = {
  id: string
  user_id: string
  email?: string | null
  role: string
  location_id: string | null
  created_at: string
}

type Location = {
  id: string
  name: string
}

type CreatedAccount = {
  staff: Staff
  user_id: string
  email: string
  invite_token?: string | null
}

// Must stay in step with ALLOWED_STAFF_ROLES in backend/app/services/staff.py —
// anything offered here that the backend does not know fails with
// invalid_staff_role after the user has already filled the form.
const STAFF_ROLES = [
  'GYM_ADMIN',
  'GYM_MANAGER',
  'ACCOUNTANT',
  'FRONT_DESK',
  'TRAINER',
  'MANAGER',
  'ADMIN',
  'STAFF',
] as const

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

export default function Staff() {
  const [staff, setStaff] = useState<Staff[]>([])
  const [locations, setLocations] = useState<Location[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [userId, setUserId] = useState('')
  const [role, setRole] = useState<string>('FRONT_DESK')
  const [locationId, setLocationId] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [formMessage, setFormMessage] = useState<string | null>(null)

  const [newEmail, setNewEmail] = useState('')
  const [newRole, setNewRole] = useState<string>('FRONT_DESK')
  const [newLocationId, setNewLocationId] = useState('')
  const [creating, setCreating] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [created, setCreated] = useState<CreatedAccount | null>(null)
  const [copied, setCopied] = useState(false)

  const load = useCallback(async (opts?: { silent?: boolean }) => {
    if (!opts?.silent) {
      setLoading(true)
      setError(null)
    }
    try {
      const [staffRows, locationRows] = await Promise.all([
        api<Staff[]>('/api/v1/staff'),
        api<Location[]>('/api/v1/locations'),
      ])
      setStaff(staffRows)
      setLocations(locationRows)
      setError(null)
    } catch (e) {
      setError(formatApiError(e, 'Personel listesi yüklenemedi'))
    } finally {
      if (!opts?.silent) setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  useEffect(() => {
    if (!created) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setCreated(null)
        setCopied(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [created])

  async function handleLink(e: FormEvent) {
    e.preventDefault()
    setFormError(null)
    setFormMessage(null)

    const trimmed = userId.trim()
    if (!UUID_RE.test(trimmed)) {
      setFormError('Geçerli bir kullanıcı ID (UUID) girin.')
      return
    }

    setSubmitting(true)
    try {
      await api<Staff>('/api/v1/staff', {
        method: 'POST',
        body: {
          user_id: trimmed,
          role,
          location_id: locationId || null,
        },
      })
      setUserId('')
      setLocationId('')
      setFormMessage('Personel bağlandı.')
      await load({ silent: true })
    } catch (err) {
      setFormError(formatApiError(err, 'Personel bağlanamadı'))
    } finally {
      setSubmitting(false)
    }
  }

  async function handleCreateAccount(e: FormEvent) {
    e.preventDefault()
    setCreateError(null)
    setCreated(null)
    setCopied(false)

    const email = newEmail.trim()
    if (!email) {
      setCreateError('E-posta adresi girin.')
      return
    }

    setCreating(true)
    try {
      const account = await api<CreatedAccount>('/api/v1/staff/accounts', {
        method: 'POST',
        body: {
          email,
          role: newRole,
          location_id: newLocationId || null,
        },
      })
      setCreated(account)
      setNewEmail('')
      setNewLocationId('')
      await load({ silent: true })
    } catch (err) {
      setCreateError(formatApiError(err, 'Hesap oluşturulamadı'))
    } finally {
      setCreating(false)
    }
  }

  async function copyPassword() {
    if (!created?.invite_token) return
    try {
      await navigator.clipboard.writeText(
        `${window.location.origin}/invite?token=${created.invite_token}`,
      )
      setCopied(true)
    } catch {
      setCopied(false)
    }
  }

  const locationName = (id: string | null) =>
    id ? (locations.find((l) => l.id === id)?.name ?? '—') : 'Tüm şubeler'

  return (
    <div>
      <PageHeader
        title="Personel"
        subtitle="Kullanıcıları bu salona personel olarak bağlayın"
      />

      {error && (
        <div className="mt-6">
          <Alert onRetry={() => void load()}>{error}</Alert>
        </div>
      )}

      <section className="card mt-6" aria-labelledby="create-account-heading">
        <div className="card-header">
          <h2
            id="create-account-heading"
            className="text-base font-semibold text-slate-100"
          >
            Yeni personel hesabı oluştur
          </h2>
        </div>
        <p className="mt-2 text-sm text-slate-400">
          Hesabı oluşturur ve bu salona bağlar. Tek kullanımlık bir parola üretilir;
          personel ilk girişte bu parolayı değiştirmek zorundadır.
        </p>
        <form
          className="mt-4 grid gap-4 sm:grid-cols-3"
          onSubmit={handleCreateAccount}
          noValidate
        >
          <div>
            <label htmlFor="new_staff_email" className="label-text">
              E-posta <span className="text-teal-500">*</span>
            </label>
            <input
              id="new_staff_email"
              type="email"
              required
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              className="input-field"
              disabled={creating}
              placeholder="ad.soyad@salon.com"
            />
          </div>
          <div>
            <label htmlFor="new_staff_role" className="label-text">
              Görev
            </label>
            <select
              id="new_staff_role"
              value={newRole}
              onChange={(e) => setNewRole(e.target.value)}
              className="input-field"
              disabled={creating}
            >
              {STAFF_ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="new_staff_location" className="label-text">
              Şube
            </label>
            <select
              id="new_staff_location"
              value={newLocationId}
              onChange={(e) => setNewLocationId(e.target.value)}
              className="input-field"
              disabled={creating}
            >
              <option value="">Tüm şubeler</option>
              {locations.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-wrap items-center gap-3 sm:col-span-3">
            <button type="submit" className="btn-primary" disabled={creating}>
              {creating ? 'Oluşturuluyor…' : 'Hesap oluştur'}
            </button>
            {createError && <Alert variant="error">{createError}</Alert>}
          </div>
        </form>

        {created && (
          <div
            className="mt-4 rounded-lg border border-amber-500/40 bg-amber-500/10 p-4"
            role="status"
            aria-live="polite"
          >
            <h3 className="text-sm font-semibold text-amber-200">
              Davet yalnızca şimdi görünür
            </h3>
            <p className="mt-1 text-sm text-amber-100/80">
              <span className="font-medium">{created.email}</span> hesabı oluşturuldu.
              Personel parolasını davet bağlantısından belirler — jeton 7 gün,
              bir kez geçerlidir.
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <code className="select-all rounded bg-slate-950/60 px-3 py-2 font-mono text-sm text-slate-100">
                {created.invite_token}
              </code>
              <button type="button" className="btn-secondary" onClick={copyPassword}>
                {copied ? 'Kopyalandı' : 'Bağlantıyı kopyala'}
              </button>
              <button
                type="button"
                className="btn-secondary"
                onClick={() => {
                  setCreated(null)
                  setCopied(false)
                }}
              >
                Gizle
              </button>
            </div>
            {created.invite_token && (
              <p className="mt-3 text-xs text-amber-100/70 break-all">
                Davet jetonu (7 gün):{' '}
                <a
                  className="underline"
                  href={`/invite?token=${encodeURIComponent(created.invite_token)}`}
                >
                  /invite
                </a>
                <span className="ml-2 font-mono">{created.invite_token}</span>
              </p>
            )}
          </div>
        )}
      </section>

      <section className="card mt-6" aria-labelledby="link-staff-heading">
        <div className="card-header">
          <h2 id="link-staff-heading" className="text-base font-semibold text-slate-100">
            Personel bağla
          </h2>
        </div>
        <p className="mt-2 text-sm text-slate-400">
          Bağlama var olan bir kullanıcı hesabını gerektirir — bu ekran kullanıcı
          oluşturmaz, mevcut kullanıcıyı bu salona bağlar.
        </p>
        <form className="mt-4 grid gap-4 sm:grid-cols-3" onSubmit={handleLink} noValidate>
          <div>
            <label htmlFor="staff_user_id" className="label-text">
              Kullanıcı ID <span className="text-teal-500">*</span>
            </label>
            <input
              id="staff_user_id"
              type="text"
              required
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              className="input-field font-mono text-xs"
              disabled={submitting}
              placeholder="00000000-0000-0000-0000-000000000000"
            />
          </div>
          <div>
            <label htmlFor="staff_role" className="label-text">
              Görev
            </label>
            <select
              id="staff_role"
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="input-field"
              disabled={submitting}
            >
              {STAFF_ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="staff_location" className="label-text">
              Şube
            </label>
            <select
              id="staff_location"
              value={locationId}
              onChange={(e) => setLocationId(e.target.value)}
              className="input-field"
              disabled={submitting}
            >
              <option value="">Tüm şubeler</option>
              {locations.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name}
                </option>
              ))}
            </select>
          </div>
          <div className="flex flex-wrap items-center gap-3 sm:col-span-3">
            <button type="submit" className="btn-primary" disabled={submitting}>
              {submitting ? 'Bağlanıyor…' : 'Personel bağla'}
            </button>
            {formError && <Alert variant="error">{formError}</Alert>}
            {formMessage && <Alert variant="success">{formMessage}</Alert>}
          </div>
        </form>
      </section>

      <section className="card mt-6" aria-labelledby="staff-list-heading">
        <div className="card-header">
          <h2 id="staff-list-heading" className="text-base font-semibold text-slate-100">
            Kayıtlı personel
          </h2>
        </div>
        {loading ? (
          <div className="mt-4">
            <LoadingSkeleton rows={3} />
          </div>
        ) : staff.length === 0 ? (
          <div className="mt-4">
            <EmptyState
              title="Henüz personel yok"
              description="Yukarıdaki formla bir kullanıcıyı bu salona bağlayın."
            />
          </div>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-3 py-2">E-posta</th>
                  <th className="px-3 py-2">Görev</th>
                  <th className="px-3 py-2">Şube</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {staff.map((s) => (
                  <tr key={s.id}>
                    <td className="px-3 py-3 text-slate-200">
                      <div>{s.email || '—'}</div>
                      <div className="mt-0.5 font-mono text-[11px] text-slate-500">{s.user_id}</div>
                    </td>
                    <td className="px-3 py-3 text-slate-200">{s.role}</td>
                    <td className="px-3 py-3 text-slate-400">{locationName(s.location_id)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
