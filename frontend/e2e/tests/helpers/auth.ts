import { createHmac } from 'node:crypto'
import type { Page } from '@playwright/test'

const OWNER_EMAIL = 'e2e.owner@e2e.local'
const OWNER_TOTP_SECRET =
  process.env.E2E_OWNER_TOTP_SECRET ?? 'JBSWY3DPEHPK3PXP'

function decodeBase32(value: string): Buffer {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567'
  const bits = value
    .replace(/=+$/u, '')
    .toUpperCase()
    .split('')
    .map((character) => alphabet.indexOf(character).toString(2).padStart(5, '0'))
    .join('')
  const bytes: number[] = []
  for (let index = 0; index + 8 <= bits.length; index += 8) {
    bytes.push(Number.parseInt(bits.slice(index, index + 8), 2))
  }
  return Buffer.from(bytes)
}

export function currentOwnerTotp(now = Date.now()): string {
  const counter = Math.floor(now / 30_000)
  const message = Buffer.alloc(8)
  message.writeBigUInt64BE(BigInt(counter))
  const digest = createHmac('sha1', decodeBase32(OWNER_TOTP_SECRET))
    .update(message)
    .digest()
  const offset = digest[digest.length - 1] & 0x0f
  const binary =
    (((digest[offset] & 0x7f) << 24) |
      ((digest[offset + 1] & 0xff) << 16) |
      ((digest[offset + 2] & 0xff) << 8) |
      (digest[offset + 3] & 0xff)) >>>
    0
  return String(binary % 1_000_000).padStart(6, '0')
}

const STAFF_MFA_EMAILS = new Set([
  OWNER_EMAIL,
  'e2e.trainer@e2e.local',
  'e2e.analyst@e2e.local',
  'e2e.desk@e2e.local',
])

export async function completeOwnerMfaIfNeeded(page: Page, email: string) {
  if (!STAFF_MFA_EMAILS.has(email)) return
  const field = page.locator('#mfa-code')
  const outcome = await Promise.race([
    field.waitFor({ state: 'visible', timeout: 10_000 }).then(() => 'mfa' as const),
    page
      .waitForURL((url) => !url.pathname.startsWith('/login'), { timeout: 10_000 })
      .then(() => 'done' as const),
  ]).catch(() => 'missing' as const)
  if (outcome !== 'mfa') return
  await field.fill(currentOwnerTotp())
  await page.locator('button[type="submit"]').click()
}

export const E2E_PASSWORD = 'E2ePortal123!'
export const E2E_OWNER = OWNER_EMAIL

export function acceptOwnerStepUp(page: Page) {
  page.on('dialog', async (dialog) => {
    const message = dialog.message()
    if (message.includes('TOTP') || message.includes('doğrulama')) {
      await dialog.accept(currentOwnerTotp())
      return
    }
    await dialog.dismiss()
  })
}

export async function loginAsOwner(page: Page, email = E2E_OWNER) {
  await page.goto('/login')
  await page.locator('input[type="email"]').fill(email)
  await page.locator('input[type="password"]').fill(E2E_PASSWORD)
  await page.locator('button[type="submit"]').click()
  await completeOwnerMfaIfNeeded(page, email)
  await page.waitForURL((url) => !url.pathname.startsWith('/login'), {
    timeout: 15_000,
  })
}

const API = process.env.E2E_API_URL ?? 'http://127.0.0.1:8000'

export async function stepUpOwner(page: Page) {
  const code = currentOwnerTotp()
  const result = await page.evaluate(
    async ({ api, totp }) => {
      const boot = await fetch(`${api}/api/v1/auth/csrf`, { credentials: 'include' })
      const csrfJson = (await boot.json()) as { csrf_token?: string }
      const tenantId = localStorage.getItem('fnos_tenant_id')
      const headers: Record<string, string> = {
        Accept: 'application/json',
        'Content-Type': 'application/json',
      }
      if (csrfJson.csrf_token) headers['x-csrf-token'] = csrfJson.csrf_token
      if (tenantId) headers['X-Tenant-ID'] = tenantId
      const res = await fetch(`${api}/api/v1/auth/mfa/step-up`, {
        method: 'POST',
        credentials: 'include',
        headers,
        body: JSON.stringify({ code: totp }),
      })
      return { ok: res.ok, status: res.status, text: await res.text() }
    },
    { api: API, totp: code },
  )
  if (!result.ok) {
    throw new Error(`step-up failed: ${result.status} ${result.text}`)
  }
}
