import { useEffect, useState } from 'react'
import { api } from '../api/client'

type AccessLog = {
  id: string
  status: string
  denial_reason: string | null
  method: string | null
  timestamp: string
}

export default function MemberAccessLogs({ memberId }: { memberId: string }) {
  const [logs, setLogs] = useState<AccessLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchLogs() {
      setLoading(true)
      setError(null)
      try {
        const data = await api<AccessLog[]>(`/api/v1/members/${memberId}/access-logs`)
        setLogs(data)
      } catch (err: any) {
        setError(err?.message || 'Giriş logları yüklenemedi')
      } finally {
        setLoading(false)
      }
    }
    void fetchLogs()
  }, [memberId])

  if (loading) {
    return <div className="text-xs text-slate-500 py-3">Giriş geçmişi yükleniyor...</div>
  }

  if (error) {
    return <div className="text-xs text-rose-400 py-2">{error}</div>
  }

  if (logs.length === 0) {
    return <div className="text-xs text-slate-500 py-3">Henüz giriş kaydı bulunmuyor.</div>
  }

  return (
    <div className="space-y-2 mt-2">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="text-slate-400 border-b border-slate-800">
            <tr>
              <th className="pb-2 font-medium">Tarih / Saat</th>
              <th className="pb-2 font-medium">Yöntem</th>
              <th className="pb-2 font-medium">Durum</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {logs.map((log) => {
              const isGranted = log.status === 'GRANTED'
              const dt = new Date(log.timestamp).toLocaleString('tr-TR')
              return (
                <tr key={log.id} className="text-slate-300">
                  <td className="py-2.5 font-mono text-[11px]">{dt}</td>
                  <td className="py-2.5 text-slate-400">{log.method || 'QR_SCAN'}</td>
                  <td className="py-2.5">
                    {isGranted ? (
                      <span className="inline-flex items-center gap-1 text-emerald-400 font-semibold text-[11px]">
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
                        GİRİŞ BAŞARILI
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-rose-400 font-semibold text-[11px]">
                        <span className="h-1.5 w-1.5 rounded-full bg-rose-400"></span>
                        ENGELENDİ ({log.denial_reason || 'RED'})
                      </span>
                    )}
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
