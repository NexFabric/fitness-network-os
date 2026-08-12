import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, ApiError } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import MemberAccessLogs from '../components/MemberAccessLogs'
import { Alert, EmptyState, LoadingSkeleton, StatusBadge } from '../components/ui'

type Member = {
  id: string
  member_number: string
  first_name: string
  last_name: string
  status: string
}

type EntitlementCheck = {
  granted: boolean
  reason: string | null
  remaining: number | null
}

/**
 * Trainer console.
 *
 * The member list is scoped server-side: TRAINER holds members:read but not
 * members:read:all, so GET /members returns only the members assigned to this
 * trainer in trainer_assignments. Nothing here filters client-side.
 */
export default function TrainerPortal() {
  const { session, hasPermission } = useAuth()

  const [members, setMembers] = useState<Member[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const [checking, setChecking] = useState(false)
  const [checkResult, setCheckResult] = useState<EntitlementCheck | null>(null)
  const [checkError, setCheckError] = useState<string | null>(null)

  // A tenant-wide reader (owner/admin) sees everyone, so the heading must not
  // claim these are "assigned" members.
  const isAssignmentScoped = !hasPermission('members:read:all')

  const loadMembers = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      setMembers(await api<Member[]>('/api/v1/members?limit=100'))
    } catch {
      setError('Üye listesi yüklenemedi. Birkaç saniye sonra tekrar deneyin.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadMembers()
  }, [loadMembers])

  async function handleCheckEntitlement(memberId: string) {
    setChecking(true)
    setCheckError(null)
    setCheckResult(null)
    try {
      setCheckResult(
        await api<EntitlementCheck>(
          `/api/v1/members/${memberId}/entitlements/check`,
          { method: 'POST', body: { action: 'GYM_ENTRY', quantity: 1 } },
        ),
      )
    } catch (err) {
      setCheckError(
        err instanceof ApiError && err.status === 403
          ? 'Bu üye için yetkiniz yok.'
          : 'Hak kontrolü yapılamadı. Birkaç saniye sonra tekrar deneyin.',
      )
    } finally {
      setChecking(false)
    }
  }

  const selected = members.find((m) => m.id === selectedId) ?? null

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-8 text-slate-100 font-sans">
      <div className="mx-auto w-full max-w-5xl">
        <header className="mb-8 flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-white">
              Antrenör Portalı
            </h1>
            <p className="mt-1 text-sm text-slate-400">
              {isAssignmentScoped
                ? 'Size atanmış üyeler'
                : 'Kulüpteki tüm üyeler'}
              {session?.email && ` · ${session.email}`}
            </p>
          </div>
          <Link
            to="/portal"
            className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-semibold text-slate-300 hover:bg-slate-800"
          >
            Portallara dön
          </Link>
        </header>

        {loading && <LoadingSkeleton rows={5} />}

        {!loading && error && (
          <div className="space-y-3">
            <Alert variant="error">{error}</Alert>
            <button
              type="button"
              onClick={() => void loadMembers()}
              className="rounded-xl border border-slate-700 bg-slate-800 px-4 py-2 text-sm font-bold text-white hover:bg-slate-700"
            >
              Tekrar dene
            </button>
          </div>
        )}

        {!loading && !error && members.length === 0 && (
          <EmptyState
            title={
              isAssignmentScoped
                ? 'Size atanmış üye yok'
                : 'Kayıtlı üye bulunmuyor'
            }
            description={
              isAssignmentScoped
                ? 'Kulüp yöneticiniz size üye atadığında burada görünecekler.'
                : 'Üye kaydı yapıldığında burada listelenir.'
            }
          />
        )}

        {!loading && !error && members.length > 0 && (
          <div className="grid gap-6 lg:grid-cols-[320px_1fr]">
            <section
              aria-label="Üye listesi"
              className="rounded-2xl border border-slate-800 bg-slate-900 p-3"
            >
              <ul className="divide-y divide-slate-800/70">
                {members.map((member) => (
                  <li key={member.id}>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedId(member.id)
                        setCheckResult(null)
                        setCheckError(null)
                      }}
                      aria-current={member.id === selectedId}
                      className={`w-full rounded-xl px-3 py-3 text-left transition-colors ${
                        member.id === selectedId
                          ? 'bg-slate-800'
                          : 'hover:bg-slate-800/50'
                      }`}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-semibold text-white">
                          {member.first_name} {member.last_name}
                        </span>
                        <StatusBadge status={member.status} kind="member" />
                      </div>
                      <span className="text-xs text-slate-500">
                        {member.member_number}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </section>

            <section
              aria-label="Üye detayı"
              className="rounded-2xl border border-slate-800 bg-slate-900 p-5"
            >
              {!selected ? (
                <EmptyState
                  title="Üye seçin"
                  description="Giriş geçmişini ve hak durumunu görmek için soldan bir üye seçin."
                />
              ) : (
                <>
                  <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h2 className="text-lg font-bold text-white">
                        {selected.first_name} {selected.last_name}
                      </h2>
                      <p className="text-xs text-slate-500">
                        {selected.member_number}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => void handleCheckEntitlement(selected.id)}
                      disabled={checking}
                      className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-bold text-white hover:bg-emerald-500 disabled:opacity-50"
                    >
                      {checking ? 'Kontrol ediliyor…' : 'Giriş hakkını kontrol et'}
                    </button>
                  </div>

                  {checkError && <Alert variant="error">{checkError}</Alert>}

                  {checkResult && (
                    <Alert variant={checkResult.granted ? 'success' : 'error'}>
                      {checkResult.granted
                        ? `Giriş hakkı var${
                            checkResult.remaining !== null
                              ? ` · kalan: ${checkResult.remaining}`
                              : ''
                          }`
                        : `Giriş hakkı yok${
                            checkResult.reason ? ` · ${checkResult.reason}` : ''
                          }`}
                    </Alert>
                  )}

                  <h3 className="mb-1 mt-6 text-sm font-bold text-slate-300">
                    Turnike giriş geçmişi
                  </h3>
                  <MemberAccessLogs memberId={selected.id} />
                </>
              )}
            </section>
          </div>
        )}
      </div>
    </div>
  )
}
