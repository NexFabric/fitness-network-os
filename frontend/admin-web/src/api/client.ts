const TENANT_KEY = 'fnos_tenant_id'

/** In-memory CSRF (API origin cookie is not readable cross-origin from :5173). */
let csrfToken: string | null = null

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

/** Persist tenant id only — never store session secrets in localStorage. */
export function setAuth(tenantId: string): void {
  localStorage.setItem(TENANT_KEY, tenantId)
}

export function clearAuth(): void {
  localStorage.removeItem(TENANT_KEY)
  csrfToken = null
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
  /** Skip X-Tenant-ID (public routes). */
  skipAuth?: boolean
  /** Skip CSRF header (e.g. bootstrap). */
  skipCsrf?: boolean
  /** Do not prompt for TOTP step-up on 403 step_up_required. */
  skipStepUp?: boolean
}

/**
 * Bootstrap CSRF for cross-origin admin → API.
 * GET /api/v1/auth/csrf sets cookie on API origin and returns token JSON.
 */
export async function ensureCsrf(): Promise<string> {
  if (csrfToken) return csrfToken
  const base = getBaseUrl()
  const res = await fetch(`${base}/api/v1/auth/csrf`, {
    method: 'GET',
    credentials: 'include',
    headers: { Accept: 'application/json' },
  })
  if (!res.ok) {
    throw new ApiError(res.status, 'CSRF bootstrap failed')
  }
  const data = (await res.json()) as { csrf_token?: string }
  if (!data.csrf_token) {
    throw new ApiError(500, 'CSRF bootstrap missing token')
  }
  csrfToken = data.csrf_token
  return csrfToken
}

/**
 * Fetch wrapper for GymClubNex API.
 * Auth: HttpOnly session cookie (credentials: include) + X-Tenant-ID.
 * CSRF: in-memory token from ensureCsrf() for unsafe methods.
 */
export async function api<T = unknown>(
  path: string,
  options: ApiOptions = {},
): Promise<T> {
  const base = getBaseUrl()
  const url = path.startsWith('http')
    ? path
    : `${base}${path.startsWith('/') ? '' : '/'}${path}`

  const method =
    options.method ?? (options.body !== undefined ? 'POST' : 'GET')

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

  const unsafe =
    method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS'
  if (unsafe && !options.skipCsrf) {
    const token = await ensureCsrf()
    headers['x-csrf-token'] = token
  }

  const res = await fetch(url, {
    method,
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    credentials: 'include',
  })

  // Capture refreshed CSRF from JSON error body not available; re-bootstrap on 403
  if (res.status === 403 && unsafe && !options.skipCsrf) {
    csrfToken = null
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

  if (!res.ok) {
    const detailPeek =
      typeof data === 'object' && data !== null && 'detail' in data
        ? String((data as { detail: unknown }).detail)
        : ''
    if (
      res.status === 403 &&
      detailPeek === 'step_up_required' &&
      !options.skipStepUp &&
      typeof window !== 'undefined'
    ) {
      const code = window.prompt('Bu işlem için doğrulama kodu (TOTP) gerekli:')
      if (code && code.trim()) {
        await api('/api/v1/auth/mfa/step-up', {
          method: 'POST',
          body: { code: code.trim() },
          skipStepUp: true,
        })
        return api<T>(path, { ...options, skipStepUp: true })
      }
    }
    if (res.status === 401 && !options.skipAuth) {
      clearAuth()
      if (
        typeof window !== 'undefined' &&
        !window.location.pathname.startsWith('/login')
      ) {
        const next = `${window.location.pathname}${window.location.search}`
        window.location.assign(
          `/login?reason=session&from=${encodeURIComponent(next)}`,
        )
      }
    }
    const detail =
      typeof data === 'object' && data !== null && 'detail' in data
        ? String((data as { detail: unknown }).detail)
        : res.statusText || 'Request failed'
    throw new ApiError(res.status, detail, data)
  }

  return data as T
}

/**
 * Helper to normalize and translate API error messages into Turkish user-facing text.
 */
export function formatApiError(e: unknown, fallback: string): string {
  if (e instanceof ApiError) {
    if (e.status === 401) return 'Oturum süreniz doldu, lütfen tekrar giriş yapın.'
    if (e.status === 403) return 'Bu işlem için yetkiniz yok.'
    if (e.status === 404) return 'İstenen kaynak bulunamadı.'
    if (e.status === 409) return e.message || 'Bu işlem başka bir kayıtla çakışıyor.'
    if (e.status === 422) {
      if (typeof e.body === 'object' && e.body !== null && 'detail' in e.body) {
        const detail = (e.body as { detail: unknown }).detail
        if (Array.isArray(detail) && detail.length > 0) {
          const first = detail[0]
          if (typeof first === 'object' && first !== null && 'msg' in first) {
            return String(first.msg)
          }
        }
      }
      return 'Lütfen form alanlarını kontrol edin.'
    }
    if (e.status >= 500) return 'Sunucu hatası oluştu, lütfen daha sonra tekrar deneyin.'
    return e.message || fallback
  }
  if (e instanceof Error) return e.message
  return fallback
}

