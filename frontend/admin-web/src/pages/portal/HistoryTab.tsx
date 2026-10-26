import { EmptyState } from '../../components/ui'
import { type MeCheckin } from './types'

type HistoryTabProps = {
  checkins: MeCheckin[]
}

export function HistoryTab({ checkins }: HistoryTabProps) {
  return (
    <div>
      <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-slate-400">Son Giriş Kayıtları</h3>
      {checkins.length === 0 ? (
        <EmptyState
          title="Giriş kaydı bulunamadı"
          description="Turnikeden gerçekleştirdiğiniz geçişler burada listelenir."
        />
      ) : (
        <div className="max-h-72 space-y-2 overflow-y-auto pr-1">
          {checkins.map((c) => (
            <div
              key={c.id}
              className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs"
            >
              <div className="flex items-center gap-2.5">
                <div className="h-2 w-2 rounded-full bg-emerald-400" />
                <div>
                  <div className="font-semibold text-slate-200">
                    {new Date(c.checkin_time).toLocaleString('tr-TR')}
                  </div>
                  <div className="text-[10px] text-slate-500">
                    {c.checkout_time
                      ? `Çıkış: ${new Date(c.checkout_time).toLocaleTimeString('tr-TR')}`
                      : 'Kulüp İçi'}
                  </div>
                </div>
              </div>
              <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] text-slate-300">Başarılı</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
