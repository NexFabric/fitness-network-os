import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api, ApiError, setAuth } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Alert, EmptyState, LoadingSkeleton, StatusBadge } from '../components/ui'

type TabKey = 'overview' | 'gyms' | 'passport' | 'compliance' | 'alerts' | 'reports'

type OrganizationSummary = {
  id: string
  name: string
  domain: string | null
}

type TenantSummary = {
  id: string
  name: string
  location_code: string
  organization_id: string
  status: 'ACTIVE' | 'SUSPENDED' | 'CLOSED'
  suspended_at?: string | null
  suspension_reason?: string | null
  member_count: number
  active_membership_count: number
  revenue_minor: number
}

type FederationSummary = {
  organization_count: number
  tenant_count: number
  active_tenant_count: number
  suspended_tenant_count: number
  member_count: number
  active_membership_count: number
  revenue_minor: number
  partial: boolean
}

type AuditEvent = {
  id: string
  tenant_id: string
  user_id: string | null
  action: string
  resource_type: string
  created_at: string
}

type PassportConfig = {
  id: string
  tenant_id: string
  is_active: boolean
  allowed_home_gym_tiers: string | null
  rules: {
    max_monthly_roaming_visits?: number
    guest_fee_minor?: number
  } | null
  updated_at?: string | null
}

type ComplianceRecord = {
  id: string
  tenant_id: string
  certification_name: string
  status: 'PASSED' | 'FAILED' | 'CONDITIONAL' | 'EXPIRED'
  audit_date: string
  auditor_notes?: string | null
  created_at: string
}

type NetworkAlert = {
  id: string
  organization_id: string
  target_tenant_id: string | null
  title: string
  message: string
  severity: 'INFO' | 'WARNING' | 'CRITICAL' | 'MAINTENANCE'
  created_at: string
}

type AnalyticsOverview = {
  total_checkins: number
  checkins_by_tenant: Record<string, number>
  total_revenue_minor: number
  revenue_by_tenant_minor: Record<string, number>
  partial: boolean
}

function formatMinor(minor: number): string {
  const major = Math.trunc(minor / 100)
  const cents = Math.abs(minor % 100)
    .toString()
    .padStart(2, '0')
  return `₺${major.toLocaleString('tr-TR')},${cents}`
}

function formatApiError(e: unknown, fallback: string): string {
  if (e instanceof ApiError) {
    if (e.status === 403) return 'Bu işlem için yetkiniz bulunmuyor.'
    return e.message
  }
  if (e instanceof Error) return e.message
  return fallback
}

export default function SuperAdminPortal() {
  const { session, refresh } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = (searchParams.get('tab') as TabKey) || 'overview'

  const setTab = (tab: TabKey) => {
    setSearchParams({ tab })
  }

  // Data states
  const [orgs, setOrgs] = useState<OrganizationSummary[]>([])
  const [tenants, setTenants] = useState<TenantSummary[]>([])
  const [summary, setSummary] = useState<FederationSummary | null>(null)
  const [audit, setAudit] = useState<AuditEvent[]>([])
  const [passports, setPassports] = useState<PassportConfig[]>([])
  const [compliance, setCompliance] = useState<ComplianceRecord[]>([])
  const [alerts, setAlerts] = useState<NetworkAlert[]>([])
  const [analytics, setAnalytics] = useState<AnalyticsOverview | null>(null)

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [switching, setSwitching] = useState<string | null>(null)

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'ACTIVE' | 'SUSPENDED'>('ALL')

  // Modals state
  const [showAddGymModal, setShowAddGymModal] = useState(false)
  const [newGymName, setNewGymName] = useState('')
  const [newGymCode, setNewGymCode] = useState('')
  const [newGymBranch, setNewGymBranch] = useState('')
  const [newGymAddress, setNewGymAddress] = useState('')
  const [newGymSubmitting, setNewGymSubmitting] = useState(false)
  const [newGymError, setNewGymError] = useState<string | null>(null)

  const [suspendTarget, setSuspendTarget] = useState<TenantSummary | null>(null)
  const [suspendReason, setSuspendReason] = useState('')
  const [suspendSubmitting, setSuspendSubmitting] = useState(false)
  const [suspendError, setSuspendError] = useState<string | null>(null)

  const [breakGlassTarget, setBreakGlassTarget] = useState<TenantSummary | null>(null)
  const [bgReason, setBgReason] = useState('')
  const [bgTicket, setBgTicket] = useState('')
  const [bgDuration, setBgDuration] = useState(30)
  const [bgSubmitting, setBgSubmitting] = useState(false)
  const [bgError, setBgError] = useState<string | null>(null)

  const [passportTarget, setPassportTarget] = useState<TenantSummary | null>(null)
  const [passportActive, setPassportActive] = useState(true)
  const [passportTiers, setPassportTiers] = useState('VIP,GOLD')
  const [passportMaxVisits, setPassportMaxVisits] = useState(5)
  const [passportFeeMinor, setPassportFeeMinor] = useState(0)
  const [passportSubmitting, setPassportSubmitting] = useState(false)
  const [passportError, setPassportError] = useState<string | null>(null)

  const [showComplianceModal, setShowComplianceModal] = useState(false)
  const [compTenantId, setCompTenantId] = useState('')
  const [compCertName, setCompCertName] = useState('')
  const [compStatus, setCompStatus] = useState<'PASSED' | 'CONDITIONAL' | 'FAILED'>('PASSED')
  const [compNotes, setCompNotes] = useState('')
  const [compSubmitting, setCompSubmitting] = useState(false)
  const [compError, setCompError] = useState<string | null>(null)

  const [showAlertModal, setShowAlertModal] = useState(false)
  const [alertTitle, setAlertTitle] = useState('')
  const [alertMessage, setAlertMessage] = useState('')
  const [alertSeverity, setAlertSeverity] = useState<'INFO' | 'WARNING' | 'CRITICAL' | 'MAINTENANCE'>('INFO')
  const [alertTargetTenant, setAlertTargetTenant] = useState<string>('')
  const [alertSubmitting, setAlertSubmitting] = useState(false)
  const [alertError, setAlertError] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [
        orgRows,
        tenantRows,
        summaryRow,
        auditRows,
        passportRows,
        complianceRows,
        alertRows,
        analyticsRow,
      ] = await Promise.all([
        api<OrganizationSummary[]>('/api/v1/admin/organizations'),
        api<TenantSummary[]>('/api/v1/admin/tenants?limit=50'),
        api<FederationSummary>('/api/v1/admin/federation/summary'),
        api<AuditEvent[]>('/api/v1/admin/audit?tenant_limit=10&limit_per_tenant=5'),
        api<PassportConfig[]>('/api/v1/admin/passport/configs').catch(() => []),
        api<ComplianceRecord[]>('/api/v1/admin/compliance').catch(() => []),
        api<NetworkAlert[]>('/api/v1/admin/alerts').catch(() => []),
        api<AnalyticsOverview>('/api/v1/admin/analytics/overview').catch(() => null),
      ])

      setOrgs(orgRows)
      setTenants(tenantRows)
      setSummary(summaryRow)
      setAudit(auditRows)
      setPassports(passportRows)
      setCompliance(complianceRows)
      setAlerts(alertRows)
      setAnalytics(analyticsRow)

      if (tenantRows.length > 0 && !compTenantId) {
        setCompTenantId(tenantRows[0].id)
      }
    } catch (err) {
      setError(formatApiError(err, 'Federasyon verileri yüklenemedi. Birkaç saniye sonra tekrar deneyin.'))
    } finally {
      setLoading(false)
    }
  }, [compTenantId])

  useEffect(() => {
    void loadData()
  }, [loadData])

  async function enterTenant(tenantId: string) {
    setSwitching(tenantId)
    setAuth(tenantId)
    await refresh()
    window.location.assign('/')
  }

  // Action: Create Gym
  async function handleCreateGym(e: FormEvent) {
    e.preventDefault()
    if (!orgs[0]) return
    setNewGymSubmitting(true)
    setNewGymError(null)
    try {
      await api('/api/v1/admin/tenants', {
        method: 'POST',
        body: {
          organization_id: orgs[0].id,
          name: newGymName.trim(),
          location_code: newGymCode.trim().toUpperCase(),
          initial_branch_name: newGymBranch.trim() || undefined,
          initial_branch_address: newGymAddress.trim() || undefined,
        },
      })
      setShowAddGymModal(false)
      setNewGymName('')
      setNewGymCode('')
      setNewGymBranch('')
      setNewGymAddress('')
      setSuccessMessage('Yeni kulüp ve ana şubesi başarıyla oluşturuldu.')
      void loadData()
    } catch (err) {
      setNewGymError(formatApiError(err, 'Kulüp oluşturulamadı.'))
    } finally {
      setNewGymSubmitting(false)
    }
  }

  // Action: Suspend Gym
  async function handleSuspendGym(e: FormEvent) {
    e.preventDefault()
    if (!suspendTarget) return
    setSuspendSubmitting(true)
    setSuspendError(null)
    try {
      await api(`/api/v1/admin/tenants/${suspendTarget.id}/suspend`, {
        method: 'POST',
        body: { reason: suspendReason.trim() },
      })
      setSuspendTarget(null)
      setSuspendReason('')
      setSuccessMessage(`${suspendTarget.name} kulübü askıya alındı. Turnike erişimleri durduruldu.`)
      void loadData()
    } catch (err) {
      setSuspendError(formatApiError(err, 'Kulüp askıya alınamadı.'))
    } finally {
      setSuspendSubmitting(false)
    }
  }

  // Action: Reactivate Gym
  async function handleReactivateGym(t: TenantSummary) {
    try {
      await api(`/api/v1/admin/tenants/${t.id}/reactivate`, { method: 'POST' })
      setSuccessMessage(`${t.name} kulübü yeniden aktifleştirildi.`)
      void loadData()
    } catch (err) {
      setError(formatApiError(err, 'Kulüp aktifleştirilemedi.'))
    }
  }

  // Action: Break Glass
  async function handleBreakGlass(e: FormEvent) {
    e.preventDefault()
    if (!breakGlassTarget) return
    setBgSubmitting(true)
    setBgError(null)
    try {
      await api('/api/v1/break-glass/sessions', {
        method: 'POST',
        body: {
          target_tenant_id: breakGlassTarget.id,
          reason: bgReason.trim(),
          ticket_reference: bgTicket.trim(),
          duration_minutes: Number(bgDuration),
        },
      })
      setAuth(breakGlassTarget.id)
      await refresh()
      window.location.assign('/')
    } catch (err) {
      setBgError(formatApiError(err, 'Acil durum oturumu başlatılamadı.'))
    } finally {
      setBgSubmitting(false)
    }
  }

  // Action: Update Passport
  async function handleUpdatePassport(e: FormEvent) {
    e.preventDefault()
    if (!passportTarget) return
    setPassportSubmitting(true)
    setPassportError(null)
    try {
      await api(`/api/v1/admin/tenants/${passportTarget.id}/passport`, {
        method: 'PUT',
        body: {
          is_active: passportActive,
          allowed_home_gym_tiers: passportTiers,
          rules: {
            max_monthly_roaming_visits: Number(passportMaxVisits),
            guest_fee_minor: Number(passportFeeMinor) * 100,
          },
        },
      })
      setPassportTarget(null)
      setSuccessMessage(`${passportTarget.name} federasyon pasaport ayarları güncellendi.`)
      void loadData()
    } catch (err) {
      setPassportError(formatApiError(err, 'Pasaport ayarları kaydedilemedi.'))
    } finally {
      setPassportSubmitting(false)
    }
  }

  // Action: Add Compliance
  async function handleAddCompliance(e: FormEvent) {
    e.preventDefault()
    if (!compTenantId) return
    setCompSubmitting(true)
    setCompError(null)
    try {
      await api(`/api/v1/admin/tenants/${compTenantId}/compliance`, {
        method: 'POST',
        body: {
          certification_name: compCertName.trim(),
          status: compStatus,
          auditor_notes: compNotes.trim() || undefined,
        },
      })
      setShowComplianceModal(false)
      setCompCertName('')
      setCompNotes('')
      setSuccessMessage('Denetim muayene kaydı başarıyla eklendi.')
      void loadData()
    } catch (err) {
      setCompError(formatApiError(err, 'Denetim kaydı eklenemedi.'))
    } finally {
      setCompSubmitting(false)
    }
  }

  // Action: Create Alert
  async function handleCreateAlert(e: FormEvent) {
    e.preventDefault()
    if (!orgs[0]) return
    setAlertSubmitting(true)
    setAlertError(null)
    try {
      await api('/api/v1/admin/alerts', {
        method: 'POST',
        body: {
          organization_id: orgs[0].id,
          title: alertTitle.trim(),
          message: alertMessage.trim(),
          severity: alertSeverity,
          target_tenant_id: alertTargetTenant || undefined,
        },
      })
      setShowAlertModal(false)
      setAlertTitle('')
      setAlertMessage('')
      setAlertSeverity('INFO')
      setAlertTargetTenant('')
      setSuccessMessage('Ağ duyurusu başarıyla yayınlandı.')
      void loadData()
    } catch (err) {
      setAlertError(formatApiError(err, 'Duyuru yayınlanamadı.'))
    } finally {
      setAlertSubmitting(false)
    }
  }

  // Action: Delete Alert
  async function handleDeleteAlert(id: string) {
    try {
      await api(`/api/v1/admin/alerts/${id}`, { method: 'DELETE' })
      setSuccessMessage('Duyuru yayından kaldırıldı.')
      void loadData()
    } catch (err) {
      setError(formatApiError(err, 'Duyuru silinemedi.'))
    }
  }

  // CSV Export
  function exportCSV() {
    if (tenants.length === 0) return
    const headers = ['Kulüp Adı', 'Lokasyon Kodu', 'Durum', 'Üye Sayısı', 'Aktif Abonelik', 'Toplam Gelir (₺)', 'Turnike Giriş']
    const rows = tenants.map((t) => [
      `"${t.name}"`,
      `"${t.location_code}"`,
      `"${t.status}"`,
      t.member_count,
      t.active_membership_count,
      (t.revenue_minor / 100).toFixed(2),
      analytics?.checkins_by_tenant[t.id] ?? 0,
    ])
    const csvContent = 'data:text/csv;charset=utf-8,\uFEFF' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n')
    const encodedUri = encodeURI(csvContent)
    const link = document.createElement('a')
    link.setAttribute('href', encodedUri)
    link.setAttribute('download', `federasyon_ag_raporu_${new Date().toISOString().slice(0, 10)}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const filteredTenants = tenants.filter((t) => {
    const matchesSearch =
      t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      t.location_code.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesStatus = statusFilter === 'ALL' || t.status === statusFilter
    return matchesSearch && matchesStatus
  })

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-8 text-slate-100 font-sans">
      <div className="mx-auto w-full max-w-7xl">
        {/* Header */}
        <header className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-500/10 text-xl text-teal-400 border border-teal-500/20">
                👑
              </span>
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-2xl font-extrabold tracking-tight text-white">
                      Federasyon Konsolu
                    </h1>
                    <span className="rounded-lg bg-teal-500/10 px-2.5 py-0.5 text-xs font-bold text-teal-400 border border-teal-500/20">
                      Ağ & HQ
                    </span>
                  </div>
                  <p className="mt-0.5 text-xs text-slate-400">
                    {orgs[0]?.name ?? 'Demo Organization'} · {session?.email}
                    {session?.is_superuser && ' · Platform Süper Yöneticisi'}
                  </p>
                </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/portal"
              className="rounded-xl border border-slate-700 bg-slate-900/80 px-4 py-2 text-xs font-semibold text-slate-300 hover:bg-slate-800 transition"
            >
              ← Portallara Dön
            </Link>
          </div>
        </header>

        {/* Global Alerts Banner */}
        {alerts.length > 0 && (
          <div className="mb-6 space-y-2">
            {alerts.slice(0, 2).map((a) => {
              const bg =
                a.severity === 'CRITICAL'
                  ? 'bg-rose-950/60 border-rose-800 text-rose-300'
                  : a.severity === 'WARNING'
                    ? 'bg-amber-950/60 border-amber-800 text-amber-300'
                    : a.severity === 'MAINTENANCE'
                      ? 'bg-purple-950/60 border-purple-800 text-purple-300'
                      : 'bg-teal-950/60 border-teal-800 text-teal-300'
              return (
                <div
                  key={a.id}
                  className={`flex flex-wrap items-center justify-between gap-3 rounded-xl border px-4 py-2.5 text-xs font-medium ${bg}`}
                >
                  <div className="flex items-center gap-2">
                    <span className="font-bold uppercase tracking-wider">[{a.severity}]</span>
                    <span>
                      <strong className="text-white">{a.title}:</strong> {a.message}
                    </span>
                  </div>
                  <span className="text-[10px] text-slate-400">
                    {new Date(a.created_at).toLocaleString('tr-TR')}
                  </span>
                </div>
              )
            })}
          </div>
        )}

        {successMessage && (
          <div className="mb-6 flex items-center justify-between gap-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-xs font-semibold text-emerald-400">
            <span>{successMessage}</span>
            <button
              type="button"
              onClick={() => setSuccessMessage(null)}
              className="text-slate-400 hover:text-white"
            >
              ✕
            </button>
          </div>
        )}

        {error && (
          <div className="mb-6 flex items-center justify-between gap-3 rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-xs font-semibold text-rose-400">
            <span>{error}</span>
            <button
              type="button"
              onClick={() => setError(null)}
              className="text-slate-400 hover:text-white"
            >
              ✕
            </button>
          </div>
        )}

        {/* Navigation Tabs */}
        <nav className="mb-6 flex flex-wrap gap-2 border-b border-slate-800 pb-2">
          {[
            { key: 'overview', label: '🌐 Genel Bakış', count: undefined },
            { key: 'gyms', label: '🏢 Kulüpler & Salonlar', count: tenants.length },
            { key: 'passport', label: '🛂 Federasyon Pasaportu', count: passports.filter((p) => p.is_active).length },
            { key: 'compliance', label: '🛡️ Uyumluluk & Denetim', count: compliance.length },
            { key: 'alerts', label: '📢 Ağ Duyuruları', count: alerts.length },
            { key: 'reports', label: '📈 Raporlar & Analitik', count: undefined },
          ].map((tab) => {
            const isActive = activeTab === tab.key
            return (
              <button
                key={tab.key}
                type="button"
                onClick={() => setTab(tab.key as TabKey)}
                className={`flex items-center gap-2 rounded-xl px-4 py-2.5 text-xs font-bold transition ${
                  isActive
                    ? 'bg-teal-500/15 text-teal-400 border border-teal-500/30'
                    : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200 border border-transparent'
                }`}
              >
                <span>{tab.label}</span>
                {tab.count !== undefined && (
                  <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] text-slate-400">
                    {tab.count}
                  </span>
                )}
              </button>
            )
          })}
        </nav>

        {loading ? (
          <LoadingSkeleton rows={6} />
        ) : (
          <>
            {/* =========================================================================
                TAB 1: GENEL BAKIŞ
               ========================================================================= */}
            {activeTab === 'overview' && summary && (
              <div className="space-y-6">
                <section aria-label="Ağ Geneli KPI'lar" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-sm">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Toplam Kulüp (Tenant)
                    </span>
                    <div className="mt-2 flex items-baseline gap-2">
                      <span className="text-3xl font-extrabold text-white">{summary.tenant_count}</span>
                      <span className="text-xs text-emerald-400 font-semibold">({summary.active_tenant_count} Aktif)</span>
                      {summary.suspended_tenant_count > 0 && (
                        <span className="text-xs text-rose-400 font-semibold">({summary.suspended_tenant_count} Askıda)</span>
                      )}
                    </div>
                    <p className="mt-1 text-[11px] text-slate-500">Federasyona bağlı lisanslı kulüpler</p>
                  </div>

                  <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-sm">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Ağ Geneli Toplam Üye
                    </span>
                    <div className="mt-2 text-3xl font-extrabold text-teal-400">
                      {summary.member_count.toLocaleString('tr-TR')}
                    </div>
                    <p className="mt-1 text-[11px] text-slate-500">Kayıtlı tekil sporcu sayısı</p>
                  </div>

                  <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-sm">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Aktif Turnike Aboneliği
                    </span>
                    <div className="mt-2 text-3xl font-extrabold text-emerald-400">
                      {summary.active_membership_count.toLocaleString('tr-TR')}
                    </div>
                    <p className="mt-1 text-[11px] text-slate-500">Geçiş yetkisi olan aktif paketler</p>
                  </div>

                  <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-sm">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Tahsil Edilen Ağ Cirosu
                    </span>
                    <div className="mt-2 text-3xl font-extrabold text-white">
                      {formatMinor(summary.revenue_minor)}
                    </div>
                    <p className="mt-1 text-[11px] text-slate-500">Tüm kulüplerin konsolide tahsilatı</p>
                  </div>
                </section>

                <div className="grid gap-6 lg:grid-cols-2">
                  {/* Hızlı Kulüp Durumu */}
                  <section className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5">
                    <div className="mb-4 flex items-center justify-between">
                      <h2 className="text-sm font-bold uppercase tracking-wide text-white">
                        🏢 Bağlı Kulüpler & Durumlar
                      </h2>
                      <button
                        type="button"
                        onClick={() => setTab('gyms')}
                        className="text-xs text-teal-400 hover:underline"
                      >
                        Tümünü Yönet ({tenants.length}) →
                      </button>
                    </div>
                    <div className="divide-y divide-slate-800/80 text-xs">
                      {tenants.slice(0, 5).map((t) => (
                        <div key={t.id} className="flex items-center justify-between py-3">
                          <div>
                            <span className="font-bold text-white">{t.name}</span>
                            <span className="ml-2 font-mono text-[11px] text-slate-500">[{t.location_code}]</span>
                            <div className="text-[11px] text-slate-400">
                              {t.member_count} üye · {t.active_membership_count} aktif abone · {formatMinor(t.revenue_minor)}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <StatusBadge status={t.status} />
                            <button
                              type="button"
                              onClick={() => void enterTenant(t.id)}
                              disabled={switching === t.id}
                              className="rounded-lg border border-slate-700 bg-slate-800 px-2.5 py-1 text-xs font-medium text-slate-200 hover:bg-slate-700 transition"
                            >
                              {switching === t.id ? 'Bağlanıyor…' : 'Kulübe Geç'}
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>

                  {/* Son Sistem ve Denetim Olayları */}
                  <section className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5">
                    <h2 className="mb-4 text-sm font-bold uppercase tracking-wide text-white">
                      📜 Son Sistem ve Audit Kayıtları
                    </h2>
                    {audit.length === 0 ? (
                      <EmptyState title="Audit kaydı yok" description="Henüz bir sistem olayı kaydedilmedi." />
                    ) : (
                      <ul className="divide-y divide-slate-800/80 text-xs">
                        {audit.slice(0, 6).map((event) => (
                          <li key={event.id} className="flex items-center justify-between py-2.5">
                            <span className="font-mono text-teal-400">{event.action}</span>
                            <span className="text-slate-500">
                              {event.resource_type} · {new Date(event.created_at).toLocaleString('tr-TR')}
                            </span>
                          </li>
                        ))}
                      </ul>
                    )}
                  </section>
                </div>
              </div>
            )}

            {/* =========================================================================
                TAB 2: KULÜPLER & SALONLAR (GYM DIRECTORY & LIFECYCLE)
               ========================================================================= */}
            {activeTab === 'gyms' && (
              <div className="space-y-6">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div className="flex flex-wrap items-center gap-3">
                    <input
                      type="text"
                      placeholder="Kulüp adı veya kod ile ara…"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-xs text-white placeholder-slate-500 focus:border-teal-500 focus:outline-none w-64"
                    />
                    <select
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value as 'ALL' | 'ACTIVE' | 'SUSPENDED')}
                      className="rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-300 focus:border-teal-500 focus:outline-none"
                    >
                      <option value="ALL">Tüm Durumlar</option>
                      <option value="ACTIVE">Yalnızca Aktif</option>
                      <option value="SUSPENDED">Yalnızca Askıda</option>
                    </select>
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowAddGymModal(true)}
                    className="rounded-xl bg-teal-600 px-4 py-2 text-xs font-bold text-white hover:bg-teal-500 transition shadow-sm"
                  >
                    + Yeni Kulüp Aç
                  </button>
                </div>

                <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/90">
                  <table className="min-w-full divide-y divide-slate-800 text-xs">
                    <thead>
                      <tr className="bg-slate-950/60 text-left text-slate-400 font-semibold">
                        <th className="px-4 py-3.5">Kulüp & Kod</th>
                        <th className="px-4 py-3.5">Durum</th>
                        <th className="px-4 py-3.5">Toplam Üye</th>
                        <th className="px-4 py-3.5">Aktif Abonelik</th>
                        <th className="px-4 py-3.5">Toplam Ciro</th>
                        <th className="px-4 py-3.5 text-right">Aksiyonlar</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/80 text-slate-300">
                      {filteredTenants.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="py-8 text-center text-slate-500">
                            Arama kriterine uygun kulüp bulunamadı.
                          </td>
                        </tr>
                      ) : (
                        filteredTenants.map((t) => (
                          <tr key={t.id} className="hover:bg-slate-800/40 transition">
                            <td className="px-4 py-3.5">
                              <div className="font-bold text-white">{t.name}</div>
                              <div className="font-mono text-[11px] text-slate-500">{t.location_code}</div>
                              {t.suspension_reason && (
                                <div className="mt-1 text-[10px] text-rose-400">
                                  Gerekçe: {t.suspension_reason}
                                </div>
                              )}
                            </td>
                            <td className="px-4 py-3.5">
                              <StatusBadge status={t.status} />
                            </td>
                            <td className="px-4 py-3.5 font-medium">{t.member_count}</td>
                            <td className="px-4 py-3.5 font-medium text-emerald-400">{t.active_membership_count}</td>
                            <td className="px-4 py-3.5 font-bold text-white">{formatMinor(t.revenue_minor)}</td>
                            <td className="px-4 py-3.5 text-right">
                              <div className="flex items-center justify-end gap-2">
                                <button
                                  type="button"
                                  onClick={() => void enterTenant(t.id)}
                                  disabled={switching === t.id}
                                  className="rounded-lg bg-teal-600/20 border border-teal-500/30 px-3 py-1 text-xs font-bold text-teal-300 hover:bg-teal-600/30 transition"
                                >
                                  {switching === t.id ? 'Bağlanıyor…' : 'Kulübe Geç'}
                                </button>
                                <button
                                  type="button"
                                  onClick={() => {
                                    setBreakGlassTarget(t)
                                    setBgReason('')
                                    setBgTicket('')
                                    setBgError(null)
                                  }}
                                  className="rounded-lg bg-purple-950/60 border border-purple-800/80 px-2.5 py-1 text-xs font-medium text-purple-300 hover:bg-purple-900/60 transition"
                                  title="Denetimli Acil Destek Girişi"
                                >
                                  Break-Glass
                                </button>
                                {t.status === 'ACTIVE' ? (
                                  <button
                                    type="button"
                                    onClick={() => {
                                      setSuspendTarget(t)
                                      setSuspendReason('')
                                      setSuspendError(null)
                                    }}
                                    className="rounded-lg bg-rose-950/60 border border-rose-800/80 px-2.5 py-1 text-xs font-medium text-rose-300 hover:bg-rose-900/60 transition"
                                  >
                                    Askıya Al
                                  </button>
                                ) : (
                                  <button
                                    type="button"
                                    onClick={() => void handleReactivateGym(t)}
                                    className="rounded-lg bg-emerald-950/60 border border-emerald-800/80 px-2.5 py-1 text-xs font-medium text-emerald-300 hover:bg-emerald-900/60 transition"
                                  >
                                    Yeniden Aç
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* =========================================================================
                TAB 3: FEDERASYON PASAPORTU (CROSS-CLUB ROAMING)
               ========================================================================= */}
            {activeTab === 'passport' && (
              <div className="space-y-6">
                <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5">
                  <div className="flex flex-wrap items-center justify-between gap-4">
                    <div>
                      <h2 className="text-sm font-bold uppercase tracking-wide text-white">
                        🛂 Federasyon Pasaportu ve Dolaşım Matrisi
                      </h2>
                      <p className="mt-1 text-xs text-slate-400">
                        Sporcuların kendi kayıtlı kulüpleri dışındaki federasyon salonlarına misafir olarak girebilme
                        kuralları ve mahsuplaşma ayarları.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/90">
                  <table className="min-w-full divide-y divide-slate-800 text-xs">
                    <thead>
                      <tr className="bg-slate-950/60 text-left text-slate-400 font-semibold">
                        <th className="px-4 py-3.5">Kulüp Adı</th>
                        <th className="px-4 py-3.5">Pasaport Durumu</th>
                        <th className="px-4 py-3.5">Kabul Edilen Paket Seviyeleri</th>
                        <th className="px-4 py-3.5">Aylık Misafir Giriş Limiti</th>
                        <th className="px-4 py-3.5">Ziyaret Başı Mahsuplaşma</th>
                        <th className="px-4 py-3.5 text-right">Aksiyon</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/80 text-slate-300">
                      {tenants.map((t) => {
                        const p = passports.find((cfg) => cfg.tenant_id === t.id)
                        return (
                          <tr key={t.id} className="hover:bg-slate-800/40 transition">
                            <td className="px-4 py-3.5 font-bold text-white">{t.name}</td>
                            <td className="px-4 py-3.5">
                              {p?.is_active ? (
                                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs font-semibold text-emerald-400 border border-emerald-500/20">
                                  Dolaşıma Açık
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 rounded-full bg-slate-800 px-2 py-0.5 text-xs font-semibold text-slate-400">
                                  Kapalı
                                </span>
                              )}
                            </td>
                            <td className="px-4 py-3.5 font-mono text-[11px] text-teal-300">
                              {p?.allowed_home_gym_tiers ?? 'VIP,GOLD'}
                            </td>
                            <td className="px-4 py-3.5 font-medium">
                              {p?.rules?.max_monthly_roaming_visits ?? 5} ziyaret / ay
                            </td>
                            <td className="px-4 py-3.5 font-medium text-amber-400">
                              {p?.rules?.guest_fee_minor ? formatMinor(p.rules.guest_fee_minor) : '₺0,00'}
                            </td>
                            <td className="px-4 py-3.5 text-right">
                              <button
                                type="button"
                                onClick={() => {
                                  setPassportTarget(t)
                                  setPassportActive(p?.is_active ?? true)
                                  setPassportTiers(p?.allowed_home_gym_tiers ?? 'VIP,GOLD')
                                  setPassportMaxVisits(p?.rules?.max_monthly_roaming_visits ?? 5)
                                  setPassportFeeMinor((p?.rules?.guest_fee_minor ?? 0) / 100)
                                  setPassportError(null)
                                }}
                                className="rounded-lg border border-slate-700 bg-slate-800 px-3 py-1 text-xs font-medium text-slate-200 hover:bg-slate-700 transition"
                              >
                                Kuralları Düzenle
                              </button>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* =========================================================================
                TAB 4: UYUMLULUK & DENETİM (COMPLIANCE & AUDITS)
               ========================================================================= */}
            {activeTab === 'compliance' && (
              <div className="space-y-6">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <h2 className="text-sm font-bold uppercase tracking-wide text-white">
                      🛡️ Federasyon Muayene, Kalite ve Sertifikasyon Kayıtları
                    </h2>
                    <p className="mt-1 text-xs text-slate-400">
                      TSE, ISO, Hijyen ve Antrenör Yeterlilik denetimlerinin resmi sicili.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setShowComplianceModal(true)
                      setCompCertName('')
                      setCompNotes('')
                      setCompError(null)
                    }}
                    className="rounded-xl bg-teal-600 px-4 py-2 text-xs font-bold text-white hover:bg-teal-500 transition shadow-sm"
                  >
                    + Yeni Denetim Kaydı Ekle
                  </button>
                </div>

                <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/90">
                  <table className="min-w-full divide-y divide-slate-800 text-xs">
                    <thead>
                      <tr className="bg-slate-950/60 text-left text-slate-400 font-semibold">
                        <th className="px-4 py-3.5">Kulüp</th>
                        <th className="px-4 py-3.5">Sertifika / Standart</th>
                        <th className="px-4 py-3.5">Sonuç Durumu</th>
                        <th className="px-4 py-3.5">Denetim Tarihi</th>
                        <th className="px-4 py-3.5">Denetçi Notları</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/80 text-slate-300">
                      {compliance.length === 0 ? (
                        <tr>
                          <td colSpan={5} className="py-8 text-center text-slate-500">
                            Henüz kayıtlı bir denetim veya sertifikasyon kaydı bulunmuyor.
                          </td>
                        </tr>
                      ) : (
                        compliance.map((c) => {
                          const t = tenants.find((item) => item.id === c.tenant_id)
                          return (
                            <tr key={c.id} className="hover:bg-slate-800/40 transition">
                              <td className="px-4 py-3.5 font-bold text-white">{t?.name ?? c.tenant_id.slice(0, 8)}</td>
                              <td className="px-4 py-3.5 font-semibold text-teal-300">{c.certification_name}</td>
                              <td className="px-4 py-3.5">
                                <StatusBadge status={c.status} />
                              </td>
                              <td className="px-4 py-3.5 text-slate-400">
                                {new Date(c.audit_date).toLocaleDateString('tr-TR')}
                              </td>
                              <td className="px-4 py-3.5 text-slate-400">{c.auditor_notes ?? '—'}</td>
                            </tr>
                          )
                        })
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* =========================================================================
                TAB 5: AĞ DUYURULARI (NETWORK ALERTS)
               ========================================================================= */}
            {activeTab === 'alerts' && (
              <div className="space-y-6">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <h2 className="text-sm font-bold uppercase tracking-wide text-white">
                      📢 Federasyon ve Ağ Düzeyinde Duyuru Yayını
                    </h2>
                    <p className="mt-1 text-xs text-slate-400">
                      Tüm kulüplere veya seçili bir kulübün yönetim paneline resmi duyuru ve uyarılar yayınlayın.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setShowAlertModal(true)
                      setAlertTitle('')
                      setAlertMessage('')
                      setAlertSeverity('INFO')
                      setAlertTargetTenant('')
                      setAlertError(null)
                    }}
                    className="rounded-xl bg-teal-600 px-4 py-2 text-xs font-bold text-white hover:bg-teal-500 transition shadow-sm"
                  >
                    + Yeni Duyuru Yayınla
                  </button>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  {alerts.length === 0 ? (
                    <div className="col-span-2">
                      <EmptyState title="Aktif duyuru yok" description="Ağ genelinde yayınlanmış bir duyuru bulunmuyor." />
                    </div>
                  ) : (
                    alerts.map((a) => {
                      const t = tenants.find((item) => item.id === a.target_tenant_id)
                      const border =
                        a.severity === 'CRITICAL'
                          ? 'border-rose-800/80 bg-rose-950/30'
                          : a.severity === 'WARNING'
                            ? 'border-amber-800/80 bg-amber-950/30'
                            : a.severity === 'MAINTENANCE'
                              ? 'border-purple-800/80 bg-purple-950/30'
                              : 'border-teal-800/80 bg-teal-950/30'
                      return (
                        <div key={a.id} className={`rounded-2xl border p-5 ${border} flex flex-col justify-between`}>
                          <div>
                            <div className="flex items-center justify-between gap-2">
                              <span className="text-[10px] font-extrabold uppercase tracking-wider rounded-md bg-slate-900 px-2 py-0.5 text-white">
                                {a.severity}
                              </span>
                              <span className="text-[11px] text-slate-400">
                                {new Date(a.created_at).toLocaleString('tr-TR')}
                              </span>
                            </div>
                            <h3 className="mt-3 text-sm font-bold text-white">{a.title}</h3>
                            <p className="mt-2 text-xs leading-relaxed text-slate-300">{a.message}</p>
                          </div>
                          <div className="mt-4 flex items-center justify-between border-t border-slate-800/80 pt-3 text-[11px]">
                            <span className="text-slate-400">
                              Hedef: <strong className="text-slate-200">{t ? t.name : 'Tüm Federasyon Kulüpleri'}</strong>
                            </span>
                            <button
                              type="button"
                              onClick={() => void handleDeleteAlert(a.id)}
                              className="text-rose-400 hover:underline font-semibold"
                            >
                              Yayından Kaldır
                            </button>
                          </div>
                        </div>
                      )
                    })
                  )}
                </div>
              </div>
            )}

            {/* =========================================================================
                TAB 6: RAPORLAR & ANALİTİK (CROSS-TENANT ANALYTICS)
               ========================================================================= */}
            {activeTab === 'reports' && (
              <div className="space-y-6">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <h2 className="text-sm font-bold uppercase tracking-wide text-white">
                      📈 Konsolide Ağ Analitiği & Finansal Raporlar
                    </h2>
                    <p className="mt-1 text-xs text-slate-400">
                      Tüm kulüplerin toplam ciro, turnike geçiş ve büyüme verileri.
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={exportCSV}
                    className="rounded-xl border border-slate-700 bg-slate-900 px-4 py-2 text-xs font-bold text-teal-400 hover:bg-slate-800 transition"
                  >
                    📥 Konsolide Ağ Verisini İndir (.csv)
                  </button>
                </div>

                <div className="grid gap-4 sm:grid-cols-3">
                  <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Konsolide Ciro
                    </span>
                    <div className="mt-2 text-2xl font-extrabold text-white">
                      {analytics ? formatMinor(analytics.total_revenue_minor) : '—'}
                    </div>
                  </div>
                  <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Toplam Turnike Geçişi
                    </span>
                    <div className="mt-2 text-2xl font-extrabold text-teal-400">
                      {analytics ? analytics.total_checkins.toLocaleString('tr-TR') : '—'}
                    </div>
                  </div>
                  <div className="rounded-2xl border border-slate-800 bg-slate-900/90 p-5">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                      Kulüp Başına Ortalama Ciro
                    </span>
                    <div className="mt-2 text-2xl font-extrabold text-emerald-400">
                      {analytics && tenants.length > 0
                        ? formatMinor(Math.trunc(analytics.total_revenue_minor / tenants.length))
                        : '—'}
                    </div>
                  </div>
                </div>

                <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/90">
                  <table className="min-w-full divide-y divide-slate-800 text-xs">
                    <thead>
                      <tr className="bg-slate-950/60 text-left text-slate-400 font-semibold">
                        <th className="px-4 py-3.5">Kulüp</th>
                        <th className="px-4 py-3.5">Turnike Geçiş Adedi</th>
                        <th className="px-4 py-3.5">Tahsil Edilen Ciro</th>
                        <th className="px-4 py-3.5">Ağ Cirosundaki Payı</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/80 text-slate-300">
                      {tenants.map((t) => {
                        const clubRev = analytics?.revenue_by_tenant_minor[t.id] ?? t.revenue_minor
                        const totalRev = analytics?.total_revenue_minor ?? 1
                        const share = totalRev > 0 ? ((clubRev / totalRev) * 100).toFixed(1) : '0'
                        const checkins = analytics?.checkins_by_tenant[t.id] ?? 0
                        return (
                          <tr key={t.id} className="hover:bg-slate-800/40 transition">
                            <td className="px-4 py-3.5 font-bold text-white">{t.name}</td>
                            <td className="px-4 py-3.5 font-medium text-teal-300">{checkins} geçiş</td>
                            <td className="px-4 py-3.5 font-bold text-white">{formatMinor(clubRev)}</td>
                            <td className="px-4 py-3.5">
                              <div className="flex items-center gap-2">
                                <div className="h-1.5 w-24 rounded-full bg-slate-800 overflow-hidden">
                                  <div
                                    className="h-full bg-teal-400 rounded-full"
                                    style={{ width: `${Math.min(100, Number(share))}%` }}
                                  />
                                </div>
                                <span className="text-[11px] text-slate-400">%{share}</span>
                              </div>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}

        {/* =========================================================================
            MODALLAR
           ========================================================================= */}

        {/* Modal: Yeni Kulüp Aç */}
        {showAddGymModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
              <h3 className="text-lg font-bold text-white">🏢 Yeni Kulüp & Franchise Ekle</h3>
              <p className="mt-1 text-xs text-slate-400">
                Federasyon ağına yeni bir spor salonu ve ana şubesini tanımlayın.
              </p>
              <form onSubmit={(e) => void handleCreateGym(e)} className="mt-4 space-y-3 text-xs">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Kulüp Adı *</label>
                  <input
                    type="text"
                    required
                    placeholder="Örn: FitClub Beşiktaş"
                    value={newGymName}
                    onChange={(e) => setNewGymName(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-teal-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Lokasyon Kodu (Benzersiz) *</label>
                  <input
                    type="text"
                    required
                    placeholder="Örn: FIT-BESIKTAS"
                    value={newGymCode}
                    onChange={(e) => setNewGymCode(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white font-mono uppercase focus:border-teal-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Varsayılan Ana Şube Adı</label>
                  <input
                    type="text"
                    placeholder="Örn: Çarşı Şubesi"
                    value={newGymBranch}
                    onChange={(e) => setNewGymBranch(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-teal-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Şube Adresi</label>
                  <input
                    type="text"
                    placeholder="Örn: Beşiktaş, İstanbul"
                    value={newGymAddress}
                    onChange={(e) => setNewGymAddress(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-teal-500 focus:outline-none"
                  />
                </div>
                {newGymError && <Alert variant="error">{newGymError}</Alert>}
                <div className="mt-5 flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowAddGymModal(false)}
                    className="rounded-xl border border-slate-700 px-4 py-2 font-semibold text-slate-300 hover:bg-slate-800"
                  >
                    Vazgeç
                  </button>
                  <button
                    type="submit"
                    disabled={newGymSubmitting}
                    className="rounded-xl bg-teal-600 px-4 py-2 font-bold text-white hover:bg-teal-500 transition"
                  >
                    {newGymSubmitting ? 'Oluşturuluyor…' : 'Kulübü Oluştur'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Askıya Al */}
        {suspendTarget && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-md rounded-2xl border border-rose-900/80 bg-slate-900 p-6 shadow-xl">
              <h3 className="text-lg font-bold text-white">⚠️ Kulübü Askıya Al</h3>
              <p className="mt-1 text-xs text-rose-300">
                <strong>{suspendTarget.name}</strong> kulübü askıya alınacaktır. Bu işlem sonrasında kulübün turnike ve
                portal erişimleri anında durdurulur.
              </p>
              <form onSubmit={(e) => void handleSuspendGym(e)} className="mt-4 space-y-3 text-xs">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Askıya Alma Gerekçesi *</label>
                  <textarea
                    required
                    rows={3}
                    placeholder="Örn: Hijyen denetimi yetersizliği ve aidat gecikmesi."
                    value={suspendReason}
                    onChange={(e) => setSuspendReason(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-rose-500 focus:outline-none"
                  />
                </div>
                {suspendError && <Alert variant="error">{suspendError}</Alert>}
                <div className="mt-5 flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setSuspendTarget(null)}
                    className="rounded-xl border border-slate-700 px-4 py-2 font-semibold text-slate-300 hover:bg-slate-800"
                  >
                    İptal
                  </button>
                  <button
                    type="submit"
                    disabled={suspendSubmitting}
                    className="rounded-xl bg-rose-600 px-4 py-2 font-bold text-white hover:bg-rose-500 transition"
                  >
                    {suspendSubmitting ? 'İşleniyor…' : 'Askıya Almayı Onayla'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Break-Glass Acil Destek Girişi */}
        {breakGlassTarget && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-md rounded-2xl border border-purple-900/80 bg-slate-900 p-6 shadow-xl">
              <h3 className="text-lg font-bold text-white">🛡️ Break-Glass Acil Destek Girişi</h3>
              <p className="mt-1 text-xs text-slate-400">
                <strong>{breakGlassTarget.name}</strong> kulübüne denetlenen süreli acil erişim oturumu başlatılır.
              </p>
              <form onSubmit={(e) => void handleBreakGlass(e)} className="mt-4 space-y-3 text-xs">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Destek Bilet No *</label>
                  <input
                    type="text"
                    required
                    placeholder="Örn: TICKET-8842"
                    value={bgTicket}
                    onChange={(e) => setBgTicket(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white font-mono uppercase focus:border-purple-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Erişim Gerekçesi *</label>
                  <textarea
                    required
                    rows={2}
                    placeholder="Örn: Turnike tarayıcı arıza giderme müdahalesi."
                    value={bgReason}
                    onChange={(e) => setBgReason(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-purple-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Oturum Süresi</label>
                  <select
                    value={bgDuration}
                    onChange={(e) => setBgDuration(Number(e.target.value))}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-purple-500 focus:outline-none"
                  >
                    <option value={15}>15 Dakika</option>
                    <option value={30}>30 Dakika</option>
                    <option value={60}>60 Dakika</option>
                  </select>
                </div>
                {bgError && <Alert variant="error">{bgError}</Alert>}
                <div className="mt-5 flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setBreakGlassTarget(null)}
                    className="rounded-xl border border-slate-700 px-4 py-2 font-semibold text-slate-300 hover:bg-slate-800"
                  >
                    Vazgeç
                  </button>
                  <button
                    type="submit"
                    disabled={bgSubmitting}
                    className="rounded-xl bg-purple-600 px-4 py-2 font-bold text-white hover:bg-purple-500 transition"
                  >
                    {bgSubmitting ? 'Yetkilendiriliyor…' : 'Oturumu Başlat & Gir'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Pasaport Düzenle */}
        {passportTarget && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
              <h3 className="text-lg font-bold text-white">🛂 Pasaport Kurallarını Güncelle</h3>
              <p className="mt-1 text-xs text-slate-400">
                <strong>{passportTarget.name}</strong> kulübünün federasyon çapraz geçiş politikaları.
              </p>
              <form onSubmit={(e) => void handleUpdatePassport(e)} className="mt-4 space-y-3 text-xs">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="passport_active"
                    checked={passportActive}
                    onChange={(e) => setPassportActive(e.target.checked)}
                    className="rounded border-slate-700 bg-slate-950 text-teal-500 focus:ring-teal-500"
                  />
                  <label htmlFor="passport_active" className="text-slate-300 font-semibold">
                    Federasyon Dolaşımı (Pasaport) Aktif
                  </label>
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">İzin Verilen Paket Seviyeleri</label>
                  <input
                    type="text"
                    required
                    placeholder="Örn: VIP,GOLD,PLATINUM"
                    value={passportTiers}
                    onChange={(e) => setPassportTiers(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white font-mono uppercase focus:border-teal-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Aylık Tavan Misafir Geçiş Limiti</label>
                  <input
                    type="number"
                    min={1}
                    max={30}
                    required
                    value={passportMaxVisits}
                    onChange={(e) => setPassportMaxVisits(Number(e.target.value))}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-teal-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Ziyaret Başı Mahsuplaşma Ücreti (₺)</label>
                  <input
                    type="number"
                    min={0}
                    step={1}
                    value={passportFeeMinor}
                    onChange={(e) => setPassportFeeMinor(Number(e.target.value))}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-teal-500 focus:outline-none"
                  />
                </div>
                {passportError && <Alert variant="error">{passportError}</Alert>}
                <div className="mt-5 flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setPassportTarget(null)}
                    className="rounded-xl border border-slate-700 px-4 py-2 font-semibold text-slate-300 hover:bg-slate-800"
                  >
                    Vazgeç
                  </button>
                  <button
                    type="submit"
                    disabled={passportSubmitting}
                    className="rounded-xl bg-teal-600 px-4 py-2 font-bold text-white hover:bg-teal-500 transition"
                  >
                    {passportSubmitting ? 'Kaydediliyor…' : 'Ayarları Kaydet'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Yeni Denetim Kaydı Ekle */}
        {showComplianceModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
              <h3 className="text-lg font-bold text-white">🛡️ Yeni Muayene / Denetim Kaydı</h3>
              <form onSubmit={(e) => void handleAddCompliance(e)} className="mt-4 space-y-3 text-xs">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Denetlenen Kulüp *</label>
                  <select
                    required
                    value={compTenantId}
                    onChange={(e) => setCompTenantId(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-teal-500 focus:outline-none"
                  >
                    {tenants.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name} [{t.location_code}]
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Sertifika / Standart Adı *</label>
                  <input
                    type="text"
                    required
                    placeholder="Örn: TSE-ISO 9001 Hijyen & Güvenlik Standardı"
                    value={compCertName}
                    onChange={(e) => setCompCertName(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-teal-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Denetim Sonucu *</label>
                  <select
                    value={compStatus}
                    onChange={(e) => setCompStatus(e.target.value as 'PASSED' | 'CONDITIONAL' | 'FAILED')}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-teal-500 focus:outline-none"
                  >
                    <option value="PASSED">GEÇTİ (Uyumlu)</option>
                    <option value="CONDITIONAL">ŞARTLI (Eksikler Var)</option>
                    <option value="FAILED">BAŞARISIZ (Kritik Uygunsuzluk)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Denetçi Notları</label>
                  <textarea
                    rows={2}
                    placeholder="Örn: İlkyardım ekipmanı ve yangın tüpü kontrolleri yapıldı."
                    value={compNotes}
                    onChange={(e) => setCompNotes(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-teal-500 focus:outline-none"
                  />
                </div>
                {compError && <Alert variant="error">{compError}</Alert>}
                <div className="mt-5 flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowComplianceModal(false)}
                    className="rounded-xl border border-slate-700 px-4 py-2 font-semibold text-slate-300 hover:bg-slate-800"
                  >
                    Vazgeç
                  </button>
                  <button
                    type="submit"
                    disabled={compSubmitting}
                    className="rounded-xl bg-teal-600 px-4 py-2 font-bold text-white hover:bg-teal-500 transition"
                  >
                    {compSubmitting ? 'Kaydediliyor…' : 'Denetimi Kaydet'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Yeni Duyuru Yayınla */}
        {showAlertModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
            <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl">
              <h3 className="text-lg font-bold text-white">📢 Yeni Ağ Duyurusu Yayınla</h3>
              <form onSubmit={(e) => void handleCreateAlert(e)} className="mt-4 space-y-3 text-xs">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Duyuru Başlığı *</label>
                  <input
                    type="text"
                    required
                    placeholder="Örn: Planlı Turnike Bakım Çalışması"
                    value={alertTitle}
                    onChange={(e) => setAlertTitle(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-teal-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Önem Derecesi *</label>
                  <select
                    value={alertSeverity}
                    onChange={(e) =>
                      setAlertSeverity(e.target.value as 'INFO' | 'WARNING' | 'CRITICAL' | 'MAINTENANCE')
                    }
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-teal-500 focus:outline-none"
                  >
                    <option value="INFO">BİLGİ (Info)</option>
                    <option value="WARNING">UYARI (Warning)</option>
                    <option value="CRITICAL">KRİTİK / ACİL (Critical)</option>
                    <option value="MAINTENANCE">BAKIM (Maintenance)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Hedef Kapsam</label>
                  <select
                    value={alertTargetTenant}
                    onChange={(e) => setAlertTargetTenant(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-teal-500 focus:outline-none"
                  >
                    <option value="">Tüm Federasyon Kulüpleri</option>
                    {tenants.map((t) => (
                      <option key={t.id} value={t.id}>
                        Yalnızca: {t.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Duyuru Metni *</label>
                  <textarea
                    required
                    rows={3}
                    placeholder="Örn: Saat 02:00 ile 04:00 arasında turnike okuyucularda yazılım güncellemesi yapılacaktır."
                    value={alertMessage}
                    onChange={(e) => setAlertMessage(e.target.value)}
                    className="w-full rounded-xl border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-teal-500 focus:outline-none"
                  />
                </div>
                {alertError && <Alert variant="error">{alertError}</Alert>}
                <div className="mt-5 flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowAlertModal(false)}
                    className="rounded-xl border border-slate-700 px-4 py-2 font-semibold text-slate-300 hover:bg-slate-800"
                  >
                    Vazgeç
                  </button>
                  <button
                    type="submit"
                    disabled={alertSubmitting}
                    className="rounded-xl bg-teal-600 px-4 py-2 font-bold text-white hover:bg-teal-500 transition"
                  >
                    {alertSubmitting ? 'Yayınlanıyor…' : 'Duyuruyu Yayınla'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
