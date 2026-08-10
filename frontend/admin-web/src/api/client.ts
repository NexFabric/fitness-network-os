const TOKEN_KEY = 'fnos_access_token'
const TENANT_KEY = 'fnos_tenant_id'

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

export function isAuthenticated(): boolean {
  return Boolean(getTenantId())
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

export type ApiOptions = {
  method?: string
  body?: unknown
  headers?: Record<string, string>
  /** Skip Authorization / X-Tenant-ID (unused on public routes). */
  skipAuth?: boolean
}

/**
 * Fetch wrapper for GymClubNex API.
 * Sends Authorization: Bearer <token> and X-Tenant-ID from localStorage.
 */
export async function api<T = unknown>(
  path: string,
  options: ApiOptions = {},
): Promise<T> {
  const base = getBaseUrl()
  const url = path.startsWith('http') ? path : `${base}${path.startsWith('/') ? '' : '/'}${path}`

  const headers: Record<string, string> = {
    Accept: 'application/json',
    ...options.headers,
  }

  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }

  if (!options.skipAuth) {
    const tenantId = getTenantId()
    if (tenantId) {
      headers['X-Tenant-ID'] = tenantId
    }
  }

  // Parse CSRF cookie if available and method is unsafe
  const method = options.method ?? (options.body !== undefined ? 'POST' : 'GET')
  if (method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS') {
    const match = document.cookie.match(/(?:^|; )csrf_token=([^;]*)/)
    if (match) {
      headers['x-csrf-token'] = match[1]
    }
  }

  const res = await fetch(url, {
    method: options.method ?? (options.body !== undefined ? 'POST' : 'GET'),
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    // Include cookies so HttpOnly session auth works alongside Bearer/localStorage.
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

  if (!res.ok) {
    const detail =
      typeof data === 'object' && data !== null && 'detail' in data
        ? String((data as { detail: unknown }).detail)
        : res.statusText || 'Request failed'
    throw new ApiError(res.status, detail, data)
  }

  return data as T
}
