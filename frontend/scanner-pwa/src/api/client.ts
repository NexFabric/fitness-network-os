const TOKEN_KEY = 'fnos_scanner_token'
const TENANT_KEY = 'fnos_scanner_tenant_id'

export function getBaseUrl(): string {
  const url = import.meta.env.VITE_API_URL
  if (!url) {
    return 'http://localhost:8000'
  }
  return url.replace(/\/$/, '')
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function getTenantId(): string | null {
  return localStorage.getItem(TENANT_KEY)
}

export function setAuth(token: string, tenantId: string): void {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(TENANT_KEY, tenantId)
}

export function clearAuth(): void {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(TENANT_KEY)
}

export class ApiError extends Error {
  status: number
  body: unknown

  constructor(status: number, message: string, body?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

export type ValidateQrRequest = {
  token: string
  location_id?: string | null
  action?: string
  consume?: boolean
}

export type ValidateQrResponse = {
  granted: boolean
  reason?: string | null
  member_id?: string | null
  jti?: string | null
  attempt_id?: string | null
  checkin_id?: string | null
  remaining?: number | null
}

/**
 * POST /api/v1/access/qr/validate
 * Backend may return 200 (granted), 403 (denied), or 409 (replay).
 * Denied bodies often nest under `detail`.
 */
export async function validateQr(
  body: ValidateQrRequest,
): Promise<ValidateQrResponse> {
  const base = getBaseUrl()
  const headers: Record<string, string> = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  }
  const token = getToken()
  const tenantId = getTenantId()
  if (token) headers.Authorization = `Bearer ${token}`
  if (tenantId) headers['X-Tenant-ID'] = tenantId

  const payload: Record<string, unknown> = {
    token: body.token,
    action: body.action ?? 'GYM_ENTRY',
    consume: body.consume ?? false,
  }
  if (body.location_id) {
    payload.location_id = body.location_id
  }

  const match = document.cookie.match(/(?:^|; )csrf_token=([^;]*)/)
  if (match) {
    headers['x-csrf-token'] = match[1]
  }

  const res = await fetch(`${base}/api/v1/access/qr/validate`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
    credentials: 'include',
  })

  const text = await res.text()
  let data: unknown = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  // Normalize FastAPI HTTPException detail shapes
  if (typeof data === 'object' && data !== null && 'detail' in data) {
    const detail = (data as { detail: unknown }).detail
    if (typeof detail === 'object' && detail !== null && 'granted' in detail) {
      return detail as ValidateQrResponse
    }
  }

  if (
    typeof data === 'object' &&
    data !== null &&
    'granted' in data
  ) {
    return data as ValidateQrResponse
  }

  if (!res.ok) {
    const msg =
      typeof data === 'object' && data !== null && 'detail' in data
        ? String((data as { detail: unknown }).detail)
        : res.statusText || 'Validate failed'
    throw new ApiError(res.status, msg, data)
  }

  return {
    granted: false,
    reason: 'unknown_response',
  }
}
