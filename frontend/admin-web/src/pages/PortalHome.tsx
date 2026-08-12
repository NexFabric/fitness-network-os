import { Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import {
  FEDERATION_ROLES,
  MEMBER_ROLES,
  OPS_ROLES,
  ROLES,
  TRAINER_ROLES,
  type RoleName,
} from '../auth/roles'
import { EmptyState } from '../components/ui'

const SCANNER_URL =
  import.meta.env.VITE_SCANNER_URL ?? 'http://localhost:5174'

type PortalCard = {
  key: string
  to: string
  external?: boolean
  icon: string
  title: string
  description: string
  cta: string
  accent: string
  allowed: RoleName[]
}

const CARDS: PortalCard[] = [
  {
    key: 'superadmin',
    to: '/superadmin',
    icon: '👑',
    title: 'Federasyon Konsolu',
    description:
      'Organizasyonlar, kulüp (tenant) listesi ve sistem çapında audit kayıtları.',
    cta: 'Federasyon Girişi',
    accent: 'purple',
    allowed: FEDERATION_ROLES,
  },
  {
    key: 'ops',
    to: '/',
    icon: '👔',
    title: 'Kulüp Operasyon Konsolu',
    description:
      'Üye kaydı, abonelik paketleri, şube yönetimi ve finans işlemleri.',
    cta: 'Operasyonlara Git',
    accent: 'cyan',
    allowed: OPS_ROLES,
  },
  {
    key: 'trainer',
    to: '/trainer',
    icon: '🏋️',
    title: 'Antrenör Portalı',
    description: 'Size atanmış üyeler, giriş geçmişi ve hak kontrolü.',
    cta: 'Antrenör Girişi',
    accent: 'amber',
    allowed: [...TRAINER_ROLES, ROLES.GYM_OWNER, ROLES.GYM_ADMIN],
  },
  {
    key: 'member',
    to: '/member',
    icon: '📱',
    title: 'Sporcu Portalı',
    description:
      'Üyelik durumunuz, kalan giriş hakkınız ve turnike için tek kullanımlık QR.',
    cta: 'Sporcu Girişi',
    accent: 'emerald',
    allowed: MEMBER_ROLES,
  },
  {
    key: 'scanner',
    to: SCANNER_URL,
    external: true,
    icon: '📹',
    title: 'Kapı Okuyucu (Kiosk)',
    description:
      'Turnikeye monte kiosk cihazı. Kendi cihaz kimliğiyle ayrı oturum açar.',
    cta: 'Kiosk Uygulaması',
    accent: 'slate',
    allowed: [ROLES.GYM_OWNER, ROLES.GYM_ADMIN, ROLES.GYM_MANAGER],
  },
]

const ACCENT: Record<string, string> = {
  purple: 'hover:border-purple-500/50 hover:shadow-purple-500/10',
  cyan: 'hover:border-cyan-500/50 hover:shadow-cyan-500/10',
  amber: 'hover:border-amber-500/50 hover:shadow-amber-500/10',
  emerald: 'hover:border-emerald-500/50 hover:shadow-emerald-500/10',
  slate: 'hover:border-slate-500/50 hover:shadow-slate-500/10',
}

const ACCENT_TEXT: Record<string, string> = {
  purple: 'text-purple-400',
  cyan: 'text-cyan-400',
  amber: 'text-amber-400',
  emerald: 'text-emerald-400',
  slate: 'text-slate-300',
}

export default function PortalHome() {
  const { session, hasRole, signOut } = useAuth()

  // Only portals the caller's roles actually unlock — a card that leads to a
  // guarded route it cannot enter would just bounce it straight back.
  const visible = CARDS.filter((card) => hasRole(card.allowed))

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-950 px-4 py-12 text-slate-100 font-sans">
      <div className="w-full max-w-5xl">
        <div className="mb-10 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-cyan-500 font-extrabold text-white text-2xl shadow-xl shadow-emerald-500/20">
            N
          </div>
          <h1 className="text-4xl font-extrabold text-white tracking-tight">
            GymClubNex
          </h1>
          {session && (
            <p className="mt-2 text-sm text-slate-400">
              {session.email}
              {session.roles.length > 0 && (
                <span className="ml-2 text-slate-500">
                  · {session.roles.join(', ')}
                </span>
              )}
            </p>
          )}
        </div>

        {visible.length === 0 ? (
          <EmptyState
            title="Erişebileceğiniz bir portal yok"
            description="Hesabınıza henüz bir rol tanımlanmamış. Kulüp yöneticinizle iletişime geçin."
          />
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {visible.map((card) => {
              const className = `group relative flex flex-col justify-between rounded-3xl border border-slate-800 bg-slate-900 p-6 shadow-xl transition-all duration-200 hover:-translate-y-1 hover:shadow-2xl ${ACCENT[card.accent]}`
              const inner = (
                <>
                  <div>
                    <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-800/60 text-2xl">
                      {card.icon}
                    </div>
                    <h2 className="text-xl font-bold text-white">
                      {card.title}
                    </h2>
                    <p className="mt-2 text-xs leading-relaxed text-slate-400">
                      {card.description}
                    </p>
                  </div>
                  <div
                    className={`mt-6 flex items-center gap-2 text-sm font-bold ${ACCENT_TEXT[card.accent]}`}
                  >
                    <span>{card.cta}</span>
                    <span aria-hidden="true">→</span>
                  </div>
                </>
              )

              return card.external ? (
                <a
                  key={card.key}
                  href={card.to}
                  target="_blank"
                  rel="noreferrer"
                  className={className}
                >
                  {inner}
                </a>
              ) : (
                <Link key={card.key} to={card.to} className={className}>
                  {inner}
                </Link>
              )
            })}
          </div>
        )}

        <div className="mt-10 text-center">
          <button
            type="button"
            onClick={signOut}
            className="text-sm font-semibold text-slate-400 underline-offset-4 hover:text-slate-200 hover:underline"
          >
            Oturumu kapat
          </button>
        </div>
      </div>
    </div>
  )
}
