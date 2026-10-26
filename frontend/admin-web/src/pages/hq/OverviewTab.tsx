import { EmptyState, StatusBadge } from '../../components/ui'
import { formatMinor, type AuditEvent, type FederationSummary, type TenantSummary } from './types'

type OverviewTabProps = {
  summary: FederationSummary
  tenants: TenantSummary[]
  audit: AuditEvent[]
  switching: string | null
  onEnterTenant: (tenantId: string) => void
  onGoGyms: () => void
}

export function OverviewTab({
  summary,
  tenants,
  audit,
  switching,
  onEnterTenant,
  onGoGyms,
}: OverviewTabProps) {
  return (
    <div className="space-y-6">
      <section aria-label="Ağ Geneli KPI'lar" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-sm">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Toplam Kulüp (Tenant)
          </span>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-extrabold text-white">{summary.tenant_count}</span>
            <span className="text-xs text-emerald-400 font-semibold">({summary.active_tenant_count} Aktif)</span>
            {summary.suspended_tenant_count > 0 && (
              <span className="text-xs text-rose-400 font-semibold">({summary.suspended_tenant_count} Askıda)</span>
            )}
          </div>
          <p className="mt-1 text-[11px] text-slate-500">Federasyona bağlı lisanslı kulüpler</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-sm">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Ağ Geneli Toplam Üye
          </span>
          <div className="mt-2 text-3xl font-extrabold text-teal-400">
            {summary.member_count.toLocaleString('tr-TR')}
          </div>
          <p className="mt-1 text-[11px] text-slate-500">Kayıtlı tekil sporcu sayısı</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-sm">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Aktif Turnike Aboneliği
          </span>
          <div className="mt-2 text-3xl font-extrabold text-emerald-400">
            {summary.active_membership_count.toLocaleString('tr-TR')}
          </div>
          <p className="mt-1 text-[11px] text-slate-500">Geçiş yetkisi olan aktif paketler</p>
        </div>

        <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-sm">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Tahsil Edilen Ağ Cirosu
          </span>
          <div className="mt-2 text-3xl font-extrabold text-white">{formatMinor(summary.revenue_minor)}</div>
          <p className="mt-1 text-[11px] text-slate-500">Tüm kulüplerin konsolide tahsilatı</p>
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-wide text-white">
              🏢 Bağlı Kulüpler & Durumlar
            </h2>
            <button type="button" onClick={onGoGyms} className="text-xs text-teal-400 hover:underline">
              Tümünü Yönet ({tenants.length}) →
            </button>
          </div>
          <div className="divide-y divide-slate-800/80 text-xs">
            {tenants.slice(0, 5).map((t) => (
              <div key={t.id} className="flex items-center justify-between py-3">
                <div>
                  <span className="font-bold text-white">{t.name}</span>
                  <span className="ml-2 font-mono text-[11px] text-slate-500">[{t.location_code}]</span>
                  <div className="text-[11px] text-slate-400">
                    {t.member_count} üye · {t.active_membership_count} aktif abone · {formatMinor(t.revenue_minor)}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <StatusBadge status={t.status} />
                  <button
                    type="button"
                    onClick={() => void onEnterTenant(t.id)}
                    disabled={switching === t.id}
                    className="rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs font-medium text-slate-200 hover:bg-slate-700 transition"
                  >
                    {switching === t.id ? 'Bağlanıyor…' : 'Kulübe Geç'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5">
          <h2 className="mb-4 text-sm font-bold uppercase tracking-wide text-white">
            📜 Son Sistem ve Audit Kayıtları
          </h2>
          {audit.length === 0 ? (
            <EmptyState title="Audit kaydı yok" description="Henüz bir sistem olayı kaydedilmedi." />
          ) : (
            <ul className="divide-y divide-slate-800/80 text-xs">
              {audit.slice(0, 6).map((event) => (
                <li key={event.id} className="flex items-center justify-between py-2.5">
                  <span className="font-mono text-teal-400">{event.action}</span>
                  <span className="text-slate-500">
                    {event.resource_type} · {new Date(event.created_at).toLocaleString('tr-TR')}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  )
}
