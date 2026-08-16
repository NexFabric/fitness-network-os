import { LoadingSkeleton } from '../../components/ui'
import { formatDateTr, type ClassSessionRoster } from './types'

type RosterDrawerProps = {
  roster: ClassSessionRoster
  loading: boolean
  onClose: () => void
  onMarkAttendance: (bookingId: string, status: 'ATTENDED' | 'NO_SHOW') => void
  onCancelBooking: (bookingId: string) => void
}

export function RosterDrawer({
  roster,
  loading,
  onClose,
  onMarkAttendance,
  onCancelBooking,
}: RosterDrawerProps) {
  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex justify-end">
      <div className="w-full max-w-xl bg-card border-l border-border/40 h-full p-6 overflow-y-auto flex flex-col justify-between shadow-2xl">
        <div>
          <div className="flex justify-between items-start pb-4 border-b border-border/30">
            <div>
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-primary/10 text-primary">
                YOKLAMA & KATILIMCI LİSTESİ
              </span>
              <h2 className="text-xl font-bold text-foreground mt-1">{roster.session.class_type_name}</h2>
              <p className="text-xs text-muted-foreground mt-0.5">
                {formatDateTr(roster.session.start_time_utc)} | Kapasite: {roster.total_confirmed} /{' '}
                {roster.session.capacity} (Yedek: {roster.total_waitlisted})
              </p>
            </div>
            <button
              onClick={onClose}
              className="text-muted-foreground hover:text-foreground text-xl font-bold p-1"
            >
              ✕
            </button>
          </div>

          {loading ? (
            <div className="py-8">
              <LoadingSkeleton rows={3} />
            </div>
          ) : roster.attendees.length === 0 ? (
            <div className="py-12 text-center text-muted-foreground">
              Bu seansa henüz kayıtlı katılımcı bulunmamaktadır.
            </div>
          ) : (
            <div className="divide-y divide-border/30 my-4">
              {roster.attendees.map((att) => (
                <div key={att.booking_id} className="py-3.5 flex items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-foreground">{att.member_name}</span>
                      {att.status === 'WAITLISTED' && (
                        <span className="text-xs px-2 py-0.5 rounded bg-amber-500/10 text-amber-500 font-bold">
                          Yedek #{att.waitlist_position}
                        </span>
                      )}
                      {att.status === 'ATTENDED' && (
                        <span className="text-xs px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 font-medium">
                          Geldi
                        </span>
                      )}
                      {att.status === 'NO_SHOW' && (
                        <span className="text-xs px-2 py-0.5 rounded bg-red-500/10 text-red-500 font-medium">
                          Gelmedi
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-muted-foreground mt-0.5">
                      {att.member_email || att.member_phone || 'İletişim yok'}
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5">
                    {att.status === 'CONFIRMED' && (
                      <>
                        <button
                          onClick={() => onMarkAttendance(att.booking_id, 'ATTENDED')}
                          className="btn btn-primary text-xs px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white"
                          title="Geldi Olarak İşaretle"
                        >
                          ✓ Geldi
                        </button>
                        <button
                          onClick={() => onMarkAttendance(att.booking_id, 'NO_SHOW')}
                          className="btn btn-secondary text-xs px-2.5 py-1 text-red-400 hover:text-red-300"
                          title="Gelmedi Olarak İşaretle"
                        >
                          ✕ Gelmedi
                        </button>
                      </>
                    )}
                    {att.status !== 'CANCELLED' && (
                      <button
                        onClick={() => onCancelBooking(att.booking_id)}
                        className="text-xs text-muted-foreground hover:text-red-400 p-1"
                        title="İptal Et & Yedekten Terfi Ettir"
                      >
                        İptal
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="pt-4 border-t border-border/30 flex justify-end">
          <button onClick={onClose} className="btn btn-secondary text-sm px-4 py-2">
            Kapat
          </button>
        </div>
      </div>
    </div>
  )
}
