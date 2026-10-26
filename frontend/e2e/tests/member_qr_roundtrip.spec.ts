import { test, expect } from '@playwright/test'
import { currentOwnerTotp } from './helpers/auth'

/**
 * Member issues a QR from the portal; the same token is validated once and
 * rejected on replay.
 *
 * The turnstile leg goes straight to the API rather than through the kiosk
 * camera — Playwright cannot show a physical QR to a webcam. What this covers
 * is the part that was never exercised before: the token really comes from
 * /access/qr/issue-self via the browser session, and the replay guard really
 * fires on the second use.
 *
 * Requires: cd backend && ./.venv/bin/python scripts/seed_role_matrix.py
 */

const API = 'http://localhost:8000'
const MEMBER_EMAIL = 'e2e.member@e2e.local'
const OWNER_EMAIL = 'e2e.owner@e2e.local'
const PASSWORD = 'E2ePortal123!'

test('QR issued by the member portal validates once, then replays are denied', async ({
  page,
  request,
}) => {
  await page.goto('/login')
  await page.fill('input[type="email"]', MEMBER_EMAIL)
  await page.fill('input[type="password"]', PASSWORD)
  await page.click('button[type="submit"]')
  await expect(page).toHaveURL(/\/member$/)

  // Capture the token the page actually received, so this tests the portal's
  // request rather than a request the test made up.
  const issued = page.waitForResponse(
    (res) =>
      res.url().includes('/access/qr/issue-self') && res.request().method() === 'POST',
  )
  await page.getByRole('button', { name: /Giriş QR kodu oluştur/ }).click()
  const response = await issued
  expect(response.status()).toBe(200)

  const body = (await response.json()) as { token: string }
  expect(body.token).toBeTruthy()

  await expect(page.getByAltText('Giriş QR kodu')).toBeVisible()

  // Staff principal performs the validation, as the turnstile would.
  const csrfRes = await request.get(`${API}/api/v1/auth/csrf`)
  const { csrf_token: csrf } = (await csrfRes.json()) as { csrf_token: string }

  const loginRes = await request.post(`${API}/api/v1/auth/login`, {
    data: {
      email: OWNER_EMAIL,
      password: PASSWORD,
      mfa_code: currentOwnerTotp(),
    },
  })
  expect(loginRes.ok()).toBeTruthy()
  const { tenant_id: tenantId } = (await loginRes.json()) as {
    tenant_id: string
  }

  const headers = {
    'X-Tenant-ID': tenantId,
    'x-csrf-token': csrf,
  }

  const first = await request.post(`${API}/api/v1/access/qr/validate`, {
    headers,
    data: { token: body.token },
  })
  expect(first.ok()).toBeTruthy()
  const firstBody = (await first.json()) as {
    granted: boolean
    reason?: string | null
  }
  expect(firstBody.granted).toBe(true)

  const second = await request.post(`${API}/api/v1/access/qr/validate`, {
    headers,
    data: { token: body.token },
    failOnStatusCode: false,
  })
  // Replay is singled out as 409 Conflict (other denials are 403); either way
  // the verdict is nested under `detail`. See access.py:178.
  expect(second.status()).toBe(409)
  const secondBody = (await second.json()) as {
    detail: { granted: boolean; reason?: string | null }
  }
  expect(secondBody.detail.granted).toBe(false)
  expect(secondBody.detail.reason).toBe('replay')
})

test('member portal cannot issue a QR for someone else', async ({
  page,
  request,
}) => {
  await page.goto('/login')
  await page.fill('input[type="email"]', MEMBER_EMAIL)
  await page.fill('input[type="password"]', PASSWORD)
  await page.click('button[type="submit"]')
  await expect(page).toHaveURL(/\/member$/)

  const tenantId = await page.evaluate(() =>
    localStorage.getItem('fnos_tenant_id'),
  )
  expect(tenantId).toBeTruthy()

  // Staff-only endpoint: the member must be refused even with a valid session.
  const cookies = await page.context().cookies()
  const cookieHeader = cookies
    .map((c) => `${c.name}=${c.value}`)
    .join('; ')

  const forged = await request.post(`${API}/api/v1/access/qr/issue`, {
    headers: {
      'X-Tenant-ID': tenantId as string,
      Cookie: cookieHeader,
    },
    data: {
      member_id: '00000000-0000-4000-8000-000000000000',
      ttl_seconds: 60,
    },
    failOnStatusCode: false,
  })
  expect([401, 403]).toContain(forged.status())
})
