import { test, expect, type Page } from '@playwright/test'

/**
 * Role isolation across the portal surfaces.
 *
 * Requires the seeded role matrix:
 *   cd backend && ./.venv/bin/python scripts/seed_role_matrix.py
 *
 * These are the tests the "5 portals are live" claim actually rests on — before
 * them, every portal route was reachable by anyone who typed the URL.
 */

const PASSWORD = 'E2ePortal123!'

const USERS = {
  owner: 'e2e.owner@e2e.local',
  trainer: 'e2e.trainer@e2e.local',
  member: 'e2e.member@e2e.local',
  analyst: 'e2e.analyst@e2e.local',
} as const

async function login(page: Page, email: string) {
  await page.goto('/login')
  await page.fill('input[type="email"]', email)
  await page.fill('input[type="password"]', PASSWORD)
  await page.click('button[type="submit"]')
  // Landing is role-dependent, so just wait until we have left /login.
  await page.waitForURL((url) => !url.pathname.startsWith('/login'), {
    timeout: 15_000,
  })
}

test.describe('post-login routing is role-dependent', () => {
  test('member lands on the athlete portal', async ({ page }) => {
    await login(page, USERS.member)
    await expect(page).toHaveURL(/\/member$/)
    await expect(page.getByRole('heading', { name: 'GymClubNex' })).toBeVisible()
  })

  test('trainer lands on the trainer portal', async ({ page }) => {
    await login(page, USERS.trainer)
    await expect(page).toHaveURL(/\/trainer$/)
    await expect(
      page.getByRole('heading', { name: 'Antrenör Portalı' }),
    ).toBeVisible()
  })

  test('gym owner lands on the ops console', async ({ page }) => {
    await login(page, USERS.owner)
    await expect(page).toHaveURL(/localhost:5173\/$/)
  })

  test('federation analyst lands on the federation console', async ({ page }) => {
    await login(page, USERS.analyst)
    await expect(page).toHaveURL(/\/superadmin$/)
    await expect(
      page.getByRole('heading', { name: 'Federasyon Konsolu' }),
    ).toBeVisible()
  })
})

test.describe('cross-portal access is denied', () => {
  test('member cannot open the finance page', async ({ page }) => {
    await login(page, USERS.member)
    await page.goto('/finance')
    await expect(page).toHaveURL(/\/member$/)
    await expect(page.locator('body')).not.toContainText('Fatura')
  })

  test('member cannot open the federation console', async ({ page }) => {
    await login(page, USERS.member)
    await page.goto('/superadmin')
    await expect(page).toHaveURL(/\/member$/)
  })

  test('trainer cannot open the federation console', async ({ page }) => {
    await login(page, USERS.trainer)
    await page.goto('/superadmin')
    await expect(page).toHaveURL(/\/trainer$/)
  })

  test('anonymous visitor is sent to login, not into a portal', async ({
    page,
  }) => {
    await page.goto('/superadmin')
    await expect(page).toHaveURL(/\/login/)
  })

  test('a forged tenant id in localStorage does not grant the console', async ({
    page,
  }) => {
    // The old guard accepted any tenant id string; this asserts it no longer does.
    await page.goto('/login')
    await page.evaluate(() =>
      localStorage.setItem(
        'fnos_tenant_id',
        '00000000-0000-4000-8000-000000000000',
      ),
    )
    await page.goto('/members')
    await expect(page).toHaveURL(/\/login/)
  })
})

test.describe('portal gateway reflects roles', () => {
  test('member sees only its own portal card', async ({ page }) => {
    await login(page, USERS.member)
    await page.goto('/portal')
    await expect(page.getByText('Sporcu Portalı')).toBeVisible()
    await expect(page.getByText('Federasyon Konsolu')).toHaveCount(0)
    await expect(page.getByText('Kulüp Operasyon Konsolu')).toHaveCount(0)
  })
})

test.describe('trainer sees only assigned members', () => {
  test('assigned member listed, unassigned member absent', async ({ page }) => {
    await login(page, USERS.trainer)
    await expect(page.getByText('E2E Sporcu')).toBeVisible()
    await expect(page.getByText('Atanmamis Uye')).toHaveCount(0)
  })
})
