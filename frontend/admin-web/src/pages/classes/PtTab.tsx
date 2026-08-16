import { EmptyState, StatusBadge } from '../../components/ui'
import { formatDateTr, formatTime, type PtAppointment } from './types'

type PtTabProps = {
  appointments: PtAppointment[]
}

export function PtTab({ appointments }: PtTabProps) {
  return (
    <div className="p-5 rounded-xl border border-border/40 bg-card">
      <h3 className="font-semibold text-foreground mb-3">Kişisel Antrenman (PT) Randevuları</h3>
      {appointments.length === 0 ? (
        <EmptyState
          title="Henüz PT Randevusu Yok"
          description="Üyeler mobil/web portal üzerinden müsait antrenörlere birebir randevu alabilir."
        />
      ) : (
        <div className="divide-y divide-border/30">
          {appointments.map((pt) => (
            <div key={pt.id} className="py-3.5 flex items-center justify-between">
              <div>
                <div className="font-semibold text-foreground">
                  {pt.member_name || 'Üye'} ↔ {pt.trainer_name || 'Antrenör'}
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  ⏰ {formatDateTr(pt.start_time_utc)} - {formatTime(pt.end_time_utc)}
                  {pt.notes && ` | Not: "${pt.notes}"`}
                </div>
              </div>
              <StatusBadge
                status={
                  pt.status === 'CONFIRMED' ? 'ACTIVE' : pt.status === 'ATTENDED' ? 'COMPLETED' : 'CANCELLED'
                }
              />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
