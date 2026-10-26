import { Alert, EmptyState } from '../../components/ui'
import { type IssuedQr } from './types'

type AccessTabProps = {
  hasActiveMembership: boolean
  issuing: boolean
  issueError: string | null
  qr: IssuedQr | null
  qrImage: string | null
  secondsLeft: number
  expired: boolean
  onIssueQr: () => void
}

export function AccessTab({
  hasActiveMembership,
  issuing,
  issueError,
  qr,
  qrImage,
  secondsLeft,
  expired,
  onIssueQr,
}: AccessTabProps) {
  return (
    <div>
      {!hasActiveMembership && (
        <div className="mb-3">
          <Alert variant="info">Aktif aboneliğiniz görünmüyor. Turnikeden geçiş reddedilebilir.</Alert>
        </div>
      )}

      <button
        type="button"
        onClick={() => void onIssueQr()}
        disabled={issuing}
        className="flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-emerald-500 to-emerald-600 px-4 py-3.5 text-base font-extrabold text-white shadow-lg shadow-emerald-500/20 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50"
      >
        {issuing ? 'Oluşturuluyor…' : 'Giriş QR kodu oluştur'}
      </button>

      {issueError && (
        <div className="mt-3">
          <Alert variant="error">{issueError}</Alert>
        </div>
      )}

      {qr && qrImage && (
        <div className="mt-5 text-center">
          <div className="mb-2 flex items-center justify-center gap-2 text-sm font-bold" role="status" aria-live="polite">
            <span>Kalan süre:</span>
            <span className={secondsLeft <= 10 ? 'font-extrabold text-red-400' : 'font-extrabold text-amber-400'}>
              {expired ? 'Süre doldu — yeniden oluşturun' : `${secondsLeft} sn`}
            </span>
          </div>

          <div
            className={`mb-2 inline-block rounded-2xl bg-white p-3.5 shadow-xl transition-opacity ${expired ? 'opacity-25' : 'opacity-100'}`}
          >
            <img src={qrImage} alt="Giriş QR kodu" className="h-48 w-48" />
          </div>

          <p className="text-xs leading-relaxed text-slate-400">
            QR kodunuzu turnikedeki okuyucuya gösterin. Kod 60 saniye geçerlidir.
          </p>
        </div>
      )}

      {!qr && (
        <div className="mt-4">
          <EmptyState
            title="Henüz QR kodu oluşturmadınız"
            description="Turnikeye geldiğinizde kodu oluşturun; güvenli ve dinamik üretilir."
          />
        </div>
      )}
    </div>
  )
}
