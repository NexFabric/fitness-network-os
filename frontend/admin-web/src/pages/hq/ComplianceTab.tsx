import { StatusBadge } from '../../components/ui'
import { type ComplianceRecord, type TenantSummary } from './types'

type ComplianceTabProps = {
  tenants: TenantSummary[]
  compliance: ComplianceRecord[]
  onOpenAdd: () => void
}

export function ComplianceTab({ tenants, compliance, onOpenAdd }: ComplianceTabProps) {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-sm font-bold uppercase tracking-wide text-white">
            🛡️ Federasyon Muayene, Kalite ve Sertifikasyon Kayıtları
          </h2>
          <p className="mt-1 text-xs text-slate-400">
            TSE, ISO, Hijyen ve Antrenör Yeterlilik denetimlerinin resmi sicili.
          </p>
        </div>
        <button
          type="button"
          onClick={onOpenAdd}
          className="rounded-xl bg-teal-600 px-4 py-2 text-xs font-bold text-white hover:bg-teal-500 transition shadow-sm"
        >
          + Yeni Denetim Kaydı Ekle
        </button>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/90">
        <table className="min-w-full divide-y divide-slate-800 text-xs">
          <thead>
            <tr className="bg-slate-950/60 text-left text-slate-400 font-semibold">
              <th className="px-4 py-3.5">Kulüp</th>
              <th className="px-4 py-3.5">Sertifika / Standart</th>
              <th className="px-4 py-3.5">Sonuç Durumu</th>
              <th className="px-4 py-3.5">Denetim Tarihi</th>
              <th className="px-4 py-3.5">Denetçi Notları</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/80 text-slate-300">
            {compliance.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-8 text-center text-slate-500">
                  Henüz kayıtlı bir denetim veya sertifikasyon kaydı bulunmuyor.
                </td>
              </tr>
            ) : (
              compliance.map((c) => {
                const t = tenants.find((item) => item.id === c.tenant_id)
                return (
                  <tr key={c.id} className="hover:bg-slate-800/40 transition">
                    <td className="px-4 py-3.5 font-bold text-white">{t?.name ?? c.tenant_id.slice(0, 8)}</td>
                    <td className="px-4 py-3.5 font-semibold text-teal-300">{c.certification_name}</td>
                    <td className="px-4 py-3.5">
                      <StatusBadge status={c.status} />
                    </td>
                    <td className="px-4 py-3.5 text-slate-400">
                      {new Date(c.audit_date).toLocaleDateString('tr-TR')}
                    </td>
                    <td className="px-4 py-3.5 text-slate-400">{c.auditor_notes ?? '—'}</td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
