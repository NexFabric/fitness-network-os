import { useCallback, useEffect, useState } from 'react'
import { api, ApiError } from '../api/client'
import {
  Alert,
  LoadingSkeleton,
  PageHeader,
  StatusBadge,
} from '../components/ui'

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
      <PageHeader
        title="Finans"
        subtitle="Faturalar ve ödeme işlemleri"
        actions={
          <button
            type="button"
            onClick={() => void loadData()}
            className="btn-secondary"
            disabled={loading}
          >
            {loading ? 'Yenileniyor…' : 'Yenile'}
          </button>
        }
      />

      {error && (
        <div className="mt-6">
          <Alert onRetry={() => void loadData()}>{error}</Alert>
        </div>
      )}

      {loading && invoices.length === 0 && (
        <div className="table-shell mt-6">
          <LoadingSkeleton rows={5} />
        </div>
      )}

      {!loading && !error && (
        <div className="mt-8 space-y-10">
          <section>
            <h2 className="mb-4 text-lg font-semibold text-slate-100">
              Son faturalar
            </h2>
            <div className="table-shell">
              <table className="min-w-full divide-y divide-slate-800 text-left">
                <thead className="bg-slate-900/80 backdrop-blur-md">
                  <tr>
                    <th className="table-th">Fatura no</th>
                    <th className="table-th">Tutar</th>
                    <th className="table-th">Son ödeme</th>
                    <th className="table-th">Durum</th>
                    <th className="table-th">Tarih</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {invoices.length === 0 ? (
                    <tr>
                      <td
                        colSpan={5}
                        className="px-4 py-8 text-center text-sm text-ink-muted"
                      >
                        Henüz fatura kaydı bulunmuyor.
                      </td>
                    </tr>
                  ) : (
                    invoices.map((inv) => (
                      <tr
                        key={inv.id}
                        className="transition-colors hover:bg-slate-800/50"
                      >
                        <td className="table-td font-mono text-xs text-slate-400">
                          {inv.invoice_number}
                        </td>
                        <td className="table-td font-medium text-slate-200">
                          {formatCurrency(inv.total_amount_minor, inv.currency)}
                        </td>
                        <td className="table-td text-slate-400">
                          {inv.due_date
                            ? new Date(inv.due_date).toLocaleDateString('tr-TR')
                            : '—'}
                        </td>
                        <td className="table-td">
                          <StatusBadge status={inv.status} kind="invoice" />
                        </td>
                        <td className="table-td text-right text-xs text-slate-400">
                          {new Date(inv.created_at).toLocaleDateString('tr-TR')}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h2 className="mb-4 text-lg font-semibold text-slate-100">
              Son ödemeler
            </h2>
            <div className="table-shell">
              <table className="min-w-full divide-y divide-slate-800 text-left">
                <thead className="bg-slate-900/80 backdrop-blur-md">
                  <tr>
                    <th className="table-th">Ödeme yöntemi</th>
                    <th className="table-th">İşlem ID</th>
                    <th className="table-th">Tutar</th>
                    <th className="table-th">Durum</th>
                    <th className="table-th">Tarih</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {payments.length === 0 ? (
                    <tr>
                      <td
                        colSpan={5}
                        className="px-4 py-8 text-center text-sm text-ink-muted"
                      >
                        Henüz ödeme kaydı bulunmuyor.
                      </td>
                    </tr>
                  ) : (
                    payments.map((pay) => (
                      <tr
                        key={pay.id}
                        className="transition-colors hover:bg-slate-800/50"
                      >
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
                          <StatusBadge status={pay.status} kind="payment" />
                        </td>
                        <td className="table-td text-right text-xs text-slate-400">
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
