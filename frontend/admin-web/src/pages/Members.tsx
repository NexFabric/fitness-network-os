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

function statusBadgeClass(status: string): string {
  const s = status.toLowerCase()
  if (s === 'active') {
    return 'bg-emerald-50 text-emerald-800 ring-1 ring-inset ring-emerald-200'
  }
  if (s === 'inactive' || s === 'cancelled' || s === 'canceled') {
    return 'bg-slate-100 text-slate-700 ring-1 ring-inset ring-slate-200'
  }
  if (s === 'suspended') {
    return 'bg-amber-50 text-amber-800 ring-1 ring-inset ring-amber-200'
  }
  return 'bg-slate-100 text-slate-700 ring-1 ring-inset ring-slate-200'
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
      <h1 className="page-title">Members</h1>
      <p className="page-subtitle">
        Roster for this gym — create and review members
      </p>

      <section className="card mt-6" aria-labelledby="create-member-heading">
        <div className="card-header">
          <h2
            id="create-member-heading"
            className="text-base font-semibold text-ink"
          >
            Create member
          </h2>
        </div>
        <form
          className="mt-4 grid gap-4 sm:grid-cols-3"
          onSubmit={handleCreate}
          noValidate
        >
          <div>
            <label htmlFor="member_number" className="label-text">
              Member number <span className="text-accent-danger">*</span>
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
              className="input-field"
              disabled={submitting}
            />
          </div>
          <div>
            <label htmlFor="first_name" className="label-text">
              First name <span className="text-accent-danger">*</span>
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
              className="input-field"
              disabled={submitting}
            />
          </div>
          <div>
            <label htmlFor="last_name" className="label-text">
              Last name <span className="text-accent-danger">*</span>
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
              className="input-field"
              disabled={submitting}
            />
          </div>
          <div className="flex flex-wrap items-center gap-3 sm:col-span-3">
            <button type="submit" disabled={submitting} className="btn-primary">
              {submitting ? 'Creating…' : 'Create member'}
            </button>
            {formError && (
              <p className="text-sm text-red-700" role="alert">
                {formError}
              </p>
            )}
            {formSuccess && (
              <p className="text-sm font-medium text-emerald-700" role="status">
                {formSuccess}
              </p>
            )}
          </div>
        </form>
      </section>

      {loading && (
        <p className="mt-6 text-sm text-slate-500" role="status">
          Loading members…
        </p>
      )}

      {error && (
        <div
          className="mt-6 rounded-control border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800"
          role="alert"
        >
          {error}
        </div>
      )}

      {!loading && !error && (
        <div className="table-shell mt-6">
          <table className="min-w-full divide-y divide-slate-100 text-left">
            <thead className="bg-surface/80">
              <tr>
                <th className="table-th">Number</th>
                <th className="table-th">Name</th>
                <th className="table-th">Email</th>
                <th className="table-th">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {members.length === 0 ? (
                <tr>
                  <td
                    colSpan={4}
                    className="px-4 py-12 text-center text-sm text-slate-500"
                  >
                    <p className="font-medium text-slate-700">No members yet</p>
                    <p className="mt-1">
                      Create the first member using the form above.
                    </p>
                  </td>
                </tr>
              ) : (
                members.map((m) => (
                  <tr key={m.id} className="hover:bg-surface/60">
                    <td className="table-td font-mono text-xs text-slate-700">
                      {m.member_number}
                    </td>
                    <td className="table-td font-medium">
                      {m.first_name} {m.last_name}
                    </td>
                    <td className="table-td text-slate-600">
                      {m.email ?? '—'}
                    </td>
                    <td className="table-td">
                      <span
                        className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${statusBadgeClass(m.status)}`}
                      >
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
