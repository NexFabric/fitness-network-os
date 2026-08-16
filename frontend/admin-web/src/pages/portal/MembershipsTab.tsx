import { EmptyState } from '../../components/ui'
import { type EntitlementsSummary, type Membership } from './types'

type MembershipsTabProps = {
  memberships: Membership[]
  entitlements: EntitlementsSummary | null
}

export function MembershipsTab({ memberships, entitlements }: MembershipsTabProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-400">Abonelik Kayıtları</h3>
        {memberships.length === 0 ? (
          <EmptyState
            title="Kayıtlı abonelik bulunamadı"
            description="Aktif üyelik tanımlaması için kulüp yetkilisiyle görüşün."
          />
        ) : (
          <div className="space-y-2">
            {memberships.map((m) => (
              <div
                key={m.id}
                className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs"
              >
                <div>
                  <div className="font-semibold text-slate-200">
                    Başlangıç: {new Date(m.start_date).toLocaleDateString('tr-TR')}
                  </div>
                  <div className="text-slate-400">
                    Bitiş: {m.end_date ? new Date(m.end_date).toLocaleDateString('tr-TR') : 'Süresiz'}
                  </div>
                </div>
                <span
                  className={`rounded px-2 py-0.5 font-bold ${
                    m.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {m.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-400">
          Kullanım Hakları & Cüzdanlar
        </h3>
        {!entitlements || entitlements.wallets.length === 0 ? (
          <p className="text-xs text-slate-500">Tanımlı özel hak cüzdanı bulunmuyor.</p>
        ) : (
          <div className="space-y-2">
            {entitlements.wallets.map((w) => (
              <div key={w.wallet_id} className="rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs">
                <div className="mb-1 flex justify-between font-semibold">
                  <span className="text-slate-200">{w.entitlement_name || w.entitlement_code}</span>
                  <span className="text-cyan-400">
                    {w.remaining} / {w.allocated} Kalan
                  </span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
                  <div
                    className="h-full bg-cyan-500 rounded-full"
                    style={{ width: `${Math.min(100, (w.remaining / Math.max(1, w.allocated)) * 100)}%` }}
                  />
                </div>
                {w.expires_at && (
                  <div className="mt-1 text-[10px] text-slate-500">
                    Son Kullanım: {new Date(w.expires_at).toLocaleDateString('tr-TR')}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
