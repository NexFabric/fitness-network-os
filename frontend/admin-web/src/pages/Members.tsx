import { useEffect, useState } from 'react'
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

export default function Members() {
  const [members, setMembers] = useState<Member[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      setLoading(true)
      setError(null)
      try {
        const data = await api<Member[]>('/api/v1/members')
        if (!cancelled) setMembers(data)
      } catch (e) {
        if (!cancelled) {
          setError(
            e instanceof ApiError
              ? `${e.status}: ${e.message}`
              : e instanceof Error
                ? e.message
                : 'Failed to load members',
          )
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900">Members</h1>
      <p className="mt-1 text-sm text-gray-600">
        GET /api/v1/members (requires members:read)
      </p>

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
