import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, getTenantId } from '../api/client'
import { PageHeader } from '../components/ui'

type CountState = number | null

export default function Dashboard() {
  const tenantId = getTenantId()
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
      <PageHeader
        title="Operasyonlar"
        subtitle="Tekrar hoş geldiniz. Bu salona ait üyeleri, şubeleri ve finansı yönetin."
      />

      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Link
          to="/members"
          className="card group transition-all duration-200 hover:-translate-y-0.5 hover:border-brand/40 hover:shadow-elevated focus-visible:ring-2 focus-visible:ring-brand"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">
                Üyeler
              </p>
              <p className="mt-2 text-3xl font-bold tracking-tight text-ink tabular-nums">
                {formatCount(memberCount)}
              </p>
              <p className="mt-1 text-sm text-ink-muted">Aktif üye listesi</p>
            </div>
            <span
              className="flex h-10 w-10 items-center justify-center rounded-control bg-teal-900/30 text-teal-400 transition group-hover:bg-brand group-hover:text-white"
              aria-hidden="true"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0z" />
              </svg>
            </span>
          </div>
          <p className="mt-4 text-sm font-medium text-brand">Üyeleri görüntüle →</p>
        </Link>

        <Link
          to="/locations"
          className="card group transition-all duration-200 hover:-translate-y-0.5 hover:border-brand/40 hover:shadow-elevated focus-visible:ring-2 focus-visible:ring-brand"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">
                Şubeler
              </p>
              <p className="mt-2 text-3xl font-bold tracking-tight text-ink tabular-nums">
                {formatCount(locationCount)}
              </p>
              <p className="mt-1 text-sm text-ink-muted">Bağlı lokasyonlar</p>
            </div>
            <span
              className="flex h-10 w-10 items-center justify-center rounded-control bg-teal-900/30 text-teal-400 transition group-hover:bg-brand group-hover:text-white"
              aria-hidden="true"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
              </svg>
            </span>
          </div>
          <p className="mt-4 text-sm font-medium text-brand">Şubeleri görüntüle →</p>
        </Link>

        <Link
          to="/finance"
          className="card group transition-all duration-200 hover:-translate-y-0.5 hover:border-brand/40 hover:shadow-elevated focus-visible:ring-2 focus-visible:ring-brand sm:col-span-2 lg:col-span-1"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">
                Finans
              </p>
              <p className="mt-2 text-3xl font-bold tracking-tight text-ink">
                Faturalar
              </p>
              <p className="mt-1 text-sm text-ink-muted">Ödemeler ve mutabakat</p>
            </div>
            <span
              className="flex h-10 w-10 items-center justify-center rounded-control bg-teal-900/30 text-teal-400 transition group-hover:bg-brand group-hover:text-white"
              aria-hidden="true"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </span>
          </div>
          <p className="mt-4 text-sm font-medium text-brand">Finansa git →</p>
        </Link>
      </div>

      <section className="card mt-6" aria-labelledby="quick-heading">
        <h2
          id="quick-heading"
          className="text-sm font-semibold uppercase tracking-wide text-ink-muted"
        >
          Hızlı işlemler
        </h2>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link to="/members" className="btn-secondary">
            Üye ekle
          </Link>
          <Link to="/locations" className="btn-secondary">
            Şube ekle
          </Link>
          <Link to="/finance" className="btn-secondary">
            Faturaları gör
          </Link>
        </div>
        {tenantId && (
          <p className="mt-4 text-xs text-ink-muted">
            Oturum kiracısı:{' '}
            <span className="font-mono text-slate-400" title={tenantId}>
              {tenantId.slice(0, 8)}…
            </span>
          </p>
        )}
      </section>
    </div>
  )
}
