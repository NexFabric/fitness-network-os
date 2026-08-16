import { EmptyState } from '../../components/ui'
import { DAYS_TR, type ClassSchedule } from './types'

type SchedulesTabProps = {
  schedules: ClassSchedule[]
}

export function SchedulesTab({ schedules }: SchedulesTabProps) {
  return (
    <div className="space-y-4">
      <div className="p-4 rounded-xl border border-border/40 bg-card">
        <h3 className="font-semibold text-foreground mb-2">Haftalık Sabit Program Şablonu</h3>
        <p className="text-sm text-muted-foreground mb-4">
          Burada tanımlanan haftalık dersler &quot;Toplu Seans Üret&quot; butonuyla istenen tarih aralığına otomatik kopyalanır.
        </p>

        {schedules.length === 0 ? (
          <EmptyState
            title="Haftalık Program Tanımlanmamış"
            description="Şablon ekleyerek her hafta tekrar eden seansları tek tıkla üretebilirsiniz."
          />
        ) : (
          <div className="divide-y divide-border/30">
            {schedules.map((sch) => (
              <div key={sch.id} className="py-3 flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-foreground">{sch.class_type_name}</span>
                    <span className="text-xs px-2 py-0.5 rounded bg-primary/10 text-primary font-medium">
                      {DAYS_TR[sch.day_of_week]}
                    </span>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    Saat: {sch.start_time.slice(0, 5)} - {sch.end_time.slice(0, 5)} | Eğitmen:{' '}
                    {sch.trainer_name || 'Eğitmen'} | Kapasite: {sch.capacity} kişi{' '}
                    {sch.room_name ? `(${sch.room_name})` : ''}
                  </div>
                </div>
                <span className="text-xs text-emerald-500 font-medium">Aktif Şablon</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
