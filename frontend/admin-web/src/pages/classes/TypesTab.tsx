import { type ClassType } from './types'

type TypesTabProps = {
  classTypes: ClassType[]
}

export function TypesTab({ classTypes }: TypesTabProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {classTypes.map((t) => (
        <div key={t.id} className="p-5 rounded-xl border border-border/40 bg-card flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-muted text-muted-foreground">
                {t.category}
              </span>
              <span
                className="w-3.5 h-3.5 rounded-full"
                style={{ backgroundColor: t.color_hex }}
                title={t.color_hex}
              />
            </div>
            <h3 className="font-bold text-foreground text-lg">{t.name}</h3>
            {t.description && <p className="text-sm text-muted-foreground my-2">{t.description}</p>}
            <div className="text-xs text-muted-foreground space-y-1 mt-4">
              <div>⏱️ Süre: {t.duration_minutes} dakika</div>
              <div>👥 Varsayılan Kapasite: {t.default_capacity} kişi</div>
              <div>⏳ İptal Eşiği: {t.cancellation_cutoff_minutes} dk öncesine kadar</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
