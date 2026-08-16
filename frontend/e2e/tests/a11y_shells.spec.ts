import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'
import { loginAsOwner } from './helpers/auth'

async function assertNoBlockingViolations(page: Page, label: string) {
  const results = await new AxeBuilder({ page }).analyze()
  const blocking = results.violations.filter(
    (violation) => violation.impact === 'critical' || violation.impact === 'serious',
  )
  expect(blocking, `${label}: ${JSON.stringify(blocking, null, 2)}`).toEqual([])
}

test.describe('accessibility regression (serious/critical)', () => {
  test('login shell', async ({ page }) => {
    await page.goto('/login')
    await assertNoBlockingViolations(page, 'login')
  })

  test('owner reception shell', async ({ page }) => {
    await loginAsOwner(page)
    await page.goto('/reception')
    await expect(page.locator('body')).toBeVisible()
    await assertNoBlockingViolations(page, 'reception')
  })

  test('owner dashboard shell', async ({ page }) => {
    await loginAsOwner(page)
    // /dashboard is not registered; the catch-all lands on the index dashboard.
    await page.goto('/dashboard')
    await expect(
      page.getByRole('heading', { name: 'Operasyonlar & Gösterge Paneli' }),
    ).toBeVisible()
    await assertNoBlockingViolations(page, 'dashboard')
  })

  test('owner members shell', async ({ page }) => {
    await loginAsOwner(page)
    await page.goto('/members')
    await expect(page.getByRole('heading', { name: 'Üyeler', exact: true })).toBeVisible()
    await assertNoBlockingViolations(page, 'members')
  })

  test('owner plans shell', async ({ page }) => {
    await loginAsOwner(page)
    await page.goto('/plans')
    await expect(page.getByRole('heading', { name: 'Planlar', exact: true })).toBeVisible()
    await assertNoBlockingViolations(page, 'plans')
  })

  test('member portal shell', async ({ page }) => {
    await page.goto('/login')
    await page.locator('input[type="email"]').fill('e2e.member@e2e.local')
    await page.locator('input[type="password"]').fill('E2ePortal123!')
    await page.locator('button[type="submit"]').click()
    await page.waitForURL((url) => !url.pathname.startsWith('/login'), {
      timeout: 15_000,
    })
    await page.goto('/member')
    await expect(page.locator('body')).toBeVisible()
    await assertNoBlockingViolations(page, 'member')
  })

  test('scanner pairing shell', async ({ page }) => {
    await page.goto('http://localhost:5174/')
    await expect(page.locator('body')).toBeVisible()
    await assertNoBlockingViolations(page, 'scanner')
  })
})
