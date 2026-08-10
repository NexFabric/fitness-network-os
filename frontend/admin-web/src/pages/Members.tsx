import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { api, ApiError } from '../api/client'

type Member = {
  id: string
  member_number: string
  first_name: string
  last_name: string
  email: string | null
  phone: string | null
  status: string
}

type CreateMemberForm = {
  member_number: string
  first_name: string
  last_name: string
}

const emptyForm: CreateMemberForm = {
  member_number: '',
  first_name: '',
  last_name: '',
}

function formatApiError(e: unknown, fallback: string): string {
  if (e instanceof ApiError) {
    return `${e.status}: ${e.message}`
  }
  if (e instanceof Error) return e.message
  return fallback
}

export default function Members() {
  const [members, setMembers] = useState<Member[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [form, setForm] = useState<CreateMemberForm>(emptyForm)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [formSuccess, setFormSuccess] = useState<string | null>(null)

  const loadMembers = useCallback(async (opts?: { silent?: boolean }) => {
    const silent = opts?.silent ?? false
    if (!silent) {
      setLoading(true)
      setError(null)
    }
    try {
      const data = await api<Member[]>('/api/v1/members')
      setMembers(data)
      if (silent) setError(null)
    } catch (e) {
      setError(formatApiError(e, 'Failed to load members'))
    } finally {
      if (!silent) setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadMembers()
  }, [loadMembers])

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    setFormError(null)
    setFormSuccess(null)

    const member_number = form.member_number.trim()
    const first_name = form.first_name.trim()
    const last_name = form.last_name.trim()

    if (!member_number || !first_name || !last_name) {
      setFormError('Member number, first name, and last name are required.')
      return
    }

    setSubmitting(true)
    try {
      await api<Member>('/api/v1/members', {
        method: 'POST',
        body: { member_number, first_name, last_name },
      })
      setForm(emptyForm)
      setFormSuccess('Member created successfully.')
      await loadMembers({ silent: true })
    } catch (err) {
      setFormError(formatApiError(err, 'Failed to create member'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Members</h1>
      <p className="mt-1 text-sm text-gray-600">
        List and create members (members:read / members:write)
      </p>

      <section
        className="mt-6 rounded-lg border border-gray-200 bg-white p-4 shadow-sm"
        aria-labelledby="create-member-heading"
      >
        <h2
          id="create-member-heading"
          className="text-lg font-semibold text-gray-900"
        >
          Create member
        </h2>
        <form
          className="mt-4 grid gap-4 sm:grid-cols-3"
          onSubmit={handleCreate}
          noValidate
        >
          <div>
            <label
              htmlFor="member_number"
              className="block text-sm font-medium text-gray-700"
            >
              Member number <span className="text-red-600">*</span>
            </label>
            <input
              id="member_number"
              name="member_number"
              type="text"
              required
              maxLength={64}
              autoComplete="off"
              value={form.member_number}
              onChange={(ev) =>
                setForm((f) => ({ ...f, member_number: ev.target.value }))
              }
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              disabled={submitting}
            />
          </div>
          <div>
            <label
              htmlFor="first_name"
              className="block text-sm font-medium text-gray-700"
            >
              First name <span className="text-red-600">*</span>
            </label>
            <input
              id="first_name"
              name="first_name"
              type="text"
              required
              maxLength={128}
              autoComplete="given-name"
              value={form.first_name}
              onChange={(ev) =>
                setForm((f) => ({ ...f, first_name: ev.target.value }))
              }
              className="mt-1 w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
              disabled={submitting}
            />
          </div>
          <div>
            <label
              htmlFor="last_name"
              className="block text-sm font-medium text-gray-700"
            >
              Last name <span className="text-red-600">*</span>
            </label>
            <input
              id="last_name"
              name="last_name"
              type="text"
              required
              maxLength={128}
              autoComplete="family-name"
              value={form.last_name}
              onChange={(ev) =>
                setForm((f) => ({ ...f, last_name: ev.target.value }))
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
              {submitting ? 'Creating…' : 'Create member'}
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
                <th className="px-4 py-3 font-medium text-gray-700">Number</th>
                <th className="px-4 py-3 font-medium text-gray-700">Name</th>
                <th className="px-4 py-3 font-medium text-gray-700">Email</th>
                <th className="px-4 py-3 font-medium text-gray-700">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {members.length === 0 ? (
                <tr>
                  <td
                    colSpan={4}
                    className="px-4 py-8 text-center text-gray-500"
                  >
                    No members found.
                  </td>
                </tr>
              ) : (
                members.map((m) => (
                  <tr key={m.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-mono text-xs text-gray-800">
                      {m.member_number}
                    </td>
                    <td className="px-4 py-3 text-gray-900">
                      {m.first_name} {m.last_name}
                    </td>
                    <td className="px-4 py-3 text-gray-600">{m.email ?? '—'}</td>
                    <td className="px-4 py-3">
                      <span className="inline-flex rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-800">
                        {m.status}
                      </span>
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
