import { ApiError } from '../../api/client'

export const TAB_KEYS = ['overview', 'gyms', 'passport', 'compliance', 'alerts', 'reports'] as const
export type TabKey = (typeof TAB_KEYS)[number]

export function isTabKey(value: string | null): value is TabKey {
  return value !== null && (TAB_KEYS as readonly string[]).includes(value)
}

export type OrganizationSummary = {
  id: string
  name: string
  domain: string | null
}

export type TenantSummary = {
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

export type FederationSummary = {
  organization_count: number
  tenant_count: number
  active_tenant_count: number
  suspended_tenant_count: number
  member_count: number
  active_membership_count: number
  revenue_minor: number
  partial: boolean
}

export type AuditEvent = {
  id: string
  tenant_id: string
  user_id: string | null
  action: string
  resource_type: string
  created_at: string
}

export type PassportConfig = {
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

export type ComplianceRecord = {
  id: string
  tenant_id: string
  certification_name: string
  status: 'PASSED' | 'FAILED' | 'CONDITIONAL' | 'EXPIRED'
  audit_date: string
  auditor_notes?: string | null
  created_at: string
}

export type NetworkAlert = {
  id: string
  organization_id: string
  target_tenant_id: string | null
  title: string
  message: string
  severity: 'INFO' | 'WARNING' | 'CRITICAL' | 'MAINTENANCE'
  created_at: string
}

export type AnalyticsOverview = {
  total_checkins: number
  checkins_by_tenant: Record<string, number>
  total_revenue_minor: number
  revenue_by_tenant_minor: Record<string, number>
  partial: boolean
}

export function formatMinor(minor: number): string {
  const major = Math.trunc(minor / 100)
  const cents = Math.abs(minor % 100)
    .toString()
    .padStart(2, '0')
  return `₺${major.toLocaleString('tr-TR')},${cents}`
}

export function formatApiError(e: unknown, fallback: string): string {
  if (e instanceof ApiError) {
    if (e.status === 403) return 'Bu işlem için yetkiniz bulunmuyor.'
    return e.message
  }
  if (e instanceof Error) return e.message
  return fallback
}
