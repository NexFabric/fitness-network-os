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
      setError(formatApiError(e, 'Failed to load locations'))
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
      setFormError('Name is required.')
      return
    }

    setSubmitting(true)
    try {
      await api<Location>('/api/v1/locations', {
        method: 'POST',
        body: { name, timezone, address },
      })
      setForm(emptyForm)
      setFormSuccess('Location created successfully.')
      await loadLocations({ silent: true })
    } catch (err) {
      setFormError(formatApiError(err, 'Failed to create location'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Locations</h1>
      <p className="mt-1 text-sm text-gray-600">
        List and create locations — Branch = Location (locations:read /
        locations:write)
      </p>

      <section
        className="mt-6 rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
        aria-labelledby="create-location-heading"
      >
        <h2
          id="create-location-heading"
          className="text-lg font-semibold text-gray-900"
        >
          Create location
        </h2>
        <form
          className="mt-4 grid gap-4 sm:grid-cols-3"
          onSubmit={handleCreate}
          noValidate
        >
          <div>
            <label
              htmlFor="location_name"
              className="block text-sm font-medium text-gray-700"
            >
              Name <span className="text-red-600">*</span>
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
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              disabled={submitting}
            />
          </div>
          <div>
            <label
              htmlFor="location_timezone"
              className="block text-sm font-medium text-gray-700"
            >
              Timezone
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
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              disabled={submitting}
            />
          </div>
          <div>
            <label
              htmlFor="location_address"
              className="block text-sm font-medium text-gray-700"
            >
              Address
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
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              disabled={submitting}
            />
          </div>
          <div className="sm:col-span-3 flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={submitting}
              className="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {submitting ? 'Creating…' : 'Create location'}
            </button>
            {formError && (
              <p className="text-sm text-red-700" role="alert">
                {formError}
              </p>
            )}
            {formSuccess && (
              <p className="text-sm text-green-700" role="status">
                {formSuccess}
              </p>
            )}
          </div>
        </form>
      </section>

      {loading && (
        <p className="mt-6 text-gray-500" role="status">
          Loading…
        </p>
      )}

      {error && (
        <div
          className="mt-6 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
          role="alert"
        >
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="mt-6 overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-gray-200 text-left text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 font-medium text-gray-700">Name</th>
                <th className="px-4 py-3 font-medium text-gray-700">Timezone</th>
                <th className="px-4 py-3 font-medium text-gray-700">Address</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {locations.length === 0 ? (
                <tr>
                  <td
                    colSpan={3}
                    className="px-4 py-8 text-center text-gray-500"
                  >
                    No locations found.
                  </td>
                </tr>
              ) : (
                locations.map((loc) => (
                  <tr key={loc.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">
                      {loc.name}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs text-gray-700">
                      {loc.timezone}
                    </td>
                    <td className="px-4 py-3 text-gray-600">
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
