import { formatMinor, type PassportConfig, type TenantSummary } from './types'

type PassportTabProps = {
  tenants: TenantSummary[]
  passports: PassportConfig[]
  onEdit: (tenant: TenantSummary, passport: PassportConfig | undefined) => void
}

export function PassportTab({ tenants, passports, onEdit }: PassportTabProps) {
  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-sm font-bold uppercase tracking-wide text-white">
              🛂 Federasyon Pasaportu ve Dolaşım Matrisi
            </h2>
            <p className="mt-1 text-xs text-slate-400">
              Sporcuların kendi kayıtlı kulüpleri dışındaki federasyon salonlarına misafir olarak girebilme
              kuralları ve mahsuplaşma ayarları.
            </p>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/90">
        <table className="min-w-full divide-y divide-slate-800 text-xs">
          <thead>
            <tr className="bg-slate-950/60 text-left text-slate-400 font-semibold">
              <th className="px-4 py-3.5">Kulüp Adı</th>
              <th className="px-4 py-3.5">Pasaport Durumu</th>
              <th className="px-4 py-3.5">Kabul Edilen Paket Seviyeleri</th>
              <th className="px-4 py-3.5">Aylık Misafir Giriş Limiti</th>
              <th className="px-4 py-3.5">Ziyaret Başı Mahsuplaşma</th>
              <th className="px-4 py-3.5 text-right">Aksiyon</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80 text-slate-300">
            {tenants.map((t) => {
              const p = passports.find((cfg) => cfg.tenant_id === t.id)
              return (
                <tr key={t.id} className="hover:bg-slate-800/40 transition">
                  <td className="px-4 py-3.5 font-bold text-white">{t.name}</td>
                  <td className="px-4 py-3.5">
                    {p?.is_active ? (
                      <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
                        Dolaşıma Açık
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full bg-slate-800 px-2 py-0.5 text-xs font-semibold text-slate-400">
                        Kapalı
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3.5 font-mono text-[11px] text-teal-300">
                    {p?.allowed_home_gym_tiers ?? 'VIP,GOLD'}
                  </td>
                  <td className="px-4 py-3.5 font-medium">
                    {p?.rules?.max_monthly_roaming_visits ?? 5} ziyaret / ay
                  </td>
                  <td className="px-4 py-3.5 font-medium text-amber-400">
                    {p?.rules?.guest_fee_minor ? formatMinor(p.rules.guest_fee_minor) : '₺0,00'}
                  </td>
                  <td className="px-4 py-3.5 text-right">
                    <button
                      type="button"
                      onClick={() => onEdit(t, p)}
                      className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1 text-xs font-medium text-slate-200 hover:bg-slate-700 transition"
                    >
                      Kuralları Düzenle
                    </button>
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
