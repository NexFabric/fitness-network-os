import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api, ApiError } from '../api/client'
import { Alert, EmptyState, LoadingSkeleton, PageHeader } from '../components/ui'

type Staff = {
  id: string
  user_id: string
  role: string
  location_id: string | null
  created_at: string
}

type Location = {
  id: string
  name: string
}

const STAFF_ROLES = [
  'GYM_ADMIN',
  'GYM_MANAGER',
  'ACCOUNTANT',
  'FRONT_DESK',
  'TRAINER',
  'STAFF',
] as const

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

function formatApiError(e: unknown, fallback: string): string {
  if (e instanceof ApiError) {
    if (e.status === 403) return 'Bu işlem için yetkiniz yok.'
    return e.status === 400 ? e.message : `${e.status}: ${e.message}`
  }
  if (e instanceof Error) return e.message
  return fallback
}

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
                  <th className="px-3 py-2">Kullanıcı</th>
                  <th className="px-3 py-2">Görev</th>
                  <th className="px-3 py-2">Şube</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/80">
                {staff.map((s) => (
                  <tr key={s.id}>
                    <td className="px-3 py-3 font-mono text-xs text-slate-300">{s.user_id}</td>
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
