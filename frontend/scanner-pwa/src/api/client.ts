const TENANT_KEY = 'fnos_scanner_tenant_id'
const DEVICE_SECRET_KEY = 'fnos_scanner_device_secret'

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
  localStorage.removeItem(DEVICE_SECRET_KEY)
}

/**
 * Device request signing.
 *
 * The `device_session` cookie is only half of the device credential — the
 * server also demands an HMAC-SHA256 signature keyed on the per-session secret
 * handed out once by POST /devices/auth. The secret lives here, outside the
 * cookie jar, so a stolen cookie cannot be replayed from another machine.
 */
const DEVICE_SIGNATURE_HEADER = 'X-Device-Signature'
const DEVICE_TIMESTAMP_HEADER = 'X-Device-Timestamp'
const DEVICE_NONCE_HEADER = 'X-Device-Nonce'

export type DeviceAuthResult = {
  device_id: string
  tenant_id: string
  location_id: string
  session_id: string
  expires_at: string
}

function base64UrlToBytes(value: string): Uint8Array {
  const padded = value + '='.repeat((4 - (value.length % 4)) % 4)
  const binary = atob(padded.replace(/-/g, '+').replace(/_/g, '/'))
  const out = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i += 1) out[i] = binary.charCodeAt(i)
  return out
}

function toHex(buffer: ArrayBuffer): string {
  return Array.from(new Uint8Array(buffer))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}

export function getDeviceSecret(): string | null {
  return localStorage.getItem(DEVICE_SECRET_KEY)
}

/**
 * POST /api/v1/devices/auth — pairs this scanner with a provisioned device.
 * The returned signing secret is stored locally and never sent again.
 */
export async function authenticateDevice(
  deviceId: string,
  tenantId: string,
  apiKey: string,
): Promise<DeviceAuthResult> {
  const res = await fetch(`${getBaseUrl()}/api/v1/devices/auth`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({
      device_id: deviceId,
      tenant_id: tenantId,
      api_key: apiKey,
    }),
  })
  if (!res.ok) {
    throw new ApiError(res.status, 'Cihaz doğrulanamadı, bilgileri kontrol edin')
  }
  const data = (await res.json()) as DeviceAuthResult & { signing_secret: string }
  localStorage.setItem(DEVICE_SECRET_KEY, data.signing_secret)
  setAuth(data.tenant_id)
  return data
}

async function deviceSignatureHeaders(
  method: string,
  path: string,
  body: string,
): Promise<Record<string, string>> {
  const secret = getDeviceSecret()
  if (!secret || !crypto?.subtle) return {}

  const encoder = new TextEncoder()
  const bodyDigest = toHex(await crypto.subtle.digest('SHA-256', encoder.encode(body)))
  const timestamp = String(Math.floor(Date.now() / 1000))
  const nonceBytes = new Uint8Array(16)
  crypto.getRandomValues(nonceBytes)
  const nonce = Array.from(nonceBytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')

  const canonical = [method.toUpperCase(), path, timestamp, nonce, bodyDigest].join('\n')
  const key = await crypto.subtle.importKey(
    'raw',
    base64UrlToBytes(secret) as unknown as ArrayBuffer,
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign'],
  )
  const signature = await crypto.subtle.sign('HMAC', key, encoder.encode(canonical))

  return {
    [DEVICE_TIMESTAMP_HEADER]: timestamp,
    [DEVICE_NONCE_HEADER]: nonce,
    [DEVICE_SIGNATURE_HEADER]: toHex(signature),
  }
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

  // Signed over the exact bytes sent — re-serializing would break the digest.
  const bodyText = JSON.stringify(payload)
  const devicePath = '/api/v1/devices/qr/validate'
  const signature = await deviceSignatureHeaders('POST', devicePath, bodyText)

  let res = await fetch(`${base}${devicePath}`, {
    method: 'POST',
    headers: { ...headers, ...signature },
    body: bodyText,
    credentials: 'include',
  })

  if (res.status === 401 || res.status === 404) {
    res = await fetch(`${base}/api/v1/access/qr/validate`, {
      method: 'POST',
      headers,
      body: bodyText,
      credentials: 'include',
    })
  }

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
