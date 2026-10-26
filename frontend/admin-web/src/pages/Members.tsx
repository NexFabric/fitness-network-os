import { useCallback, useEffect, useMemo, useState, type FormEvent } from 'react'
import { api, ApiError } from '../api/client'
import MemberMemberships from '../components/MemberMemberships'
import MemberAccessLogs from '../components/MemberAccessLogs'
import {
  Alert,
  EmptyState,
  LoadingSkeleton,
  PageHeader,
  StatusBadge,
} from '../components/ui'

type Member = {
  id: string
  member_number: string
  first_name: string
  last_name: string
  email: string | null
  phone: string | null
  status: string
  user_id: string | null
}

type PortalAccount = {
  member_id: string
  user_id: string
  email: string
  invite_token?: string | null
}

type CreateMemberForm = {
  member_number: string
  first_name: string
  last_name: string
}

type EditMemberForm = {
  first_name: string
  last_name: string
  email: string
  phone: string
  status: string
}

const emptyForm: CreateMemberForm = {
  member_number: '',
  first_name: '',
  last_name: '',
}

function formatApiError(e: unknown, fallback: string): string {
  if (e instanceof ApiError) {
    return `${e.status}: ${e.message}`
  }
  if (e instanceof Error) return e.message
  return fallback
}

function generateMemberNumber(existing: Member[]): string {
  const nums = existing
    .map((m) => {
      const match = m.member_number.match(/\d+/)
      return match ? parseInt(match[0], 10) : 0
    })
    .filter((n) => !isNaN(n))
  const max = nums.length > 0 ? Math.max(...nums) : 100
  return `MEM-${max + 1}`
}

export default function Members() {
  const [members, setMembers] = useState<Member[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [showCreate, setShowCreate] = useState(false)

  const [form, setForm] = useState<CreateMemberForm>(emptyForm)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const [formSuccess, setFormSuccess] = useState<string | null>(null)

  const [editingMember, setEditingMember] = useState<Member | null>(null)
  const [editForm, setEditForm] = useState<EditMemberForm | null>(null)
  const [editSubmitting, setEditSubmitting] = useState(false)
  const [editError, setEditError] = useState<string | null>(null)
  const [portalBusy, setPortalBusy] = useState(false)
  const [portalError, setPortalError] = useState<string | null>(null)
  const [portalAccount, setPortalAccount] = useState<PortalAccount | null>(null)
  const [portalCopied, setPortalCopied] = useState(false)

  const loadMembers = useCallback(async (opts?: { silent?: boolean }) => {
    const silent = opts?.silent ?? false
    if (!silent) {
      setLoading(true)
      setError(null)
    }
    try {
      const data = await api<Member[]>('/api/v1/members')
      setMembers(data)
      if (silent) setError(null)
    } catch (e) {
      setError(formatApiError(e, 'Üyeler yüklenemedi'))
    } finally {
      if (!silent) setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadMembers()
  }, [loadMembers])

  const toggleCreate = () => {
    const next = !showCreate
    setShowCreate(next)
    if (next && !form.member_number) {
      setForm((f) => ({ ...f, member_number: generateMemberNumber(members) }))
    }
  }

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return members
    return members.filter((m) => {
      const hay = `${m.member_number} ${m.first_name} ${m.last_name} ${m.email ?? ''}`.toLowerCase()
      return hay.includes(q)
    })
  }, [members, query])

  async function handleCreate(e: FormEvent) {
    e.preventDefault()
    setFormError(null)
    setFormSuccess(null)

    const member_number = form.member_number.trim() || generateMemberNumber(members)
    const first_name = form.first_name.trim()
    const last_name = form.last_name.trim()

    if (!first_name || !last_name) {
      setFormError('Ad ve Soyad alanları zorunludur.')
      return
    }

    setSubmitting(true)
    try {
      await api<Member>('/api/v1/members', {
        method: 'POST',
        body: { member_number, first_name, last_name },
      })
      setForm(emptyForm)
      setFormSuccess('Üye başarıyla oluşturuldu.')
      await loadMembers({ silent: true })
    } catch (err) {
      setFormError(formatApiError(err, 'Üye oluşturulamadı'))
    } finally {
      setSubmitting(false)
    }
  }

  function openEditModal(member: Member) {
    setEditingMember(member)
    setEditForm({
      first_name: member.first_name,
      last_name: member.last_name,
      email: member.email || '',
      phone: member.phone || '',
      status: member.status,
    })
    setEditError(null)
  }

  function closeEditModal() {
    setEditingMember(null)
    setEditForm(null)
    setPortalAccount(null)
    setPortalError(null)
    setPortalCopied(false)
  }

  async function provisionPortalAccount() {
    if (!editingMember) return
    if (!editingMember.email && !editForm?.email.trim()) {
      setPortalError('Önce üyeye bir e-posta kaydedin.')
      return
    }
    setPortalBusy(true)
    setPortalError(null)
    try {
      if (editForm && editForm.email.trim() && editForm.email.trim() !== (editingMember.email ?? '')) {
        await api<Member>(`/api/v1/members/${editingMember.id}`, {
          method: 'PATCH',
          body: { email: editForm.email.trim() },
        })
      }
      const created = await api<PortalAccount>(
        `/api/v1/members/${editingMember.id}/portal-account`,
        { method: 'POST' },
      )
      setPortalAccount(created)
      setEditingMember((m) => (m ? { ...m, user_id: created.user_id, email: created.email } : m))
    } catch (err) {
      setPortalError(formatApiError(err, 'Portal hesabı açılamadı'))
    } finally {
      setPortalBusy(false)
    }
  }

  async function handleEditSubmit(e: FormEvent) {
    e.preventDefault()
    if (!editingMember || !editForm) return

    const first_name = editForm.first_name.trim()
    const last_name = editForm.last_name.trim()
    const email = editForm.email.trim() || null
    const phone = editForm.phone.trim() || null

    if (!first_name || !last_name) {
      setEditError('Ad ve Soyad gereklidir.')
      return
    }

    setEditSubmitting(true)
    setEditError(null)
    try {
      // 1. Update basic fields
      await api<Member>(`/api/v1/members/${editingMember.id}`, {
        method: 'PATCH',
        body: { first_name, last_name, email, phone },
      })

      // 2. Update status if changed
      if (editForm.status !== editingMember.status) {
        await api<Member>(`/api/v1/members/${editingMember.id}/status`, {
          method: 'POST',
          body: { status: editForm.status },
        })
      }

      closeEditModal()
      await loadMembers({ silent: true })
    } catch (err) {
      setEditError(formatApiError(err, 'Üye güncellenemedi'))
    } finally {
      setEditSubmitting(false)
    }
  }

  return (
    <div>
      <PageHeader
        title="Üyeler"
        subtitle="Bu salonun üye listesi — oluşturun, arayın ve düzenleyin"
        actions={
          <button
            type="button"
            className="btn-primary"
            onClick={toggleCreate}
          >
            {showCreate ? 'Formu gizle' : 'Üye oluştur'}
          </button>
        }
      />

      <div className="mt-6">
        <label htmlFor="member-search" className="sr-only">
          Üye ara
        </label>
        <input
          id="member-search"
          type="search"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="İsim, numara veya e-posta ara…"
          className="input-field !mt-0 max-w-md"
        />
      </div>

      {showCreate && (
      <section className="card mt-6" aria-labelledby="create-member-heading">
        <div className="card-header">
          <h2
            id="create-member-heading"
            className="text-base font-semibold text-slate-100"
          >
            Üye oluştur
          </h2>
        </div>
        <form
          className="mt-4 grid gap-4 sm:grid-cols-3"
          onSubmit={handleCreate}
          noValidate
        >
          <div>
            <label htmlFor="member_number" className="label-text">
              Üye Numarası <span className="text-xs text-ink-muted font-normal">(Otomatik)</span>
            </label>
            <input
              id="member_number"
              name="member_number"
              type="text"
              maxLength={64}
              autoComplete="off"
              placeholder="Otomatik üretilir (örn. MEM-104)"
              value={form.member_number}
              onChange={(ev) =>
                setForm((f) => ({ ...f, member_number: ev.target.value }))
              }
              className="input-field"
              disabled={submitting}
            />
          </div>
          <div>
            <label htmlFor="first_name" className="label-text">
              Ad <span className="text-teal-500">*</span>
            </label>
            <input
              id="first_name"
              name="first_name"
              type="text"
              required
              maxLength={128}
              autoComplete="given-name"
              value={form.first_name}
              onChange={(ev) =>
                setForm((f) => ({ ...f, first_name: ev.target.value }))
              }
              className="input-field"
              disabled={submitting}
            />
          </div>
          <div>
            <label htmlFor="last_name" className="label-text">
              Soyad <span className="text-teal-500">*</span>
            </label>
            <input
              id="last_name"
              name="last_name"
              type="text"
              required
              maxLength={128}
              autoComplete="family-name"
              value={form.last_name}
              onChange={(ev) =>
                setForm((f) => ({ ...f, last_name: ev.target.value }))
              }
              className="input-field"
              disabled={submitting}
            />
          </div>
          <div className="flex flex-wrap items-center gap-3 sm:col-span-3">
            <button type="submit" disabled={submitting} className="btn-primary">
              {submitting ? 'Oluşturuluyor…' : 'Üye oluştur'}
            </button>
            {formError && (
              <p className="text-sm text-rose-400" role="alert">
                {formError}
              </p>
            )}
            {formSuccess && (
              <p className="text-sm font-medium text-emerald-400" role="status">
                {formSuccess}
              </p>
            )}
          </div>
        </form>
      </section>
      )}

      {loading && (
        <div className="table-shell mt-6">
          <LoadingSkeleton rows={5} />
        </div>
      )}

      {error && (
        <div className="mt-6">
          <Alert onRetry={() => void loadMembers()}>{error}</Alert>
        </div>
      )}

      {!loading && !error && (
        <div className="table-shell mt-6">
          <table className="min-w-full divide-y divide-slate-800 text-left">
            <thead className="bg-slate-900/80 backdrop-blur-md">
              <tr>
                <th className="table-th">Numara</th>
                <th className="table-th">İsim</th>
                <th className="table-th">E-posta</th>
                <th className="table-th">Durum</th>
                <th className="table-th">İşlemler</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={5}>
                    <EmptyState
                      title={members.length === 0 ? 'Henüz üye yok' : 'Sonuç bulunamadı'}
                      description={
                        members.length === 0
                          ? 'İlk üyeyi oluşturarak başlayın.'
                          : 'Arama kriterlerinizi değiştirin.'
                      }
                      actionLabel={members.length === 0 ? 'Üye oluştur' : undefined}
                      onAction={
                        members.length === 0
                          ? () => setShowCreate(true)
                          : undefined
                      }
                    />
                  </td>
                </tr>
              ) : (
                filtered.map((m) => (
                  <tr key={m.id} className="transition-colors hover:bg-slate-800/50">
                    <td className="table-td font-mono text-xs text-slate-400">
                      {m.member_number}
                    </td>
                    <td className="table-td font-medium text-slate-200">
                      {m.first_name} {m.last_name}
                    </td>
                    <td className="table-td text-slate-400">
                      {m.email ?? '—'}
                    </td>
                    <td className="table-td">
                      <StatusBadge status={m.status} kind="member" />
                    </td>
                    <td className="table-td text-right">
                      <button
                        type="button"
                        onClick={() => openEditModal(m)}
                        className="text-sm font-medium text-brand transition-colors hover:text-brand-light"
                      >
                        Düzenle
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Edit Modal */}
      {editingMember && editForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
            <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
              <h2 className="text-lg font-semibold text-slate-100">
                Üye Detayı: <span className="text-brand">{editingMember.member_number}</span>
              </h2>
              <button 
                onClick={closeEditModal}
                className="text-slate-400 hover:text-white transition-colors"
              >
                Kapat
              </button>
            </div>
            
            <div className="p-6 overflow-y-auto flex-1 flex flex-col gap-8">
              {/* Profil Düzenleme Formu */}
              <form onSubmit={handleEditSubmit} className="flex flex-col gap-4">
                <h3 className="text-sm font-medium text-slate-300 border-b border-slate-800 pb-2">Profil Bilgileri</h3>
                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="edit_first_name" className="label-text">Ad <span className="text-teal-500">*</span></label>
                    <input
                      id="edit_first_name"
                      type="text"
                      required
                      maxLength={128}
                      value={editForm.first_name}
                      onChange={(e) => setEditForm({ ...editForm, first_name: e.target.value })}
                      className="input-field"
                      disabled={editSubmitting}
                    />
                  </div>
                  <div>
                    <label htmlFor="edit_last_name" className="label-text">Soyad <span className="text-teal-500">*</span></label>
                    <input
                      id="edit_last_name"
                      type="text"
                      required
                      maxLength={128}
                      value={editForm.last_name}
                      onChange={(e) => setEditForm({ ...editForm, last_name: e.target.value })}
                      className="input-field"
                      disabled={editSubmitting}
                    />
                  </div>
                </div>

                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="edit_email" className="label-text">E-posta</label>
                    <input
                      id="edit_email"
                      type="email"
                      maxLength={128}
                      value={editForm.email}
                      onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                      className="input-field"
                      disabled={editSubmitting}
                    />
                  </div>
                  <div>
                    <label htmlFor="edit_phone" className="label-text">Telefon</label>
                    <input
                      id="edit_phone"
                      type="text"
                      maxLength={32}
                      value={editForm.phone}
                      onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                      className="input-field"
                      disabled={editSubmitting}
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="edit_status" className="label-text">Durum</label>
                  <select
                    id="edit_status"
                    value={editForm.status}
                    onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
                    className="input-field"
                    disabled={editSubmitting}
                  >
                    <option value="ACTIVE">ACTIVE</option>
                    <option value="INACTIVE">INACTIVE</option>
                    <option value="SUSPENDED">SUSPENDED</option>
                    <option value="CANCELED">CANCELED</option>
                    <option value="LEAD">LEAD</option>
                  </select>
                </div>

                {editError && (
                  <div className="rounded-control border border-rose-800/80 bg-rose-950/50 px-4 py-3 text-sm text-rose-300 mt-2">
                    {editError}
                  </div>
                )}

                <div className="mt-2 flex justify-end gap-3">
                  <button 
                    type="submit" 
                    disabled={editSubmitting} 
                    className="btn-primary"
                  >
                    {editSubmitting ? 'Kaydediliyor...' : 'Profili Kaydet'}
                  </button>
                </div>
              </form>

              <div>
                <h3 className="text-sm font-medium text-slate-300 border-b border-slate-800 pb-2">
                  Sporcu portalı
                </h3>
                {editingMember.user_id && !portalAccount ? (
                  <p className="mt-3 text-sm text-slate-400">
                    Bu üye bir giriş hesabına bağlı.
                    <span className="ml-2 font-mono text-xs text-slate-500">
                      {editingMember.user_id}
                    </span>
                  </p>
                ) : (
                  <p className="mt-3 text-sm text-slate-400">
                    E-posta kaydı olan üyeye tek kullanımlık parolalı MEMBER hesabı açılır.
                    Parola yalnızca bir kez gösterilir.
                  </p>
                )}
                {portalError && (
                  <p className="mt-2 text-sm text-rose-400" role="alert">
                    {portalError}
                  </p>
                )}
                {portalAccount && (
                  <div className="mt-3 rounded-control border border-emerald-800/60 bg-emerald-950/40 px-4 py-3 text-sm text-emerald-200">
                    <p>
                      Hesap: <span className="font-mono">{portalAccount.email}</span>
                    </p>
                    <p className="mt-1">
                      Davet jetonu:{' '}
                      <span className="font-mono">{portalAccount.invite_token}</span>
                    </p>
                    <button
                      type="button"
                      className="mt-2 text-xs font-medium text-emerald-300 underline"
                      onClick={() => {
                        if (!portalAccount.invite_token) return
                        void navigator.clipboard.writeText(
                          `${window.location.origin}/invite?token=${portalAccount.invite_token}`,
                        )
                        setPortalCopied(true)
                      }}
                    >
                      {portalCopied ? 'Kopyalandı' : 'Davet bağlantısını kopyala'}
                    </button>
                    {portalAccount.invite_token && (
                      <p className="mt-2 text-xs break-all">
                        Davet:{' '}
                        <a
                          className="underline"
                          href={`/invite?token=${encodeURIComponent(portalAccount.invite_token)}`}
                        >
                          /invite
                        </a>
                      </p>
                    )}
                  </div>
                )}
                {!editingMember.user_id && !portalAccount && (
                  <button
                    type="button"
                    className="btn-primary mt-3"
                    disabled={portalBusy}
                    onClick={() => void provisionPortalAccount()}
                  >
                    {portalBusy ? 'Açılıyor…' : 'Portal hesabı aç'}
                  </button>
                )}
              </div>

              {/* Abonelikler Bölümü */}
              <div>
                <h3 className="text-sm font-medium text-slate-300 border-b border-slate-800 pb-2">Abonelikler</h3>
                <MemberMemberships memberId={editingMember.id} />
              </div>

              {/* Giriş-Çıkış Geçmişi Bölümü */}
              <div className="pt-2">
                <h3 className="text-sm font-medium text-slate-300 border-b border-slate-800 pb-2">Giriş - Çıkış Geçmişi</h3>
                <MemberAccessLogs memberId={editingMember.id} />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

