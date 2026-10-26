import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, getTenantId } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { RECEPTION_ROLES, ROLES } from '../auth/roles'
import { LoadingSkeleton, PageHeader } from '../components/ui'

type DashboardKPIs = {
  active_members_count: number
  expiring_memberships_count: number
  today_checkins_count: number
  past_due_invoices_count: number
  past_due_invoices_amount_minor: number
  month_collected_amount_minor: number
  total_outstanding_debt_minor: number
  finance_visible?: boolean
  currency: string
}

export default function Dashboard() {
  const tenantId = getTenantId()
  const { hasRole } = useAuth()
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null)
  const [loading, setLoading] = useState(true)
  const canReception = hasRole(RECEPTION_ROLES)
  const canFinance = hasRole([
    ROLES.GYM_OWNER,
    ROLES.GYM_ADMIN,
    ROLES.GYM_MANAGER,
    ROLES.ACCOUNTANT,
  ])
  const showFinance = (kpis?.finance_visible ?? true) && canFinance

  useEffect(() => {
    let cancelled = false

    async function loadKPIs() {
      try {
        const data = await api<DashboardKPIs>('/api/v1/dashboard/kpis')
        if (!cancelled) {
          setKpis(data)
        }
      } catch {
        // Handled silently
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void loadKPIs()
    return () => {
      cancelled = true
    }
  }, [])

  const formatMinor = (minor: number) =>
    (minor / 100).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' ₺'

  return (
    <div>
      <PageHeader
        title="Operasyonlar & Gösterge Paneli"
        subtitle="Kulüp operasyonel verileri, anlık turnike geçişleri ve finansal göstergeler."
      />

      {loading && (
        <div className="mt-6">
          <LoadingSkeleton rows={4} />
        </div>
      )}

      {!loading && kpis && (
        <>
          {/* Main Operational KPI Cards */}
          <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Link
              to="/members"
              className="card group transition-all duration-200 hover:-translate-y-0.5 hover:border-brand/40 hover:shadow-elevated focus-visible:ring-2 focus-visible:ring-brand"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">
                    Aktif Üyeler
                  </p>
                  <p className="mt-2 text-3xl font-bold tracking-tight text-ink tabular-nums">
                    {kpis.active_members_count}
                  </p>
                  <p className="mt-1 text-xs text-ink-muted">Sistemde kayıtlı aktif üye</p>
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
              <p className="mt-4 text-xs font-medium text-brand">Üyeleri görüntüle →</p>
            </Link>

            <Link
              to={canReception ? '/reception' : '/members'}
              className="card group transition-all duration-200 hover:-translate-y-0.5 hover:border-brand/40 hover:shadow-elevated focus-visible:ring-2 focus-visible:ring-brand"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">
                    Bugünkü Girişler
                  </p>
                  <p className="mt-2 text-3xl font-bold tracking-tight text-emerald-400 tabular-nums">
                    {kpis.today_checkins_count}
                  </p>
                  <p className="mt-1 text-xs text-ink-muted">Turnike & manuel geçiş</p>
                </div>
                <span
                  className="flex h-10 w-10 items-center justify-center rounded-control bg-emerald-900/30 text-emerald-400 transition group-hover:bg-brand group-hover:text-white"
                  aria-hidden="true"
                >
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </span>
              </div>
              <p className="mt-4 text-xs font-medium text-brand">Resepsiyona git →</p>
            </Link>

            <Link
              to="/members"
              className="card group transition-all duration-200 hover:-translate-y-0.5 hover:border-brand/40 hover:shadow-elevated focus-visible:ring-2 focus-visible:ring-brand"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">
                    Yenileme Bekleyen (30g)
                  </p>
                  <p className="mt-2 text-3xl font-bold tracking-tight text-amber-400 tabular-nums">
                    {kpis.expiring_memberships_count}
                  </p>
                  <p className="mt-1 text-xs text-ink-muted">Süresi dolmak üzere olan paket</p>
                </div>
                <span
                  className="flex h-10 w-10 items-center justify-center rounded-control bg-amber-900/30 text-amber-400 transition group-hover:bg-brand group-hover:text-white"
                  aria-hidden="true"
                >
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </span>
              </div>
              <p className="mt-4 text-xs font-medium text-brand">Abonelikleri incele →</p>
            </Link>

            {showFinance && (
            <Link
              to="/finance"
              className="card group transition-all duration-200 hover:-translate-y-0.5 hover:border-brand/40 hover:shadow-elevated focus-visible:ring-2 focus-visible:ring-brand"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-ink-muted">
                    Gecikmiş Ödemeler
                  </p>
                  <p className="mt-2 text-3xl font-bold tracking-tight text-rose-400 tabular-nums">
                    {kpis.past_due_invoices_count}
                  </p>
                  <p className="mt-1 text-xs text-rose-400 font-semibold">{formatMinor(kpis.past_due_invoices_amount_minor)}</p>
                </div>
                <span
                  className="flex h-10 w-10 items-center justify-center rounded-control bg-rose-900/30 text-rose-400 transition group-hover:bg-brand group-hover:text-white"
                  aria-hidden="true"
                >
                  <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
                  </svg>
                </span>
              </div>
              <p className="mt-4 text-xs font-medium text-brand">Gecikmeleri gör →</p>
            </Link>
            )}
          </div>

          {/* Financial Summary Strip */}
          {showFinance && (
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <div className="card border-slate-800 bg-slate-900/80 p-5">
              <span className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Bu Ay Tahsil Edilen</span>
              <div className="mt-2 text-2xl font-extrabold text-emerald-400">
                {formatMinor(kpis.month_collected_amount_minor)}
              </div>
              <p className="mt-1 text-xs text-slate-400">Ay başından itibaren tamamlanan başarılı tahsilatlar</p>
            </div>

            <div className="card border-slate-800 bg-slate-900/80 p-5">
              <span className="text-xs font-semibold uppercase tracking-wide text-ink-muted">Toplam Açık Alacak</span>
              <div className="mt-2 text-2xl font-extrabold text-amber-400">
                {formatMinor(kpis.total_outstanding_debt_minor)}
              </div>
              <p className="mt-1 text-xs text-slate-400">Açık ve kısmen ödenmiş faturaların kalan bakiye toplamı</p>
            </div>
          </div>
          )}
        </>
      )}

      {/* Quick Action Navigation */}
      <section className="card mt-6" aria-labelledby="quick-heading">
        <h2
          id="quick-heading"
          className="text-sm font-semibold uppercase tracking-wide text-ink-muted"
        >
          Hızlı Operasyon İşlemleri
        </h2>
        <div className="mt-4 flex flex-wrap gap-2.5">
          {canReception && (
            <Link to="/reception" className="btn-primary">
              Resepsiyon Masası
            </Link>
          )}
          <Link to="/members" className="btn-secondary">
            Üye Yönetimi
          </Link>
          <Link to="/locations" className="btn-secondary">
            Şubeler
          </Link>
          {canFinance && (
            <Link to="/finance" className="btn-secondary">
              Finans & Faturalar
            </Link>
          )}
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
