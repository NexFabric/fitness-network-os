import { useCallback, useEffect, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { api, setAuth } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { Alert, LoadingSkeleton } from '../components/ui'
import { AlertsTab } from './hq/AlertsTab'
import { ComplianceTab } from './hq/ComplianceTab'
import { GymsTab } from './hq/GymsTab'
import { OverviewTab } from './hq/OverviewTab'
import { PassportTab } from './hq/PassportTab'
import { ReportsTab } from './hq/ReportsTab'
import {
  formatApiError,
  isTabKey,
  type AnalyticsOverview,
  type AuditEvent,
  type ComplianceRecord,
  type FederationSummary,
  type NetworkAlert,
  type OrganizationSummary,
  type PassportConfig,
  type TabKey,
  type TenantSummary,
} from './hq/types'

export default function SuperAdminPortal() {
  const { session, refresh } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const rawTab = searchParams.get('tab')
  const activeTab: TabKey = isTabKey(rawTab) ? rawTab : 'overview'

  const setTab = (tab: TabKey) => {
    setSearchParams(tab === 'overview' ? {} : { tab })
  }

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
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<'ALL' | 'ACTIVE' | 'SUSPENDED'>('ALL')

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

      if (tenantRows.length > 0) {
        setCompTenantId((prev) => prev || tenantRows[0].id)
      }
    } catch (err) {
      setError(formatApiError(err, 'Federasyon verileri yüklenemedi. Birkaç saniye sonra tekrar deneyin.'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadData()
  }, [loadData])

  async function enterTenant(tenantId: string) {
    setSwitching(tenantId)
    setAuth(tenantId)
    await refresh()
    window.location.assign('/')
  }

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

  async function handleReactivateGym(t: TenantSummary) {
    try {
      await api(`/api/v1/admin/tenants/${t.id}/reactivate`, { method: 'POST' })
      setSuccessMessage(`${t.name} kulübü yeniden aktifleştirildi.`)
      void loadData()
    } catch (err) {
      setError(formatApiError(err, 'Kulüp aktifleştirilemedi.'))
    }
  }

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

  async function handleDeleteAlert(id: string) {
    try {
      await api(`/api/v1/admin/alerts/${id}`, { method: 'DELETE' })
      setSuccessMessage('Duyuru yayından kaldırıldı.')
      void loadData()
    } catch (err) {
      setError(formatApiError(err, 'Duyuru silinemedi.'))
    }
  }

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
    <div className="min-h-[100dvh] bg-slate-950 px-4 py-8 text-slate-100 font-sans">
      <div className="mx-auto w-full max-w-7xl">
        <header className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-teal-500/10 text-xl text-teal-400 border border-teal-500/20">
                👑
              </span>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-2xl font-extrabold tracking-tight text-white">Federasyon Konsolu</h1>
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
                  <span className="text-[10px] text-slate-400">{new Date(a.created_at).toLocaleString('tr-TR')}</span>
                </div>
              )
            })}
          </div>
        )}

        {successMessage && (
          <div className="mb-6 flex items-center justify-between gap-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-xs font-semibold text-emerald-400">
            <span>{successMessage}</span>
            <button type="button" onClick={() => setSuccessMessage(null)} className="text-slate-400 hover:text-white">
              ✕
            </button>
          </div>
        )}

        {error && (
          <div className="mb-6 flex items-center justify-between gap-3 rounded-xl border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-xs font-semibold text-rose-400">
            <span>{error}</span>
            <button type="button" onClick={() => setError(null)} className="text-slate-400 hover:text-white">
              ✕
            </button>
          </div>
        )}

        <nav className="mb-6 flex overflow-x-auto whitespace-nowrap no-scrollbar gap-2 border-b border-slate-800 pb-2">
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
                className={`flex shrink-0 items-center gap-2 rounded-xl px-4 py-2.5 min-h-[44px] sm:min-h-[38px] text-xs font-bold transition ${
                  isActive
                    ? 'bg-teal-500/15 text-teal-400 border border-teal-500/30'
                    : 'text-slate-400 hover:bg-slate-900 hover:text-slate-200 border border-transparent'
                }`}
              >
                <span>{tab.label}</span>
                {tab.count !== undefined && (
                  <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] text-slate-400">{tab.count}</span>
                )}
              </button>
            )
          })}
        </nav>

        {loading ? (
          <LoadingSkeleton rows={6} />
        ) : (
          <>
            {activeTab === 'overview' && summary && (
              <OverviewTab
                summary={summary}
                tenants={tenants}
                audit={audit}
                switching={switching}
                onEnterTenant={enterTenant}
                onGoGyms={() => setTab('gyms')}
              />
            )}
            {activeTab === 'gyms' && (
              <GymsTab
                tenants={filteredTenants}
                searchQuery={searchQuery}
                statusFilter={statusFilter}
                switching={switching}
                onSearchChange={setSearchQuery}
                onStatusFilterChange={setStatusFilter}
                onOpenAddGym={() => setShowAddGymModal(true)}
                onEnterTenant={enterTenant}
                onOpenBreakGlass={(t) => {
                  setBreakGlassTarget(t)
                  setBgReason('')
                  setBgTicket('')
                  setBgError(null)
                }}
                onOpenSuspend={(t) => {
                  setSuspendTarget(t)
                  setSuspendReason('')
                  setSuspendError(null)
                }}
                onReactivate={handleReactivateGym}
              />
            )}
            {activeTab === 'passport' && (
              <PassportTab
                tenants={tenants}
                passports={passports}
                onEdit={(t, p) => {
                  setPassportTarget(t)
                  setPassportActive(p?.is_active ?? true)
                  setPassportTiers(p?.allowed_home_gym_tiers ?? 'VIP,GOLD')
                  setPassportMaxVisits(p?.rules?.max_monthly_roaming_visits ?? 5)
                  setPassportFeeMinor((p?.rules?.guest_fee_minor ?? 0) / 100)
                  setPassportError(null)
                }}
              />
            )}
            {activeTab === 'compliance' && (
              <ComplianceTab
                tenants={tenants}
                compliance={compliance}
                onOpenAdd={() => {
                  setShowComplianceModal(true)
                  setCompCertName('')
                  setCompNotes('')
                  setCompError(null)
                }}
              />
            )}
            {activeTab === 'alerts' && (
              <AlertsTab
                tenants={tenants}
                alerts={alerts}
                onOpenCreate={() => {
                  setShowAlertModal(true)
                  setAlertTitle('')
                  setAlertMessage('')
                  setAlertSeverity('INFO')
                  setAlertTargetTenant('')
                  setAlertError(null)
                }}
                onDelete={handleDeleteAlert}
              />
            )}
            {activeTab === 'reports' && (
              <ReportsTab tenants={tenants} analytics={analytics} onExportCsv={exportCSV} />
            )}
          </>
        )}

        {showAddGymModal && (
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="add-gym-modal-title"
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 overflow-y-auto"
          >
            <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl max-h-[90dvh] overflow-y-auto pb-[max(1.5rem,env(safe-area-inset-bottom))]">
              <h3 id="add-gym-modal-title" className="text-lg font-bold text-white">🏢 Yeni Kulüp & Franchise Ekle</h3>
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
                    className="input-field mt-1 text-[16px] sm:text-xs"
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
                    className="input-field mt-1 font-mono uppercase text-[16px] sm:text-xs"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Varsayılan Ana Şube Adı</label>
                  <input
                    type="text"
                    placeholder="Örn: Çarşı Şubesi"
                    value={newGymBranch}
                    onChange={(e) => setNewGymBranch(e.target.value)}
                    className="input-field mt-1 text-[16px] sm:text-xs"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Şube Adresi</label>
                  <input
                    type="text"
                    placeholder="Örn: Beşiktaş, İstanbul"
                    value={newGymAddress}
                    onChange={(e) => setNewGymAddress(e.target.value)}
                    className="input-field mt-1 text-[16px] sm:text-xs"
                  />
                </div>
                {newGymError && <Alert variant="error">{newGymError}</Alert>}
                <div className="mt-5 flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowAddGymModal(false)}
                    className="btn-secondary text-xs px-4 py-2 min-h-[44px] sm:min-h-[36px]"
                  >
                    Vazgeç
                  </button>
                  <button
                    type="submit"
                    disabled={newGymSubmitting}
                    className="btn-primary text-xs px-4 py-2 min-h-[44px] sm:min-h-[36px] bg-teal-600 hover:bg-teal-500"
                  >
                    {newGymSubmitting ? 'Oluşturuluyor…' : 'Kulübü Oluştur'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {suspendTarget && (
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="suspend-gym-modal-title"
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 overflow-y-auto"
          >
            <div className="w-full max-w-md rounded-2xl border border-rose-900/80 bg-slate-900 p-6 shadow-xl max-h-[90dvh] overflow-y-auto pb-[max(1.5rem,env(safe-area-inset-bottom))]">
              <h3 id="suspend-gym-modal-title" className="text-lg font-bold text-white">⚠️ Kulübü Askıya Al</h3>
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
                    className="input-field mt-1 text-[16px] sm:text-xs"
                  />
                </div>
                {suspendError && <Alert variant="error">{suspendError}</Alert>}
                <div className="mt-5 flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setSuspendTarget(null)}
                    className="btn-secondary text-xs px-4 py-2 min-h-[44px] sm:min-h-[36px]"
                  >
                    İptal
                  </button>
                  <button
                    type="submit"
                    disabled={suspendSubmitting}
                    className="btn-danger text-xs px-4 py-2 min-h-[44px] sm:min-h-[36px]"
                  >
                    {suspendSubmitting ? 'İşleniyor…' : 'Askıya Almayı Onayla'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {breakGlassTarget && (
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="break-glass-modal-title"
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 overflow-y-auto"
          >
            <div className="w-full max-w-md rounded-2xl border border-purple-900/80 bg-slate-900 p-6 shadow-xl max-h-[90dvh] overflow-y-auto pb-[max(1.5rem,env(safe-area-inset-bottom))]">
              <h3 id="break-glass-modal-title" className="text-lg font-bold text-white">🛡️ Break-Glass Acil Destek Girişi</h3>
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
                    className="input-field mt-1 font-mono uppercase text-[16px] sm:text-xs"
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
                    className="input-field mt-1 text-[16px] sm:text-xs"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Oturum Süresi</label>
                  <select
                    value={bgDuration}
                    onChange={(e) => setBgDuration(Number(e.target.value))}
                    className="input-field mt-1 text-[16px] sm:text-xs"
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
                    className="btn-secondary text-xs px-4 py-2 min-h-[44px] sm:min-h-[36px]"
                  >
                    Vazgeç
                  </button>
                  <button
                    type="submit"
                    disabled={bgSubmitting}
                    className="btn-primary text-xs px-4 py-2 min-h-[44px] sm:min-h-[36px] bg-purple-600 hover:bg-purple-500"
                  >
                    {bgSubmitting ? 'Yetkilendiriliyor…' : 'Oturumu Başlat & Gir'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {passportTarget && (
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="passport-modal-title"
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 overflow-y-auto"
          >
            <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl max-h-[90dvh] overflow-y-auto pb-[max(1.5rem,env(safe-area-inset-bottom))]">
              <h3 id="passport-modal-title" className="text-lg font-bold text-white">🛂 Pasaport Kurallarını Güncelle</h3>
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
                    className="input-field mt-1 font-mono uppercase text-[16px] sm:text-xs"
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
                    className="input-field mt-1 text-[16px] sm:text-xs"
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
                    className="input-field mt-1 text-[16px] sm:text-xs"
                  />
                </div>
                {passportError && <Alert variant="error">{passportError}</Alert>}
                <div className="mt-5 flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setPassportTarget(null)}
                    className="btn-secondary text-xs px-4 py-2 min-h-[44px] sm:min-h-[36px]"
                  >
                    Vazgeç
                  </button>
                  <button
                    type="submit"
                    disabled={passportSubmitting}
                    className="btn-primary text-xs px-4 py-2 min-h-[44px] sm:min-h-[36px] bg-teal-600 hover:bg-teal-500"
                  >
                    {passportSubmitting ? 'Kaydediliyor…' : 'Ayarları Kaydet'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {showComplianceModal && (
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="compliance-modal-title"
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 overflow-y-auto"
          >
            <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl max-h-[90dvh] overflow-y-auto pb-[max(1.5rem,env(safe-area-inset-bottom))]">
              <h3 id="compliance-modal-title" className="text-lg font-bold text-white">🛡️ Yeni Muayene / Denetim Kaydı</h3>
              <form onSubmit={(e) => void handleAddCompliance(e)} className="mt-4 space-y-3 text-xs">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Denetlenen Kulüp *</label>
                  <select
                    required
                    value={compTenantId}
                    onChange={(e) => setCompTenantId(e.target.value)}
                    className="input-field mt-1 text-[16px] sm:text-xs"
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
                    className="input-field mt-1 text-[16px] sm:text-xs"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Denetim Sonucu *</label>
                  <select
                    value={compStatus}
                    onChange={(e) => setCompStatus(e.target.value as 'PASSED' | 'CONDITIONAL' | 'FAILED')}
                    className="input-field mt-1 text-[16px] sm:text-xs"
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
                    className="input-field mt-1 text-[16px] sm:text-xs"
                  />
                </div>
                {compError && <Alert variant="error">{compError}</Alert>}
                <div className="mt-5 flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowComplianceModal(false)}
                    className="btn-secondary text-xs px-4 py-2 min-h-[44px] sm:min-h-[36px]"
                  >
                    Vazgeç
                  </button>
                  <button
                    type="submit"
                    disabled={compSubmitting}
                    className="btn-primary text-xs px-4 py-2 min-h-[44px] sm:min-h-[36px] bg-teal-600 hover:bg-teal-500"
                  >
                    {compSubmitting ? 'Kaydediliyor…' : 'Denetimi Kaydet'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {showAlertModal && (
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="alert-modal-title"
            className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 overflow-y-auto"
          >
            <div className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-6 shadow-xl max-h-[90dvh] overflow-y-auto pb-[max(1.5rem,env(safe-area-inset-bottom))]">
              <h3 id="alert-modal-title" className="text-lg font-bold text-white">📢 Yeni Ağ Duyurusu Yayınla</h3>
              <form onSubmit={(e) => void handleCreateAlert(e)} className="mt-4 space-y-3 text-xs">
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Duyuru Başlığı *</label>
                  <input
                    type="text"
                    required
                    placeholder="Örn: Planlı Turnike Bakım Çalışması"
                    value={alertTitle}
                    onChange={(e) => setAlertTitle(e.target.value)}
                    className="input-field mt-1 text-[16px] sm:text-xs"
                  />
                </div>
                <div>
                  <label className="block text-slate-300 font-semibold mb-1">Önem Derecesi *</label>
                  <select
                    value={alertSeverity}
                    onChange={(e) =>
                      setAlertSeverity(e.target.value as 'INFO' | 'WARNING' | 'CRITICAL' | 'MAINTENANCE')
                    }
                    className="input-field mt-1 text-[16px] sm:text-xs"
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
                    className="input-field mt-1 text-[16px] sm:text-xs"
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
                    className="input-field mt-1 text-[16px] sm:text-xs"
                  />
                </div>
                {alertError && <Alert variant="error">{alertError}</Alert>}
                <div className="mt-5 flex justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setShowAlertModal(false)}
                    className="btn-secondary text-xs px-4 py-2 min-h-[44px] sm:min-h-[36px]"
                  >
                    Vazgeç
                  </button>
                  <button
                    type="submit"
                    disabled={alertSubmitting}
                    className="btn-primary text-xs px-4 py-2 min-h-[44px] sm:min-h-[36px] bg-teal-600 hover:bg-teal-500"
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
