import { test, expect, type Page } from '@playwright/test'
import { completeOwnerMfaIfNeeded } from './helpers/auth'

/**
 * Every portal must render without console errors or failed requests.
 *
 * Project rule: after any UI change, check the browser console. Asserting it
 * here means the check runs on every CI run instead of depending on someone
 * remembering to open devtools.
 */

const PASSWORD = 'E2ePortal123!'

const PORTALS = [
  { email: 'e2e.member@e2e.local', path: '/member', label: 'sporcu portalı' },
  { email: 'e2e.trainer@e2e.local', path: '/trainer', label: 'antrenör portalı' },
  { email: 'e2e.analyst@e2e.local', path: '/superadmin', label: 'federasyon konsolu' },
  { email: 'e2e.owner@e2e.local', path: '/', label: 'ops konsolu' },
  { email: 'e2e.member@e2e.local', path: '/portal', label: 'portal geçidi' },
] as const

/** React dev-mode noise that says nothing about this app's behaviour. */
const IGNORED = [
  /Download the React DevTools/i,
  /\[vite\]/i,
  /favicon/i,
]

function collect(page: Page) {
  const errors: string[] = []
  page.on('console', (msg) => {
    if (msg.type() !== 'error') return
    const text = msg.text()
    if (IGNORED.some((re) => re.test(text))) return
    errors.push(text)
  })
  page.on('pageerror', (err) => errors.push(`pageerror: ${err.message}`))
  return errors
}

for (const portal of PORTALS) {
  test(`${portal.label} renders without console errors`, async ({ page }) => {
    const errors = collect(page)

    await page.goto('/login')
    await page.fill('input[type="email"]', portal.email)
    await page.fill('input[type="password"]', PASSWORD)
    await page.click('button[type="submit"]')
    await completeOwnerMfaIfNeeded(page, portal.email)
    await page.waitForURL((url) => !url.pathname.startsWith('/login'), {
      timeout: 15_000,
    })

    // Measure the portal itself, not the login round-trip that got us here.
    errors.length = 0

    await page.goto(portal.path)
    // Let data fetches settle so a failed XHR surfaces before we assert.
    await page.waitForLoadState('networkidle')

    expect(errors, `console errors on ${portal.path}`).toEqual([])
  })
}
