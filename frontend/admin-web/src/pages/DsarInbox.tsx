import { useCallback, useEffect, useState } from 'react'
import { api, ApiError } from '../api/client'
import { Alert, EmptyState, LoadingSkeleton, PageHeader } from '../components/ui'

type DsarRow = {
  id: string
  member_id: string
  kind: string
  status: string
  due_at: string
  download_url: string | null
  rejection_reason: string | null
}

export default function DsarInbox() {
  const [rows, setRows] = useState<DsarRow[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setError(null)
    try {
      const data = await api<DsarRow[]>('/api/v1/admin/dsar')
      setRows(data)
    } catch (e) {
      setError(e instanceof ApiError ? e.message : 'DSAR listesi alınamadı')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  return (
    <div>
      <PageHeader
        title="KVKK başvuruları"
        subtitle="Üye dışa aktarma ve silme talepleri. Açık fatura silmeyi reddeder; tahsilat kayıtları saklanır."
      />
      {loading && <LoadingSkeleton rows={4} />}
      {error && (
        <div className="mt-6">
          <Alert onRetry={() => void load()}>{error}</Alert>
        </div>
      )}
      {!loading && !error && rows.length === 0 && (
        <div className="mt-6">
          <EmptyState title="Talep yok" description="Üyeler portalından paket isteyince burada görünür." />
        </div>
      )}
      {rows.length > 0 && (
        <div className="table-shell mt-6">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                <th className="table-th">Üye</th>
                <th className="table-th">Tür</th>
                <th className="table-th">Durum</th>
                <th className="table-th">Son tarih</th>
                <th className="table-th">Paket</th>
                <th className="table-th">Ret</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {rows.map((r) => (
                <tr key={r.id}>
                  <td className="table-td font-mono text-xs text-slate-400">{r.member_id}</td>
                  <td className="table-td text-slate-300">{r.kind}</td>
                  <td className="table-td text-slate-300">{r.status}</td>
                  <td className="table-td text-slate-400">{r.due_at.slice(0, 10)}</td>
                  <td className="table-td">
                    {r.download_url ? (
                      <a className="text-teal-400 underline" href={r.download_url} target="_blank" rel="noreferrer">
                        İndir
                      </a>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="table-td text-xs text-rose-400">{r.rejection_reason ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
