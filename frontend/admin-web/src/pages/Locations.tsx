import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api, ApiError } from '../api/client'

type Location = {
  id: string
  name: string
  timezone: string
  address: string | null
}

type CreateLocationForm = {
  name: string
  timezone: string
  address: string
}

const emptyForm: CreateLocationForm = {
  name: '',
  timezone: 'UTC',
  address: '',
}

function formatApiError(e: unknown, fallback: string): string {
  if (e instanceof ApiError) {
    return `${e.status}: ${e.message}`
  }
  if (e instanceof Error) return e.message
  return fallback
}

export default function Locations() {
  const [locations, setLocations] = useState<Location[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [form, setForm] = useState<CreateLocationForm>(emptyForm)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [formSuccess, setFormSuccess] = useState<string | null>(null)

  const loadLocations = useCallback(async (opts?: { silent?: boolean }) => {
    const silent = opts?.silent ?? false
    if (!silent) {
      setLoading(true)
      setError(null)
    }
    try {
      const data = await api<Location[]>('/api/v1/locations')
      setLocations(data)
      if (silent) setError(null)
    } catch (e) {
      setError(formatApiError(e, 'Şubeler yüklenemedi'))
    } finally {
      if (!silent) setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadLocations()
  }, [loadLocations])

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    setFormError(null)
    setFormSuccess(null)

    const name = form.name.trim()
    const timezone = form.timezone.trim() || 'UTC'
    const addressTrimmed = form.address.trim()
    const address = addressTrimmed.length > 0 ? addressTrimmed : null

    if (!name) {
      setFormError('Şube adı gereklidir.')
      return
    }

    setSubmitting(true)
    try {
      await api<Location>('/api/v1/locations', {
        method: 'POST',
        body: { name, timezone, address },
      })
      setForm(emptyForm)
      setFormSuccess('Şube başarıyla oluşturuldu.')
      await loadLocations({ silent: true })
    } catch (err) {
      setFormError(formatApiError(err, 'Şube oluşturulamadı'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <h1 className="page-title">Şubeler</h1>
      <p className="page-subtitle">
        Bu salonun şubeleri — Şube = Lokasyon
      </p>

      <section className="card mt-6" aria-labelledby="create-location-heading">
        <div className="card-header">
          <h2
            id="create-location-heading"
            className="text-base font-semibold text-slate-100"
          >
            Şube Oluştur
          </h2>
        </div>
        <form
          className="mt-4 grid gap-4 sm:grid-cols-3"
          onSubmit={handleCreate}
          noValidate
        >
          <div>
            <label htmlFor="location_name" className="label-text">
              İsim <span className="text-teal-500">*</span>
            </label>
            <input
              id="location_name"
              name="name"
              type="text"
              required
              maxLength={200}
              autoComplete="organization"
              value={form.name}
              onChange={(ev) =>
                setForm((f) => ({ ...f, name: ev.target.value }))
              }
              className="input-field"
              disabled={submitting}
            />
          </div>
          <div>
            <label htmlFor="location_timezone" className="label-text">
              Zaman Dilimi
            </label>
            <input
              id="location_timezone"
              name="timezone"
              type="text"
              maxLength={64}
              autoComplete="off"
              placeholder="UTC"
              value={form.timezone}
              onChange={(ev) =>
                setForm((f) => ({ ...f, timezone: ev.target.value }))
              }
              className="input-field"
              disabled={submitting}
            />
          </div>
          <div>
            <label htmlFor="location_address" className="label-text">
              Adres
            </label>
            <input
              id="location_address"
              name="address"
              type="text"
              maxLength={500}
              autoComplete="street-address"
              value={form.address}
              onChange={(ev) =>
                setForm((f) => ({ ...f, address: ev.target.value }))
              }
              className="input-field"
              disabled={submitting}
            />
          </div>
          <div className="flex flex-wrap items-center gap-3 sm:col-span-3">
            <button type="submit" disabled={submitting} className="btn-primary">
              {submitting ? 'Oluşturuluyor…' : 'Şube Oluştur'}
            </button>
            {formError && (
              <p className="text-sm text-rose-400" role="alert">
                {formError}
              </p>
            )}
            {formSuccess && (
              <p className="text-sm font-medium text-emerald-400" role="status">
                {formSuccess}
              </p>
            )}
          </div>
        </form>
      </section>

      {loading && (
        <p className="mt-6 text-sm text-slate-400" role="status">
          Şubeler yükleniyor…
        </p>
      )}

      {error && (
        <div
          className="mt-6 rounded-control border border-rose-800/80 bg-rose-950/50 px-4 py-3 text-sm text-rose-300"
          role="alert"
        >
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="table-shell mt-6">
          <table className="min-w-full divide-y divide-slate-800 text-left">
            <thead className="bg-slate-900/80 backdrop-blur-md">
              <tr>
                <th className="table-th">İsim</th>
                <th className="table-th">Zaman Dilimi</th>
                <th className="table-th">Adres</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {locations.length === 0 ? (
                <tr>
                  <td
                    colSpan={3}
                    className="px-4 py-12 text-center text-sm text-slate-500"
                  >
                    <p className="font-medium text-slate-300">
                      Henüz şube yok
                    </p>
                    <p className="mt-1">
                      Yukarıdaki formu kullanarak ilk şubeyi oluşturun.
                    </p>
                  </td>
                </tr>
              ) : (
                locations.map((loc) => (
                  <tr key={loc.id} className="transition-colors hover:bg-slate-800/50">
                    <td className="table-td font-medium text-slate-200">{loc.name}</td>
                    <td className="table-td font-mono text-xs text-slate-400">
                      {loc.timezone}
                    </td>
                    <td className="table-td text-slate-400">
                      {loc.address ?? '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
