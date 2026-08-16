import { EmptyState, StatusBadge } from '../../components/ui'
import { formatDateTr, formatTime, type ClassSession } from './types'

type SessionsTabProps = {
  sessions: ClassSession[]
  onOpenSessionModal: () => void
  onOpenRoster: (sessionId: string) => void
}

export function SessionsTab({ sessions, onOpenSessionModal, onOpenRoster }: SessionsTabProps) {
  if (sessions.length === 0) {
    return (
      <div className="space-y-4">
        <EmptyState
          title="Henüz Planlanmış Ders Seansı Yok"
          description="Yeni seans ekleyebilir veya haftalık şablondan toplu seans üretebilirsiniz."
          actionLabel="+ İlk Seansı Ekle"
          onAction={onOpenSessionModal}
        />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sessions.map((sess) => {
          const isFull = sess.confirmed_count >= sess.capacity
          return (
            <div
              key={sess.id}
              className="p-5 rounded-xl border border-border/40 bg-card hover:border-primary/40 transition-all flex flex-col justify-between shadow-sm relative overflow-hidden"
            >
              <div
                className="absolute top-0 left-0 right-0 h-1.5"
                style={{ backgroundColor: sess.color_hex || '#3B82F6' }}
              />
              <div>
                <div className="flex justify-between items-start mb-2">
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-muted/60 text-muted-foreground uppercase tracking-wider">
                    {sess.class_category || 'DERS'}
                  </span>
                  <StatusBadge
                    status={
                      sess.status === 'SCHEDULED' ? (isFull ? 'PENDING' : 'ACTIVE') : sess.status
                    }
                  />
                </div>

                <h3 className="font-bold text-lg text-foreground mb-1">
                  {sess.class_type_name || 'Grup Dersi'}
                </h3>

                <div className="text-sm text-muted-foreground space-y-1 my-3">
                  <div className="flex items-center gap-2">
                    <span>⏰</span>
                    <span className="font-medium text-foreground">
                      {formatDateTr(sess.start_time_utc)} - {formatTime(sess.end_time_utc)}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>🏋️</span>
                    <span>Eğitmen: {sess.trainer_name || 'Atanmamış'}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span>📍</span>
                    <span>
                      {sess.location_name || 'Ana Şube'} {sess.room_name ? `(${sess.room_name})` : ''}
                    </span>
                  </div>
                </div>

                <div className="my-3">
                  <div className="flex justify-between text-xs font-medium mb-1">
                    <span>
                      Doluluk: {sess.confirmed_count} / {sess.capacity}
                    </span>
                    {sess.waitlist_count > 0 && (
                      <span className="text-amber-500 font-semibold">🟡 {sess.waitlist_count} Yedek</span>
                    )}
                  </div>
                  <div className="w-full bg-muted/50 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full transition-all ${isFull ? 'bg-amber-500' : 'bg-emerald-500'}`}
                      style={{
                        width: `${Math.min(100, (sess.confirmed_count / sess.capacity) * 100)}%`,
                      }}
                    />
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-border/30 flex justify-end">
                <button
                  onClick={() => onOpenRoster(sess.id)}
                  className="btn btn-outline text-xs px-3 py-1.5 w-full justify-center"
                >
                  👥 Katılımcı Listesi & Yoklama ({sess.confirmed_count + sess.waitlist_count})
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
