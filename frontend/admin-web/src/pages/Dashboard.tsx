import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, getBaseUrl, getTenantId } from '../api/client'

type CountState = number | null

export default function Dashboard() {
  const tenantId = getTenantId()
  const apiUrl = getBaseUrl()
  const [memberCount, setMemberCount] = useState<CountState>(null)
  const [locationCount, setLocationCount] = useState<CountState>(null)
  const [countsReady, setCountsReady] = useState(false)

  useEffect(() => {
    let cancelled = false

    async function loadCounts() {
      const [membersResult, locationsResult] = await Promise.allSettled([
        api<unknown[]>('/api/v1/members'),
        api<unknown[]>('/api/v1/locations'),
      ])

      if (cancelled) return

      if (membersResult.status === 'fulfilled' && Array.isArray(membersResult.value)) {
        setMemberCount(membersResult.value.length)
      }
      if (
        locationsResult.status === 'fulfilled' &&
        Array.isArray(locationsResult.value)
      ) {
        setLocationCount(locationsResult.value.length)
      }
      setCountsReady(true)
    }

    void loadCounts()
    return () => {
      cancelled = true
    }
  }, [])

  function formatCount(n: CountState): string {
    if (!countsReady) return '…'
    if (n === null) return '—'
    return String(n)
  }

  return (
    <div>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="page-title">Operations</h1>
          <p className="page-subtitle">
            Welcome back. Manage members and branch locations for this gym.
          </p>
        </div>
      </div>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <Link
          to="/members"
          className="card group transition hover:border-brand/40 hover:shadow-elevated focus-visible:ring-2 focus-visible:ring-brand"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Members
              </p>
              <p className="mt-2 text-3xl font-bold tracking-tight text-ink tabular-nums">
                {formatCount(memberCount)}
              </p>
              <p className="mt-1 text-sm text-slate-600">
                Active roster for this tenant
              </p>
            </div>
            <span
              className="flex h-10 w-10 items-center justify-center rounded-control bg-teal-50 text-brand transition group-hover:bg-brand group-hover:text-white"
              aria-hidden="true"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.75}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"
                />
              </svg>
            </span>
          </div>
          <p className="mt-4 text-sm font-medium text-brand">
            Open members →
          </p>
        </Link>

        <Link
          to="/locations"
          className="card group transition hover:border-brand/40 hover:shadow-elevated focus-visible:ring-2 focus-visible:ring-brand"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Locations
              </p>
              <p className="mt-2 text-3xl font-bold tracking-tight text-ink tabular-nums">
                {formatCount(locationCount)}
              </p>
              <p className="mt-1 text-sm text-slate-600">
                Branches under this gym
              </p>
            </div>
            <span
              className="flex h-10 w-10 items-center justify-center rounded-control bg-teal-50 text-brand transition group-hover:bg-brand group-hover:text-white"
              aria-hidden="true"
            >
              <svg
                className="h-5 w-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.75}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z"
                />
              </svg>
            </span>
          </div>
          <p className="mt-4 text-sm font-medium text-brand">
            Open locations →
          </p>
        </Link>
      </div>

      <section className="card mt-6" aria-labelledby="session-heading">
        <h2
          id="session-heading"
          className="text-sm font-semibold uppercase tracking-wide text-slate-500"
        >
          Session
        </h2>
        <dl className="mt-3 grid gap-3 sm:grid-cols-2">
          <div>
            <dt className="text-xs font-medium text-slate-500">API base</dt>
            <dd className="mt-0.5 font-mono text-sm text-ink break-all">
              {apiUrl}
            </dd>
          </div>
          <div>
            <dt className="text-xs font-medium text-slate-500">Tenant</dt>
            <dd className="mt-0.5 font-mono text-sm text-ink break-all">
              {tenantId ?? '—'}
            </dd>
          </div>
        </dl>
      </section>
    </div>
  )
}
