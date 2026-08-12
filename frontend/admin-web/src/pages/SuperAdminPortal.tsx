import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, setAuth } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Alert, EmptyState, LoadingSkeleton } from '../components/ui'

type TenantSummary = {
  id: string
  name: string
  location_code: string
  organization_id: string
  member_count: number
  active_membership_count: number
  revenue_minor: number
}

type FederationSummary = {
  organization_count: number
  tenant_count: number
  member_count: number
  active_membership_count: number
  revenue_minor: number
  partial: boolean
}

type AuditEvent = {
  id: string
  tenant_id: string
  user_id: string | null
  action: string
  resource_type: string
  created_at: string
}

/** amount_minor → display. Money never becomes a float on the way in. */
function formatMinor(minor: number): string {
  const major = Math.trunc(minor / 100)
  const cents = Math.abs(minor % 100)
    .toString()
    .padStart(2, '0')
  return `₺${major.toLocaleString('tr-TR')},${cents}`
}

/**
 * Federation console.
 *
 * Every figure comes from /api/v1/admin/* — there are no placeholder KPIs here.
 * The backend computes cross-tenant aggregates one tenant at a time (ADR-031),
 * so `partial` is surfaced rather than hidden: a page total must never be
 * presented as a platform total.
 */
export default function SuperAdminPortal() {
  const { session, refresh } = useAuth()

  const [tenants, setTenants] = useState<TenantSummary[]>([])
  const [summary, setSummary] = useState<FederationSummary | null>(null)
  const [audit, setAudit] = useState<AuditEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [switching, setSwitching] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [tenantRows, summaryRow, auditRows] = await Promise.all([
        api<TenantSummary[]>('/api/v1/admin/tenants?limit=25'),
        api<FederationSummary>('/api/v1/admin/federation/summary'),
        api<AuditEvent[]>('/api/v1/admin/audit?tenant_limit=10&limit_per_tenant=5'),
      ])
      setTenants(tenantRows)
      setSummary(summaryRow)
      setAudit(auditRows)
    } catch {
      setError('Federasyon verileri yüklenemedi. Birkaç saniye sonra tekrar deneyin.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  /** Switch the ops console into a tenant. Audited server-side (deps.py). */
  async function enterTenant(tenantId: string) {
    setSwitching(tenantId)
    setAuth(tenantId)
    await refresh()
    window.location.assign('/')
  }

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-8 text-slate-100 font-sans">
      <div className="mx-auto w-full max-w-6xl">
        <header className="mb-8 flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-white">
              Federasyon Konsolu
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              {session?.email}
              {session?.is_superuser && ' · platform yöneticisi'}
            </p>
          </div>
          <Link
            to="/portal"
            className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-800"
          >
            Portallara dön
          </Link>
        </header>

        {loading && <LoadingSkeleton rows={6} />}

        {!loading && error && (
          <div className="space-y-3">
            <Alert variant="error">{error}</Alert>
            <button
              type="button"
              onClick={() => void load()}
              className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-bold text-white hover:bg-slate-700"
            >
              Tekrar dene
            </button>
          </div>
        )}

        {!loading && !error && summary && (
          <>
            <section
              aria-label="Federasyon özeti"
              className="mb-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
            >
              {[
                { label: 'Organizasyon', value: summary.organization_count },
                { label: 'Kulüp (tenant)', value: summary.tenant_count },
                { label: 'Toplam üye', value: summary.member_count },
                {
                  label: 'Aktif abonelik',
                  value: summary.active_membership_count,
                },
              ].map((kpi) => (
                <div
                  key={kpi.label}
                  className="rounded-2xl border border-slate-800 bg-slate-900 p-5"
                >
                  <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                    {kpi.label}
                  </div>
                  <div className="mt-2 text-3xl font-extrabold text-white">
                    {kpi.value.toLocaleString('tr-TR')}
                  </div>
                </div>
              ))}
            </section>

            <section className="mb-6 rounded-2xl border border-slate-800 bg-slate-900 p-5">
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Tahsil edilen toplam
              </div>
              <div className="mt-2 text-3xl font-extrabold text-emerald-400">
                {formatMinor(summary.revenue_minor)}
              </div>
            </section>

            {summary.partial && (
              <div className="mb-6">
                <Alert variant="info">
                  Bu rakamlar yalnızca listelenen ilk {summary.tenant_count}{' '}
                  kulübü kapsıyor; platform geneli toplam değildir.
                </Alert>
              </div>
            )}

            <section
              aria-label="Kulüpler"
              className="mb-6 rounded-2xl border border-slate-800 bg-slate-900 p-5"
            >
              <h2 className="mb-4 text-lg font-bold text-white">Kulüpler</h2>
              {tenants.length === 0 ? (
                <EmptyState
                  title="Görüntülenecek kulüp yok"
                  description="Yetkiniz olan organizasyonlarda henüz kulüp tanımlı değil."
                />
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-500">
                      <tr>
                        <th className="pb-3 font-semibold">Kulüp</th>
                        <th className="pb-3 font-semibold">Kod</th>
                        <th className="pb-3 text-right font-semibold">Üye</th>
                        <th className="pb-3 text-right font-semibold">
                          Aktif abonelik
                        </th>
                        <th className="pb-3 text-right font-semibold">Gelir</th>
                        <th className="pb-3" />
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {tenants.map((tenant) => (
                        <tr key={tenant.id} className="text-slate-300">
                          <td className="py-3 font-semibold text-white">
                            {tenant.name}
                          </td>
                          <td className="py-3 font-mono text-xs text-slate-500">
                            {tenant.location_code}
                          </td>
                          <td className="py-3 text-right">
                            {tenant.member_count.toLocaleString('tr-TR')}
                          </td>
                          <td className="py-3 text-right">
                            {tenant.active_membership_count.toLocaleString(
                              'tr-TR',
                            )}
                          </td>
                          <td className="py-3 text-right font-semibold text-emerald-400">
                            {formatMinor(tenant.revenue_minor)}
                          </td>
                          <td className="py-3 text-right">
                            <button
                              type="button"
                              onClick={() => void enterTenant(tenant.id)}
                              disabled={switching !== null}
                              className="rounded-lg border border-slate-700 px-3 py-1.5 text-xs font-bold text-slate-200 hover:bg-slate-800 disabled:opacity-50"
                            >
                              {switching === tenant.id
                                ? 'Geçiliyor…'
                                : 'Bu kulübe geç'}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  <p className="mt-4 text-xs text-slate-500">
                    “Bu kulübe geç” operasyon konsolunu seçilen kulübe bağlar.
                    Bu erişim sunucu tarafında audit kaydına yazılır.
                  </p>
                </div>
              )}
            </section>

            <section
              aria-label="Audit kayıtları"
              className="rounded-2xl border border-slate-800 bg-slate-900 p-5"
            >
              <h2 className="mb-4 text-lg font-bold text-white">
                Son sistem olayları
              </h2>
              {audit.length === 0 ? (
                <EmptyState
                  title="Audit kaydı yok"
                  description="Kayda değer bir sistem olayı henüz oluşmadı."
                />
              ) : (
                <ul className="divide-y divide-slate-800/60 text-sm">
                  {audit.map((event) => (
                    <li
                      key={event.id}
                      className="flex flex-wrap items-center justify-between gap-2 py-2.5"
                    >
                      <span className="font-mono text-xs text-slate-300">
                        {event.action}
                      </span>
                      <span className="text-xs text-slate-500">
                        {event.resource_type} ·{' '}
                        {new Date(event.created_at).toLocaleString('tr-TR')}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </>
        )}
      </div>
    </div>
  )
}
