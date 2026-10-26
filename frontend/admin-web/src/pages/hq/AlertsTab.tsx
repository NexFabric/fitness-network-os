import { EmptyState } from '../../components/ui'
import { type NetworkAlert, type TenantSummary } from './types'

type AlertsTabProps = {
  tenants: TenantSummary[]
  alerts: NetworkAlert[]
  onOpenCreate: () => void
  onDelete: (id: string) => void
}

export function AlertsTab({ tenants, alerts, onOpenCreate, onDelete }: AlertsTabProps) {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wide text-white">
            📢 Federasyon ve Ağ Düzeyinde Duyuru Yayını
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            Tüm kulüplere veya seçili bir kulübün yönetim paneline resmi duyuru ve uyarılar yayınlayın.
          </p>
        </div>
        <button
          type="button"
          onClick={onOpenCreate}
          className="rounded-xl bg-teal-600 px-4 py-2 text-xs font-bold text-white hover:bg-teal-500 transition shadow-sm"
        >
          + Yeni Duyuru Yayınla
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {alerts.length === 0 ? (
          <div className="col-span-2">
            <EmptyState title="Aktif duyuru yok" description="Ağ genelinde yayınlanmış bir duyuru bulunmuyor." />
          </div>
        ) : (
          alerts.map((a) => {
            const t = tenants.find((item) => item.id === a.target_tenant_id)
            const border =
              a.severity === 'CRITICAL'
                ? 'border-rose-800/80 bg-rose-950/30'
                : a.severity === 'WARNING'
                  ? 'border-amber-800/80 bg-amber-950/30'
                  : a.severity === 'MAINTENANCE'
                    ? 'border-purple-800/80 bg-purple-950/30'
                    : 'border-teal-800/80 bg-teal-950/30'
            return (
              <div key={a.id} className={`rounded-2xl border p-5 ${border} flex flex-col justify-between`}>
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[10px] font-extrabold uppercase tracking-wider rounded-md bg-slate-900 px-2 py-0.5 text-white">
                      {a.severity}
                    </span>
                    <span className="text-[11px] text-slate-400">
                      {new Date(a.created_at).toLocaleString('tr-TR')}
                    </span>
                  </div>
                  <h3 className="mt-3 text-sm font-bold text-white">{a.title}</h3>
                  <p className="mt-2 text-xs leading-relaxed text-slate-300">{a.message}</p>
                </div>
                <div className="mt-4 flex items-center justify-between border-t border-slate-800/80 pt-3 text-[11px]">
                  <span className="text-slate-400">
                    Hedef: <strong className="text-slate-200">{t ? t.name : 'Tüm Federasyon Kulüpleri'}</strong>
                  </span>
                  <button
                    type="button"
                    onClick={() => void onDelete(a.id)}
                    className="text-rose-400 hover:underline font-semibold"
                  >
                    Yayından Kaldır
                  </button>
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
