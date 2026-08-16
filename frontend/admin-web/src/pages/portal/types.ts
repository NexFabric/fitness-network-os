export type MeMember = {
  id: string
  member_number: string
  first_name: string
  last_name: string
  status: string
}

export type Membership = {
  id: string
  status: string
  start_date: string
  end_date: string | null
}

export type Wallet = {
  wallet_id: string
  entitlement_code: string | null
  entitlement_name: string | null
  allocated: number
  remaining: number
  expires_at: string | null
}

export type EntitlementsSummary = {
  member_id: string
  wallets: Wallet[]
}

export type MeCheckin = {
  id: string
  tenant_id: string
  member_id: string
  location_id: string
  device_id: string | null
  checkin_time: string
  checkout_time: string | null
}

export type MeInvoice = {
  id: string
  invoice_number: string | null
  status: string
  total_amount_minor: number
  paid_amount_minor: number
  discount_amount_minor: number
  currency: string
  due_date: string | null
  issued_at: string | null
  created_at: string
}

export type MePayment = {
  id: string
  amount_minor: number
  refunded_amount_minor: number
  currency: string
  status: string
  method: string
  paid_at: string | null
  created_at: string
}

export type MeConsent = {
  id: string
  consent_type: string
  document_version: string
  status: string
  given_at: string | null
  withdrawn_at: string | null
}

export type IssuedQr = {
  token: string
  jti: string
  exp: string
}

export type ActiveTab = 'access' | 'classes' | 'memberships' | 'history' | 'finance' | 'preferences'

export const TTL_SECONDS = 60

export function formatDateTr(isoString: string): string {
  const d = new Date(isoString)
  return d.toLocaleDateString('tr-TR', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatTime(isoString: string): string {
  const d = new Date(isoString)
  return d.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })
}

export function formatMinor(minor: number, currency: string = 'TRY'): string {
  const abs = Math.abs(minor)
  return `${Math.floor(abs / 100)},${String(abs % 100).padStart(2, '0')} ${currency}`
}
