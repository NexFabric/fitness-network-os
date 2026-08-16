import { useCallback, useEffect, useState } from 'react'
import { api, ApiError } from '../api/client'
import { Alert, EmptyState, LoadingSkeleton, PageHeader } from '../components/ui'

type MemberSearchResult = {
  id: string
  member_number: string
  first_name: string
  last_name: string
  email: string | null
  phone: string | null
  status: string
  has_active_membership: boolean
  total_remaining_entitlements: number
}

type MemberDetail = {
  id: string
  member_number: string
  first_name: string
  last_name: string
  email: string | null
  phone: string | null
  status: string
  tags: string[]
  notes: string[]
  memberships: Array<{
    id: string
    status: string
    start_date: string | null
    end_date: string | null
  }>
  wallets: Array<{
    id: string
    allocated: number
    remaining: number
    expires_at: string | null
  }>
  invoices: Array<{
    id: string
    invoice_number: string | null
    status: string
    total_amount_minor: number
    paid_amount_minor: number
    due_date: string | null
  }>
  payments: Array<{
    id: string
    amount_minor: number
    currency: string
    status: string
    method: string
    created_at: string | null
  }>
  recent_checkins: Array<{
    id: string
    location_id: string
    checkin_time: string | null
    checkout_time: string | null
  }>
  total_debt_minor: number
  currency: string
}

type LocationItem = {
  id: string
  name: string
}

export default function Reception() {
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState<MemberSearchResult[]>([])
  const [searching, setSearching] = useState(false)
  const [selectedMemberId, setSelectedMemberId] = useState<string | null>(null)
  const [memberDetail, setMemberDetail] = useState<MemberDetail | null>(null)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [locations, setLocations] = useState<LocationItem[]>([])
  const [selectedLocationId, setSelectedLocationId] = useState<string>('')

  const [overrideReason, setOverrideReason] = useState('')
  const [overriding, setOverriding] = useState(false)
  const [overrideMessage, setOverrideMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  // Load locations on mount
  useEffect(() => {
    async function loadLocations() {
      try {
        const locs = await api<LocationItem[]>('/api/v1/locations')
        setLocations(locs)
        if (locs.length > 0) {
          setSelectedLocationId(locs[0].id)
        }
      } catch (err) {
        console.error('Lokasyonlar yüklenemedi:', err)
      }
    }
    void loadLocations()
  }, [])

  // Search members debounce
  useEffect(() => {
    if (!query.trim()) {
      setSearchResults([])
      return
    }
    const timer = setTimeout(async () => {
      setSearching(true)
      try {
        const res = await api<MemberSearchResult[]>(`/api/v1/reception/search?q=${encodeURIComponent(query.trim())}`)
        setSearchResults(res)
      } catch (err) {
        console.error('Arama hatası:', err)
      } finally {
        setSearching(false)
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [query])

  // Load selected member detail
  const loadMemberDetail = useCallback(async (id: string) => {
    setLoadingDetail(true)
    try {
      const detail = await api<MemberDetail>(`/api/v1/reception/member/${id}`)
      setMemberDetail(detail)
    } catch (err) {
      console.error('Üye detay hatası:', err)
    } finally {
      setLoadingDetail(false)
    }
  }, [])

  useEffect(() => {
    setOverrideMessage(null)
    if (selectedMemberId) {
      void loadMemberDetail(selectedMemberId)
    } else {
      setMemberDetail(null)
    }
  }, [selectedMemberId, loadMemberDetail])

  // Handle manual override checkin
  async function handleManualOverride(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedMemberId || !selectedLocationId || !overrideReason.trim()) return

    setOverriding(true)
    setOverrideMessage(null)
    try {
      const res = await api<{ message: string }>(`/api/v1/reception/checkin/${selectedMemberId}/override`, {
        method: 'POST',
        body: {
          location_id: selectedLocationId,
          reason: overrideReason.trim(),
        },
      })
      setOverrideMessage({ type: 'success', text: res.message })
      setOverrideReason('')
      await loadMemberDetail(selectedMemberId)
    } catch (err) {
      if (err instanceof ApiError) {
        setOverrideMessage({ type: 'error', text: err.message || 'Manuel geçiş onaylanamadı.' })
      } else {
        setOverrideMessage({ type: 'error', text: 'İşlem gerçekleştirilemedi. Lütfen tekrar deneyin.' })
      }
    } finally {
      setOverriding(false)
    }
  }

  const formatMinor = (minor: number) =>
    (minor / 100).toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' ₺'

  return (
    <div>
      <PageHeader
        title="Resepsiyon & Danışma Masası"
        subtitle="Hızlı üye arama, anlık kimlik ve abonelik doğrulama, manuel turnike geçiş yetkilendirmesi."
      />

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left Column: Instant Member Search */}
        <div className="lg:col-span-5 space-y-4">
          <div className="card p-4">
            <label htmlFor="member-search" className="block text-xs font-bold uppercase tracking-wider text-ink-muted">
              Üye Arama (İsim, Telefon, Kart No, E-posta)
            </label>
            <div className="mt-2 relative">
              <input
                id="member-search"
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Örn: Ahmet, 555..., MEM-102"
                className="input-field !mt-0 w-full pr-10 text-sm font-medium text-slate-100 placeholder:text-slate-500 bg-slate-900/90 border-slate-700 focus:border-brand focus:ring-1 focus:ring-brand"
                autoFocus
              />
              {searching && (
                <div className="absolute right-3 top-2.5 text-xs text-brand font-medium">
                  Aranıyor…
                </div>
              )}
            </div>

            {/* Search Results List */}
            <div className="mt-4 max-h-[520px] space-y-2 overflow-y-auto pr-1">
              {searchResults.map((m) => (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => setSelectedMemberId(m.id)}
                  className={`w-full text-left rounded-xl border p-3 transition-all ${
                    selectedMemberId === m.id
                      ? 'border-brand bg-brand/10 shadow-sm'
                      : 'border-slate-800 bg-slate-900/60 hover:bg-slate-800/60'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-sm text-slate-100">
                      {m.first_name} {m.last_name}
                    </span>
                    <span
                      className={`rounded px-2 py-0.5 text-[10px] font-bold ${
                        m.has_active_membership
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                          : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                      }`}
                    >
                      {m.has_active_membership ? 'Aktif Paket' : 'Paket Yok'}
                    </span>
                  </div>
                  <div className="mt-1 flex items-center justify-between text-xs text-slate-400">
                    <span className="font-mono">{m.member_number}</span>
                    <span>{m.phone || m.email || '—'}</span>
                  </div>
                </button>
              ))}

              {!searching && query.trim() !== '' && searchResults.length === 0 && (
                <p className="py-6 text-center text-xs text-slate-500">
                  Aramanızla eşleşen üye bulunamadı.
                </p>
              )}

              {!query.trim() && (
                <p className="py-8 text-center text-xs text-slate-500">
                  Aramaya başlamak için yukarıdaki kutuya yazın.
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Member Overview Card & Manual Override */}
        <div className="lg:col-span-7">
          {!selectedMemberId && (
            <div className="card flex h-full min-h-[400px] items-center justify-center p-8 text-center">
              <EmptyState
                title="Üye Seçilmedi"
                description="Detayları incelemek ve manuel geçiş onayı vermek için sol listeden bir üye seçin."
              />
            </div>
          )}

          {selectedMemberId && loadingDetail && (
            <div className="card p-6">
              <LoadingSkeleton rows={6} />
            </div>
          )}

          {selectedMemberId && !loadingDetail && memberDetail && (
            <div className="space-y-4">
              {/* Member Card Header */}
              <div className="card p-5 border-slate-800 bg-slate-900">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <h2 className="text-xl font-extrabold text-white">
                      {memberDetail.first_name} {memberDetail.last_name}
                    </h2>
                    <p className="mt-0.5 text-xs text-slate-400">
                      Üye No: <span className="font-mono text-slate-300 font-bold">{memberDetail.member_number}</span>
                      {memberDetail.phone && ` · Tel: ${memberDetail.phone}`}
                      {memberDetail.email && ` · E-posta: ${memberDetail.email}`}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="rounded-full bg-slate-800 px-3 py-1 text-xs font-bold text-slate-300 border border-slate-700">
                      {memberDetail.status}
                    </span>
                    {memberDetail.total_debt_minor > 0 && (
                      <span className="rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 px-3 py-1 text-xs font-bold">
                        Borç: {formatMinor(memberDetail.total_debt_minor)}
                      </span>
                    )}
                  </div>
                </div>

                {/* Tags & Notes */}
                {(memberDetail.tags.length > 0 || memberDetail.notes.length > 0) && (
                  <div className="mt-3 border-t border-slate-800 pt-3 flex flex-wrap gap-2 items-center">
                    {memberDetail.tags.map((t) => (
                      <span key={t} className="rounded bg-sky-500/10 text-sky-400 border border-sky-500/20 px-2 py-0.5 text-[11px] font-semibold">
                        🏷️ {t}
                      </span>
                    ))}
                    {memberDetail.notes.map((n, i) => (
                      <span key={i} className="rounded bg-amber-500/10 text-amber-300 border border-amber-500/20 px-2 py-0.5 text-[11px]">
                        📝 {n}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Subscriptions & Entitlements Strip */}
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                <div className="card p-4 border-slate-800 bg-slate-900/60">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Abonelik Durumu
                  </h3>
                  {memberDetail.memberships.length === 0 ? (
                    <p className="mt-2 text-xs text-slate-500">Kayıtlı paket bulunmuyor.</p>
                  ) : (
                    <div className="mt-2 space-y-1.5">
                      {memberDetail.memberships.slice(0, 2).map((m) => (
                        <div key={m.id} className="flex justify-between text-xs">
                          <span className="text-slate-300">
                            Bitiş: {m.end_date ? new Date(m.end_date).toLocaleDateString('tr-TR') : 'Süresiz'}
                          </span>
                          <span className={m.status === 'ACTIVE' ? 'font-bold text-emerald-400' : 'text-slate-400'}>
                            {m.status}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="card p-4 border-slate-800 bg-slate-900/60">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Kalan Kullanım Hakları
                  </h3>
                  {memberDetail.wallets.length === 0 ? (
                    <p className="mt-2 text-xs text-slate-500">Özel hak cüzdanı tanımlı değil.</p>
                  ) : (
                    <div className="mt-2 space-y-1.5">
                      {memberDetail.wallets.slice(0, 2).map((w) => (
                        <div key={w.id} className="flex justify-between text-xs">
                          <span className="text-slate-300">Giriş / Seans</span>
                          <span className="font-bold text-cyan-400">{w.remaining} / {w.allocated} Kalan</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Manual Turnstile Override Action Form */}
              <div className="card p-5 border-brand/30 bg-gradient-to-br from-slate-900 to-slate-950 shadow-lg">
                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                  <span>⚡</span> Manuel Turnike / Giriş Onayı (Override)
                </h3>
                <p className="mt-1 text-xs text-slate-400">
                  Kartını unutan veya turnike mekanik sorununda yetkili personel onaylı manuel geçiş hakkı tanır.
                </p>

                {overrideMessage && (
                  <div className="mt-3">
                    <Alert variant={overrideMessage.type === 'success' ? 'success' : 'error'}>
                      {overrideMessage.text}
                    </Alert>
                  </div>
                )}

                <form onSubmit={handleManualOverride} className="mt-4 space-y-3">
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                    <div>
                      <label htmlFor="reception-location" className="block text-xs font-semibold text-slate-300">
                        Şube / Lokasyon
                      </label>
                      <select
                        id="reception-location"
                        value={selectedLocationId}
                        onChange={(e) => setSelectedLocationId(e.target.value)}
                        className="input-field text-xs bg-slate-900/90 text-slate-100 border-slate-700"
                        required
                      >
                        {locations.map((loc) => (
                          <option key={loc.id} value={loc.id} className="bg-slate-900 text-slate-100">
                            {loc.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label htmlFor="override-reason" className="block text-xs font-semibold text-slate-300">
                        Geçiş Gerekçesi
                      </label>
                      <input
                        id="override-reason"
                        type="text"
                        value={overrideReason}
                        onChange={(e) => setOverrideReason(e.target.value)}
                        placeholder="Örn: Kartını evde unutmuş, kimlik kontrolü yapıldı."
                        className="input-field text-xs bg-slate-900/90 text-slate-100 placeholder:text-slate-500 border-slate-700"
                        required
                        minLength={3}
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={overriding || !overrideReason.trim()}
                    className="btn-primary w-full justify-center py-2.5 font-bold"
                  >
                    {overriding ? 'Onaylanıyor…' : 'Manuel Girişi Onayla & Kaydet'}
                  </button>
                </form>
              </div>

              {/* Recent Access History */}
              <div className="card p-4 border-slate-800 bg-slate-900/40">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
                  Son Giriş Kayıtları
                </h3>
                {memberDetail.recent_checkins.length === 0 ? (
                  <p className="text-xs text-slate-500">Henüz giriş kaydı bulunmuyor.</p>
                ) : (
                  <div className="space-y-1.5 max-h-36 overflow-y-auto">
                    {memberDetail.recent_checkins.map((c) => (
                      <div key={c.id} className="flex justify-between text-xs text-slate-300 py-1 border-b border-slate-800/60 last:border-0">
                        <span>{c.checkin_time ? new Date(c.checkin_time).toLocaleString('tr-TR') : '—'}</span>
                        <span className="text-[10px] text-emerald-400 font-semibold">Başarılı Giriş</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
