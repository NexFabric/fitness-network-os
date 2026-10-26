import { EmptyState } from '../../components/ui'
import { formatMinor, type MeInvoice, type MePayment } from './types'

type FinanceTabProps = {
  invoices: MeInvoice[]
  payments: MePayment[]
}

export function FinanceTab({ invoices, payments }: FinanceTabProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-400">Faturalar & Belgeler</h3>
        {invoices.length === 0 ? (
          <EmptyState title="Fatura bulunamadı" description="Kulüp abonelik faturalarınız burada listelenir." />
        ) : (
          <div className="space-y-2">
            {invoices.map((inv) => (
              <div
                key={inv.id}
                className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs"
              >
                <div>
                  <div className="font-semibold text-slate-200">{inv.invoice_number || 'Fatura Taslağı'}</div>
                  <div className="text-slate-400">{new Date(inv.created_at).toLocaleDateString('tr-TR')}</div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-white">{formatMinor(inv.total_amount_minor)}</div>
                  <span
                    className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
                      inv.status === 'PAID'
                        ? 'bg-emerald-500/10 text-emerald-400'
                        : inv.status === 'OPEN'
                          ? 'bg-amber-500/10 text-amber-400'
                          : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {inv.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-400">Ödeme İşlemleri</h3>
        {payments.length === 0 ? (
          <p className="text-xs text-slate-500">Kayıtlı ödeme hareketi bulunamadı.</p>
        ) : (
          <div className="space-y-2">
            {payments.map((p) => (
              <div
                key={p.id}
                className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs"
              >
                <div>
                  <div className="font-semibold text-slate-200">{p.method}</div>
                  <div className="text-slate-400">{new Date(p.created_at).toLocaleDateString('tr-TR')}</div>
                </div>
                <div className="text-right">
                  <div className="font-bold text-emerald-400">{formatMinor(p.amount_minor)}</div>
                  <span className="text-[10px] text-slate-400">{p.status}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
