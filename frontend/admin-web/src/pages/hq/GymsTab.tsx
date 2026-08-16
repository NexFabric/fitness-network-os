import { StatusBadge } from '../../components/ui'
import { formatMinor, type TenantSummary } from './types'

type GymsTabProps = {
  tenants: TenantSummary[]
  searchQuery: string
  statusFilter: 'ALL' | 'ACTIVE' | 'SUSPENDED'
  switching: string | null
  onSearchChange: (value: string) => void
  onStatusFilterChange: (value: 'ALL' | 'ACTIVE' | 'SUSPENDED') => void
  onOpenAddGym: () => void
  onEnterTenant: (tenantId: string) => void
  onOpenBreakGlass: (tenant: TenantSummary) => void
  onOpenSuspend: (tenant: TenantSummary) => void
  onReactivate: (tenant: TenantSummary) => void
}

export function GymsTab({
  tenants,
  searchQuery,
  statusFilter,
  switching,
  onSearchChange,
  onStatusFilterChange,
  onOpenAddGym,
  onEnterTenant,
  onOpenBreakGlass,
  onOpenSuspend,
  onReactivate,
}: GymsTabProps) {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="text"
            placeholder="Kulüp adı veya kod ile ara…"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-xs text-white placeholder-slate-500 focus:border-teal-500 focus:outline-none w-64"
          />
          <select
            value={statusFilter}
            onChange={(e) => onStatusFilterChange(e.target.value as 'ALL' | 'ACTIVE' | 'SUSPENDED')}
            className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-300 focus:border-teal-500 focus:outline-none"
          >
            <option value="ALL">Tüm Durumlar</option>
            <option value="ACTIVE">Yalnızca Aktif</option>
            <option value="SUSPENDED">Yalnızca Askıda</option>
          </select>
        </div>
        <button
          type="button"
          onClick={onOpenAddGym}
          className="rounded-xl bg-teal-600 px-4 py-2 text-xs font-bold text-white hover:bg-teal-500 transition shadow-sm"
        >
          + Yeni Kulüp Aç
        </button>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/90">
        <table className="min-w-full divide-y divide-slate-800 text-xs">
          <thead>
            <tr className="bg-slate-950/60 text-left text-slate-400 font-semibold">
              <th className="px-4 py-3.5">Kulüp & Kod</th>
              <th className="px-4 py-3.5">Durum</th>
              <th className="px-4 py-3.5">Toplam Üye</th>
              <th className="px-4 py-3.5">Aktif Abonelik</th>
              <th className="px-4 py-3.5">Toplam Ciro</th>
              <th className="px-4 py-3.5 text-right">Aksiyonlar</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80 text-slate-300">
            {tenants.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-500">
                  Arama kriterine uygun kulüp bulunamadı.
                </td>
              </tr>
            ) : (
              tenants.map((t) => (
                <tr key={t.id} className="hover:bg-slate-800/40 transition">
                  <td className="px-4 py-3.5">
                    <div className="font-bold text-white">{t.name}</div>
                    <div className="font-mono text-[11px] text-slate-500">{t.location_code}</div>
                    {t.suspension_reason && (
                      <div className="mt-1 text-[10px] text-rose-400">Gerekçe: {t.suspension_reason}</div>
                    )}
                  </td>
                  <td className="px-4 py-3.5">
                    <StatusBadge status={t.status} />
                  </td>
                  <td className="px-4 py-3.5 font-medium">{t.member_count}</td>
                  <td className="px-4 py-3.5 font-medium text-emerald-400">{t.active_membership_count}</td>
                  <td className="px-4 py-3.5 font-bold text-white">{formatMinor(t.revenue_minor)}</td>
                  <td className="px-4 py-3.5 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        type="button"
                        onClick={() => void onEnterTenant(t.id)}
                        disabled={switching === t.id}
                        className="rounded-lg bg-teal-600/20 border border-teal-500/30 px-3 py-1 text-xs font-bold text-teal-300 hover:bg-teal-600/30 transition"
                      >
                        {switching === t.id ? 'Bağlanıyor…' : 'Kulübe Geç'}
                      </button>
                      <button
                        type="button"
                        onClick={() => onOpenBreakGlass(t)}
                        className="rounded-lg bg-purple-950/60 border border-purple-800/80 px-2.5 py-1 text-xs font-medium text-purple-300 hover:bg-purple-900/60 transition"
                        title="Denetimli Acil Destek Girişi"
                      >
                        Break-Glass
                      </button>
                      {t.status === 'ACTIVE' ? (
                        <button
                          type="button"
                          onClick={() => onOpenSuspend(t)}
                          className="rounded-lg bg-rose-950/60 border border-rose-800/80 px-2.5 py-1 text-xs font-medium text-rose-300 hover:bg-rose-900/60 transition"
                        >
                          Askıya Al
                        </button>
                      ) : (
                        <button
                          type="button"
                          onClick={() => void onReactivate(t)}
                          className="rounded-lg bg-emerald-950/60 border border-emerald-800/80 px-2.5 py-1 text-xs font-medium text-emerald-300 hover:bg-emerald-900/60 transition"
                        >
                          Yeniden Aç
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
