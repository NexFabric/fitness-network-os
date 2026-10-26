import { EmptyState } from '../../components/ui'
import { staffLabel, type ClassBooking, type ClassSession, type PtAppointment, type TrainerOption } from '../classes/types'
import { formatDateTr, formatTime } from './types'

type ClassesTabProps = {
  categoryFilter: string
  filteredSessions: ClassSession[]
  myBookings: ClassBooking[]
  myPtAppointments: PtAppointment[]
  trainers: TrainerOption[]
  bookingLoading: boolean
  showPtModal: boolean
  ptTrainerId: string
  ptLocationId: string
  ptLocations: { id: string; name: string }[]
  ptStart: string
  ptEnd: string
  ptNotes: string
  onCategoryChange: (cat: string) => void
  onOpenPtModal: () => void
  onClosePtModal: () => void
  onBookSession: (sessionId: string) => void
  onCancelBooking: (bookingId: string) => void
  onCancelPt: (appointmentId: string) => void
  onBookPt: (e: React.FormEvent) => void
  onPtTrainerChange: (id: string) => void
  onPtLocationChange: (id: string) => void
  onPtStartChange: (value: string) => void
  onPtEndChange: (value: string) => void
  onPtNotesChange: (value: string) => void
}

export function ClassesTab({
  categoryFilter,
  filteredSessions,
  myBookings,
  myPtAppointments,
  trainers,
  bookingLoading,
  showPtModal,
  ptTrainerId,
  ptLocationId,
  ptLocations,
  ptStart,
  ptEnd,
  ptNotes,
  onCategoryChange,
  onOpenPtModal,
  onClosePtModal,
  onBookSession,
  onCancelBooking,
  onCancelPt,
  onBookPt,
  onPtTrainerChange,
  onPtLocationChange,
  onPtStartChange,
  onPtEndChange,
  onPtNotesChange,
}: ClassesTabProps) {
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <div className="flex gap-1.5 overflow-x-auto pb-1 text-xs">
          {['ALL', 'PILATES', 'CARDIO', 'YOGA', 'HIIT', 'CROSSFIT'].map((cat) => (
            <button
              key={cat}
              onClick={() => onCategoryChange(cat)}
              className={`px-2.5 py-1 rounded-lg font-medium transition-colors ${
                categoryFilter === cat
                  ? 'bg-emerald-500 text-slate-950 font-bold'
                  : 'bg-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              {cat === 'ALL' ? 'Tümü' : cat}
            </button>
          ))}
        </div>
        <button
          onClick={onOpenPtModal}
          className="btn btn-secondary text-xs px-2.5 py-1 shrink-0 text-cyan-400 border-cyan-500/40"
        >
          + PT Randevusu
        </button>
      </div>

      {myBookings.filter((b) => b.status === 'CONFIRMED' || b.status === 'WAITLISTED').length > 0 && (
        <div className="p-3 rounded-xl border border-emerald-500/30 bg-emerald-950/30 space-y-2">
          <div className="text-xs font-bold text-emerald-400">Aktif Rezervasyonlarım</div>
          <div className="space-y-1.5">
            {myBookings
              .filter((b) => b.status === 'CONFIRMED' || b.status === 'WAITLISTED')
              .map((b) => (
                <div key={b.id} className="flex items-center justify-between text-xs bg-slate-900/80 p-2 rounded-lg">
                  <div>
                    <span className="font-semibold text-white">Ders Rezervasyonu</span>
                    {b.status === 'WAITLISTED' ? (
                      <span className="ml-2 text-amber-400 font-bold">🟡 Yedek #{b.waitlist_position}</span>
                    ) : (
                      <span className="ml-2 text-emerald-400 font-bold">🟢 Onaylandı</span>
                    )}
                  </div>
                  <button
                    disabled={bookingLoading}
                    onClick={() => onCancelBooking(b.id)}
                    className="text-red-400 hover:text-red-300 font-bold"
                  >
                    İptal Et
                  </button>
                </div>
              ))}
          </div>
        </div>
      )}

      {filteredSessions.length === 0 ? (
        <EmptyState title="Planlanmış Ders Seansı Yok" description="Yakın zamanda planlanan grup dersi bulunmuyor." />
      ) : (
        <div className="space-y-3">
          {filteredSessions.map((s) => {
            const isFull = s.confirmed_count >= s.capacity
            const userStatus = s.user_booking_status

            return (
              <div
                key={s.id}
                className="p-4 rounded-2xl border border-slate-800 bg-slate-900 flex flex-col justify-between relative overflow-hidden"
              >
                <div
                  className="absolute top-0 left-0 right-0 h-1"
                  style={{ backgroundColor: s.class_type_color || '#10B981' }}
                />
                <div>
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300 uppercase tracking-wider">
                      {s.class_type_category || 'DERS'}
                    </span>
                    <span className="text-xs font-semibold text-slate-400">
                      {s.confirmed_count} / {s.capacity} Kişi
                    </span>
                  </div>
                  <h3 className="font-bold text-white text-base">{s.class_type_name}</h3>
                  <div className="text-xs text-slate-400 space-y-0.5 my-2">
                    <div>
                      ⏰ {formatDateTr(s.start_time_utc)} - {formatTime(s.end_time_utc)}
                    </div>
                    <div>🏋️ Eğitmen: {s.trainer_name || 'Eğitmen'}</div>
                    <div>
                      📍 {s.location_name || 'Ana Şube'} {s.room_name ? `(${s.room_name})` : ''}
                    </div>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                  <div>
                    {userStatus === 'CONFIRMED' && (
                      <span className="text-xs text-emerald-400 font-bold">✓ Rezervasyonunuz Var</span>
                    )}
                    {userStatus === 'WAITLISTED' && (
                      <span className="text-xs text-amber-400 font-bold">
                        🟡 Yedektesiniz (#{s.user_waitlist_position})
                      </span>
                    )}
                    {!userStatus && (
                      <span className={`text-xs font-medium ${isFull ? 'text-amber-400' : 'text-emerald-400'}`}>
                        {isFull
                          ? `Kontenjan Dolu (${s.waitlist_count} Yedek)`
                          : `${s.capacity - s.confirmed_count} Boş Yer`}
                      </span>
                    )}
                  </div>

                  <div>
                    {!userStatus ? (
                      <button
                        disabled={bookingLoading}
                        onClick={() => onBookSession(s.id)}
                        className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                          isFull
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 hover:bg-amber-500/30'
                            : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-500/20'
                        }`}
                      >
                        {isFull ? `Yedek Sıraya Gir (#${s.waitlist_count + 1})` : 'Rezervasyon Yap'}
                      </button>
                    ) : (
                      <span className="text-xs text-slate-500">Kayıtlı</span>
                    )}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {myPtAppointments.length > 0 && (
        <div className="mt-6">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">Birebir PT Randevularım</h3>
          <div className="space-y-2">
            {myPtAppointments.map((pt) => (
              <div
                key={pt.id}
                className="p-3 rounded-xl border border-slate-800 bg-slate-900 flex justify-between items-center text-xs"
              >
                <div>
                  <div className="font-semibold text-white">Antrenör: {pt.trainer_name || 'Atanmış Antrenör'}</div>
                  <div className="text-slate-400 mt-0.5">
                    ⏰ {formatDateTr(pt.start_time_utc)} - {formatTime(pt.end_time_utc)}
                  </div>
                </div>
                {pt.status === 'CONFIRMED' && (
                  <button
                    disabled={bookingLoading}
                    onClick={() => onCancelPt(pt.id)}
                    className="text-red-400 hover:text-red-300 font-bold"
                  >
                    İptal
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {showPtModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-md p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-white">1-on-1 PT Randevusu Al</h3>
            <form onSubmit={onBookPt} className="space-y-3">
              <div>
                <label htmlFor="pt-trainer" className="block text-xs font-medium text-slate-400 mb-1">
                  Antrenör
                </label>
                <select
                  id="pt-trainer"
                  required
                  disabled={trainers.length === 0}
                  aria-invalid={trainers.length === 0}
                  value={ptTrainerId}
                  onChange={(e) => onPtTrainerChange(e.target.value)}
                  className="input w-full text-xs"
                >
                  <option value="" disabled>
                    {trainers.length === 0 ? 'Henüz antrenör tanımlı değil' : 'Antrenör seçin'}
                  </option>
                  {trainers.map((t) => (
                    <option key={t.user_id} value={t.user_id}>
                      {staffLabel(t)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label htmlFor="pt-location" className="block text-xs font-medium text-slate-400 mb-1">
                  Şube
                </label>
                <select
                  id="pt-location"
                  required
                  disabled={ptLocations.length === 0}
                  aria-invalid={ptLocations.length === 0}
                  value={ptLocationId}
                  onChange={(e) => onPtLocationChange(e.target.value)}
                  className="input w-full text-xs"
                >
                  <option value="" disabled>
                    {ptLocations.length === 0 ? 'Takvimde şube yok — önce bir seans olmalı' : 'Şube seçin'}
                  </option>
                  {ptLocations.map((loc) => (
                    <option key={loc.id} value={loc.id}>
                      {loc.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Başlangıç Zamanı</label>
                <input
                  type="datetime-local"
                  required
                  value={ptStart}
                  onChange={(e) => onPtStartChange(e.target.value)}
                  className="input w-full text-xs"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Bitiş Zamanı</label>
                <input
                  type="datetime-local"
                  required
                  value={ptEnd}
                  onChange={(e) => onPtEndChange(e.target.value)}
                  className="input w-full text-xs"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Hedef & Notlar</label>
                <input
                  type="text"
                  value={ptNotes}
                  onChange={(e) => onPtNotesChange(e.target.value)}
                  placeholder="Örn: Sırt & Kol antrenmanı"
                  className="input w-full text-xs"
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button type="button" onClick={onClosePtModal} className="btn btn-secondary text-xs px-3 py-1.5">
                  Vazgeç
                </button>
                <button
                  type="submit"
                  disabled={bookingLoading || trainers.length === 0 || ptLocations.length === 0}
                  className="btn btn-primary text-xs px-3 py-1.5"
                >
                  Randevu Oluştur
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
