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
  billing_account_id: string
  invoice_number: string | null
  status: string
  total_amount_minor: number
  remaining_amount_minor?: number
  currency: string
  due_date: string | null
  issued_at: string | null
}

type Payment = {
  id: string
  amount_minor: number
  currency: string
  status: string
  method: string
  provider: string | null
  provider_ref: string | null
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
  const [payingId, setPayingId] = useState<string | null>(null)

  async function markPaid(inv: Invoice) {
    const remaining = inv.remaining_amount_minor ?? inv.total_amount_minor
    if (remaining <= 0) return
    setPayingId(inv.id)
    setError(null)
    try {
      await api('/api/v1/finance/payments', {
        method: 'POST',
        body: {
          billing_account_id: inv.billing_account_id,
          amount_minor: remaining,
          method: 'CASH',
          currency: inv.currency || 'TRY',
          allocations: [{ invoice_id: inv.id, amount_minor: remaining }],
        },
        headers: { 'Idempotency-Key': `cash-${inv.id}-${Date.now()}` },
      })
      await loadData()
    } catch (e) {
      setError(formatApiError(e, 'Nakit tahsilat kaydedilemedi'))
    } finally {
      setPayingId(null)
    }
  }

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [invRes, payRes] = await Promise.all([
        api<{ items: Invoice[]; total: number }>('/api/v1/finance/invoices?limit=50'),
        api<{ items: Payment[]; total: number }>('/api/v1/finance/payments?limit=50'),
      ])
      setInvoices(invRes.items)
      setPayments(payRes.items)
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
                    <th className="table-th">İşlem</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {invoices.length === 0 ? (
                    <tr>
                      <td
                        colSpan={6}
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
                          {inv.invoice_number || '—'}
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
                          {inv.issued_at
                            ? new Date(inv.issued_at).toLocaleDateString('tr-TR')
                            : '—'}
                        </td>
                        <td className="table-td">
                          {inv.status !== 'PAID' &&
                          (inv.remaining_amount_minor ?? inv.total_amount_minor) >
                            0 ? (
                            <button
                              type="button"
                              className="btn-secondary text-xs"
                              disabled={payingId === inv.id}
                              onClick={() => void markPaid(inv)}
                            >
                              {payingId === inv.id
                                ? 'Kaydediliyor…'
                                : 'Nakit tahsil'}
                            </button>
                          ) : (
                            '—'
                          )}
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
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {payments.length === 0 ? (
                    <tr>
                      <td
                        colSpan={4}
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
                          {pay.method || 'Bilinmiyor'}
                        </td>
                        <td className="table-td font-mono text-xs text-slate-400">
                          {pay.provider_ref || '—'}
                        </td>
                        <td className="table-td font-medium text-slate-200">
                          {formatCurrency(pay.amount_minor, pay.currency)}
                        </td>
                        <td className="table-td">
                          <StatusBadge status={pay.status} kind="payment" />
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
