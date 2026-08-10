import { useEffect, useState } from 'react'
import { api, ApiError } from '../api/client'

export type Membership = {
  id: string
  member_id: string
  plan_version_id: string
  status: string
  start_date: string
  end_date: string | null
  current_period_end: string | null
  canceled_at: string | null
  frozen_until: string | null
}

function formatApiError(e: unknown, fallback: string): string {
  if (e instanceof ApiError) return `${e.status}: ${e.message}`
  if (e instanceof Error) return e.message
  return fallback
}

export default function MemberMemberships({ memberId }: { memberId: string }) {
  const [memberships, setMemberships] = useState<Membership[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [freezing, setFreezing] = useState<string | null>(null) // membership_id
  const [freezeReason, setFreezeReason] = useState('')
  const [expectedEndDate, setExpectedEndDate] = useState('')

  useEffect(() => {
    async function load() {
      setLoading(true)
      try {
        const data = await api<Membership[]>(`/api/v1/members/${memberId}/memberships`)
        setMemberships(data)
      } catch (e) {
        setError(formatApiError(e, 'Abonelikler yüklenemedi'))
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [memberId])

  async function handleFreeze(membershipId: string) {
    if (!freezeReason) {
      alert("Lütfen dondurma sebebi girin")
      return
    }
    try {
      const today = new Date().toISOString().split('T')[0]
      await api(`/api/v1/memberships/${membershipId}/freeze`, {
        method: 'POST',
        body: {
          start_date: today,
          reason: freezeReason,
          expected_end_date: expectedEndDate || undefined,
        }
      })
      setFreezing(null)
      setFreezeReason('')
      setExpectedEndDate('')
      // reload
      const data = await api<Membership[]>(`/api/v1/members/${memberId}/memberships`)
      setMemberships(data)
    } catch (e) {
      alert(formatApiError(e, 'Dondurma başarısız'))
    }
  }

  async function handleUnfreeze(membershipId: string) {
    try {
      await api(`/api/v1/memberships/${membershipId}/unfreeze`, { method: 'POST' })
      const data = await api<Membership[]>(`/api/v1/members/${memberId}/memberships`)
      setMemberships(data)
    } catch (e) {
      alert(formatApiError(e, 'İşlem başarısız'))
    }
  }

  if (loading) return <p className="text-sm text-slate-400 mt-4">Abonelikler yükleniyor...</p>
  if (error) return <p className="text-sm text-rose-400 mt-4">{error}</p>

  if (memberships.length === 0) {
    return <p className="text-sm text-slate-500 mt-4">Bu üyeye ait abonelik bulunmuyor.</p>
  }

  return (
    <div className="mt-4 space-y-4">
      {memberships.map(m => (
        <div key={m.id} className="p-4 border border-slate-700 rounded-lg bg-slate-800/50">
          <div className="flex justify-between items-start mb-2">
            <div>
              <p className="text-sm font-semibold text-slate-200">
                Plan ID: <span className="font-mono text-xs">{m.plan_version_id.substring(0,8)}...</span>
              </p>
              <p className="text-xs text-slate-400 mt-1">
                Başlangıç: {m.start_date} {m.end_date ? `| Bitiş: ${m.end_date}` : ''}
              </p>
            </div>
            <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${m.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400 ring-1 ring-emerald-500/20' : m.status === 'FROZEN' ? 'bg-cyan-500/10 text-cyan-400 ring-1 ring-cyan-500/20' : 'bg-slate-700 text-slate-300'}`}>
              {m.status}
            </span>
          </div>

          <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-slate-700">
            {m.status === 'ACTIVE' && freezing !== m.id && (
              <button onClick={() => setFreezing(m.id)} className="px-3 py-1.5 text-xs font-medium bg-slate-700 hover:bg-slate-600 text-slate-200 rounded transition-colors">
                Dondur
              </button>
            )}
            {freezing === m.id && (
              <div className="flex flex-col gap-2 w-full">
                <div className="flex flex-wrap items-end gap-2 w-full">
                  <input 
                    type="text" 
                    placeholder="Dondurma sebebi..." 
                    value={freezeReason}
                    onChange={e => setFreezeReason(e.target.value)}
                    className="input-field py-1 text-sm flex-1 min-w-[180px]"
                  />
                  <div className="flex flex-col gap-1">
                    <label className="text-xs text-slate-400">Beklenen Bitiş Tarihi</label>
                    <input 
                      type="date" 
                      value={expectedEndDate}
                      onChange={e => setExpectedEndDate(e.target.value)}
                      className="input-field py-1 text-sm"
                    />
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => handleFreeze(m.id)} className="px-3 py-1 text-xs font-medium bg-cyan-600 hover:bg-cyan-500 text-white rounded transition-colors">
                      Onayla
                    </button>
                    <button onClick={() => { setFreezing(null); setFreezeReason(''); setExpectedEndDate(''); }} className="px-3 py-1 text-xs text-slate-400 hover:text-white transition-colors">
                      İptal
                    </button>
                  </div>
                </div>
              </div>
            )}
            {m.status === 'FROZEN' && (
              <button onClick={() => handleUnfreeze(m.id)} className="px-3 py-1.5 text-xs font-medium bg-emerald-600/20 hover:bg-emerald-600/30 text-emerald-400 ring-1 ring-emerald-500/30 rounded transition-colors">
                Dondurmayı Kaldır
              </button>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}
