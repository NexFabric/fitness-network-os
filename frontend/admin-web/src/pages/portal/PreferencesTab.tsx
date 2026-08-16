import { type MeConsent } from './types'

type PreferencesTabProps = {
  consents: MeConsent[]
  dsarBusy: boolean
  dsarMessage: string | null
  eraseBusy: boolean
  eraseMessage: string | null
  consentUpdating: string | null
  onDsarExport: () => void
  onDsarErasure: () => void
  onToggleConsent: (consentType: string, currentStatus: string) => void
}

export function PreferencesTab({
  consents,
  dsarBusy,
  dsarMessage,
  eraseBusy,
  eraseMessage,
  consentUpdating,
  onDsarExport,
  onDsarErasure,
  onToggleConsent,
}: PreferencesTabProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">İletişim & Gizlilik Tercihleri</h3>
      <div className="rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs">
        <p className="font-semibold text-slate-200">Verilerimi indir</p>
        <p className="mt-1 text-[11px] text-slate-400">
          KVKK: profil paketi indirilebilir. Silme adı ve iletişim bilgilerini anonimleştirir; fatura ve ödemeler
          yasal kayıt olarak kalır. Açık fatura varsa talep reddedilir.
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <button type="button" className="btn-primary" disabled={dsarBusy} onClick={() => void onDsarExport()}>
            {dsarBusy ? 'Hazırlanıyor…' : 'Paketi indir'}
          </button>
          <button
            type="button"
            className="rounded-lg border border-rose-800 bg-rose-950/60 px-3 py-1.5 text-xs font-bold text-rose-300 hover:bg-rose-900/60 disabled:opacity-50"
            disabled={eraseBusy}
            onClick={() => void onDsarErasure()}
          >
            {eraseBusy ? 'İşleniyor…' : 'Verilerimi sil'}
          </button>
        </div>
        {dsarMessage && (
          <p className="mt-2 text-slate-400" role="status">
            {dsarMessage}
          </p>
        )}
        {eraseMessage && (
          <p className="mt-2 text-rose-300" role="status">
            {eraseMessage}
          </p>
        )}
      </div>
      <div className="space-y-3">
        {[
          { type: 'MARKETING_SMS', label: 'SMS Bilgilendirmeleri', desc: 'Kampanya ve duyuru SMS mesajları' },
          { type: 'MARKETING_EMAIL', label: 'E-Posta Bültenleri', desc: 'Etkinlik ve fırsat e-postaları' },
          { type: 'KVKK_CONSENT', label: 'KVKK Açık Rıza Onayı', desc: 'Kişisel veri işleme ve mevzuat onayı' },
        ].map((item) => {
          const found = consents.find((c) => c.consent_type === item.type)
          const isGiven = found?.status === 'GIVEN'

          return (
            <div
              key={item.type}
              className="flex items-center justify-between rounded-xl border border-slate-800 bg-slate-950/40 p-3 text-xs"
            >
              <div className="max-w-[70%]">
                <div className="font-semibold text-slate-200">{item.label}</div>
                <div className="text-[11px] text-slate-400">{item.desc}</div>
              </div>
              <button
                type="button"
                disabled={consentUpdating === item.type}
                onClick={() => void onToggleConsent(item.type, isGiven ? 'GIVEN' : 'WITHDRAWN')}
                className={`rounded-lg px-3 py-1.5 text-xs font-bold transition-colors ${
                  isGiven
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 hover:bg-emerald-500/30'
                    : 'bg-slate-800 text-slate-400 border border-slate-700 hover:bg-slate-700'
                }`}
              >
                {consentUpdating === item.type ? '…' : isGiven ? 'Açık' : 'Kapalı'}
              </button>
            </div>
          )
        })}
      </div>
    </div>
  )
}
