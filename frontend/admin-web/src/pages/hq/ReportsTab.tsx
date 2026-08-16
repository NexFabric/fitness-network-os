import { formatMinor, type AnalyticsOverview, type TenantSummary } from './types'

type ReportsTabProps = {
  tenants: TenantSummary[]
  analytics: AnalyticsOverview | null
  onExportCsv: () => void
}

export function ReportsTab({ tenants, analytics, onExportCsv }: ReportsTabProps) {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wide text-white">
            📈 Konsolide Ağ Analitiği & Finansal Raporlar
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            Tüm kulüplerin toplam ciro, turnike geçiş ve büyüme verileri.
          </p>
        </div>
        <button
          type="button"
          onClick={onExportCsv}
          className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-xs font-bold text-teal-400 hover:bg-slate-800 transition"
        >
          📥 Konsolide Ağ Verisini İndir (.csv)
        </button>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Konsolide Ciro</span>
          <div className="mt-2 text-2xl font-extrabold text-white">
            {analytics ? formatMinor(analytics.total_revenue_minor) : '—'}
          </div>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Toplam Turnike Geçişi
          </span>
          <div className="mt-2 text-2xl font-extrabold text-teal-400">
            {analytics ? analytics.total_checkins.toLocaleString('tr-TR') : '—'}
          </div>
        </div>
        <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            Kulüp Başına Ortalama Ciro
          </span>
          <div className="mt-2 text-2xl font-extrabold text-emerald-400">
            {analytics && tenants.length > 0
              ? formatMinor(Math.trunc(analytics.total_revenue_minor / tenants.length))
              : '—'}
          </div>
        </div>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/90">
        <table className="min-w-full divide-y divide-slate-800 text-xs">
          <thead>
            <tr className="bg-slate-950/60 text-left text-slate-400 font-semibold">
              <th className="px-4 py-3.5">Kulüp</th>
              <th className="px-4 py-3.5">Turnike Geçiş Adedi</th>
              <th className="px-4 py-3.5">Tahsil Edilen Ciro</th>
              <th className="px-4 py-3.5">Ağ Cirosundaki Payı</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80 text-slate-300">
            {tenants.map((t) => {
              const clubRev = analytics?.revenue_by_tenant_minor[t.id] ?? t.revenue_minor
              const totalRev = analytics?.total_revenue_minor ?? 1
              const share = totalRev > 0 ? ((clubRev / totalRev) * 100).toFixed(1) : '0'
              const checkins = analytics?.checkins_by_tenant[t.id] ?? 0
              return (
                <tr key={t.id} className="hover:bg-slate-800/40 transition">
                  <td className="px-4 py-3.5 font-bold text-white">{t.name}</td>
                  <td className="px-4 py-3.5 font-medium text-teal-300">{checkins} geçiş</td>
                  <td className="px-4 py-3.5 font-bold text-white">{formatMinor(clubRev)}</td>
                  <td className="px-4 py-3.5">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 w-24 rounded-full bg-slate-800 overflow-hidden">
                        <div
                          className="h-full bg-teal-400 rounded-full"
                          style={{ width: `${Math.min(100, Number(share))}%` }}
                        />
                      </div>
                      <span className="text-[11px] text-slate-400">%{share}</span>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
