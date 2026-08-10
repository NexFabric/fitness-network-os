import { useCallback, useEffect, useState } from 'react'
import { api, ApiError } from '../api/client'

type Invoice = {
  id: string
  invoice_number: string
  status: string
  total_amount_minor: number
  currency: string
  due_date: string | null
  paid_at: string | null
  created_at: string
}

type Payment = {
  id: string
  amount_minor: number
  currency: string
  status: string
  payment_method: string | null
  transaction_id: string | null
  created_at: string
}

function formatCurrency(amount_minor: number, currency: string) {
  return new Intl.NumberFormat('tr-TR', {
    style: 'currency',
    currency: currency,
  }).format(amount_minor / 100)
}

function formatApiError(e: unknown, fallback: string): string {
  if (e instanceof ApiError) return `${e.status}: ${e.message}`
  if (e instanceof Error) return e.message
  return fallback
}

function invoiceStatusBadge(status: string) {
  switch (status.toLowerCase()) {
    case 'paid':
      return 'bg-emerald-500/10 text-emerald-400 ring-1 ring-inset ring-emerald-500/20'
    case 'pending':
    case 'open':
      return 'bg-amber-500/10 text-amber-400 ring-1 ring-inset ring-amber-500/20'
    case 'overdue':
      return 'bg-rose-500/10 text-rose-400 ring-1 ring-inset ring-rose-500/20'
    case 'void':
      return 'bg-slate-800 text-slate-400 ring-1 ring-inset ring-slate-700'
    default:
      return 'bg-slate-800 text-slate-400 ring-1 ring-inset ring-slate-700'
  }
}

function paymentStatusBadge(status: string) {
  switch (status.toLowerCase()) {
    case 'succeeded':
    case 'completed':
      return 'bg-emerald-500/10 text-emerald-400 ring-1 ring-inset ring-emerald-500/20'
    case 'pending':
      return 'bg-amber-500/10 text-amber-400 ring-1 ring-inset ring-amber-500/20'
    case 'failed':
      return 'bg-rose-500/10 text-rose-400 ring-1 ring-inset ring-rose-500/20'
    default:
      return 'bg-slate-800 text-slate-400 ring-1 ring-inset ring-slate-700'
  }
}

export default function Finance() {
  const [invoices, setInvoices] = useState<Invoice[]>([])
  const [payments, setPayments] = useState<Payment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [invData, payData] = await Promise.all([
        api<Invoice[]>('/api/v1/finance/invoices?limit=50'),
        api<Payment[]>('/api/v1/finance/payments?limit=50'),
      ])
      setInvoices(invData)
      setPayments(payData)
    } catch (e) {
      setError(formatApiError(e, 'Finans verileri yüklenemedi'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadData()
  }, [loadData])

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Finans</h1>
          <p className="page-subtitle">
            Faturalar ve ödeme işlemleri (Day-1 Operations)
          </p>
        </div>
        <button onClick={loadData} className="btn-secondary" disabled={loading}>
          {loading ? 'Yenileniyor...' : 'Yenile'}
        </button>
      </div>

      {error && (
        <div
          className="mt-6 rounded-control border border-rose-800/80 bg-rose-950/50 px-4 py-3 text-sm text-rose-300"
          role="alert"
        >
          {error}
        </div>
      )}

      {loading && invoices.length === 0 && (
        <p className="mt-6 text-sm text-slate-400" role="status">
          Finans verileri yükleniyor…
        </p>
      )}

      {!loading && !error && (
        <div className="mt-8 space-y-12">
          {/* Fatura Listesi */}
          <section>
            <h2 className="text-lg font-semibold text-slate-100 mb-4">Son Faturalar</h2>
            <div className="table-shell">
              <table className="min-w-full divide-y divide-slate-800 text-left">
                <thead className="bg-slate-900/80 backdrop-blur-md">
                  <tr>
                    <th className="table-th">Fatura No</th>
                    <th className="table-th">Tutar</th>
                    <th className="table-th">Son Ödeme</th>
                    <th className="table-th">Durum</th>
                    <th className="table-th">Tarih</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {invoices.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-sm text-slate-500">
                        Henüz fatura kaydı bulunmuyor.
                      </td>
                    </tr>
                  ) : (
                    invoices.map((inv) => (
                      <tr key={inv.id} className="transition-colors hover:bg-slate-800/50">
                        <td className="table-td font-mono text-xs text-slate-400">
                          {inv.invoice_number}
                        </td>
                        <td className="table-td font-medium text-slate-200">
                          {formatCurrency(inv.total_amount_minor, inv.currency)}
                        </td>
                        <td className="table-td text-slate-400">
                          {inv.due_date ? new Date(inv.due_date).toLocaleDateString('tr-TR') : '—'}
                        </td>
                        <td className="table-td">
                          <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${invoiceStatusBadge(inv.status)}`}>
                            {inv.status}
                          </span>
                        </td>
                        <td className="table-td text-slate-400 text-xs text-right">
                          {new Date(inv.created_at).toLocaleDateString('tr-TR')}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>

          {/* Ödeme Listesi */}
          <section>
            <h2 className="text-lg font-semibold text-slate-100 mb-4">Son Ödemeler</h2>
            <div className="table-shell">
              <table className="min-w-full divide-y divide-slate-800 text-left">
                <thead className="bg-slate-900/80 backdrop-blur-md">
                  <tr>
                    <th className="table-th">Ödeme Yöntemi</th>
                    <th className="table-th">İşlem ID</th>
                    <th className="table-th">Tutar</th>
                    <th className="table-th">Durum</th>
                    <th className="table-th">Tarih</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {payments.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-sm text-slate-500">
                        Henüz ödeme kaydı bulunmuyor.
                      </td>
                    </tr>
                  ) : (
                    payments.map((pay) => (
                      <tr key={pay.id} className="transition-colors hover:bg-slate-800/50">
                        <td className="table-td text-slate-300">
                          {pay.payment_method || 'Bilinmiyor'}
                        </td>
                        <td className="table-td font-mono text-xs text-slate-400">
                          {pay.transaction_id || '—'}
                        </td>
                        <td className="table-td font-medium text-slate-200">
                          {formatCurrency(pay.amount_minor, pay.currency)}
                        </td>
                        <td className="table-td">
                          <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${paymentStatusBadge(pay.status)}`}>
                            {pay.status}
                          </span>
                        </td>
                        <td className="table-td text-slate-400 text-xs text-right">
                          {new Date(pay.created_at).toLocaleString('tr-TR')}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </div>
      )}
    </div>
  )
}
