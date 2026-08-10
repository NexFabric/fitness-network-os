const TENANT_KEY = 'fnos_scanner_tenant_id'

export function getBaseUrl(): string {
  const url = import.meta.env.VITE_API_URL
  if (!url) {
    return 'http://localhost:8000'
  }
  return url.replace(/\/$/, '')
}

export function getTenantId(): string | null {
  return localStorage.getItem(TENANT_KEY)
}

export function setAuth(tenantId: string): void {
  localStorage.setItem(TENANT_KEY, tenantId)
}

export function clearAuth(): void {
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
  const tenantId = getTenantId()
  if (tenantId) headers['X-Tenant-ID'] = tenantId

  const payload: Record<string, unknown> = {
    token: body.token,
    action: body.action ?? 'GYM_ENTRY',
    consume: body.consume ?? false,
  }
  if (body.location_id) {
    payload.location_id = body.location_id
  }

  // Cross-origin: bootstrap CSRF from API (cookie not readable via document.cookie)
  let csrf: string | null = null
  try {
    const boot = await fetch(`${base}/api/v1/auth/csrf`, {
      method: 'GET',
      credentials: 'include',
      headers: { Accept: 'application/json' },
    })
    if (boot.ok) {
      const j = (await boot.json()) as { csrf_token?: string }
      csrf = j.csrf_token ?? null
    }
  } catch {
    // continue; server may return 403
  }
  if (csrf) {
    headers['x-csrf-token'] = csrf
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
