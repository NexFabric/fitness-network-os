import { test, expect, type Page } from '@playwright/test'

/**
 * The operations surfaces added on top of endpoints that had no UI:
 * notifications, reports and staff.
 *
 * Each one is exercised against the real API rather than asserted from a
 * screenshot — a page that renders but cannot write is not a delivered feature.
 */

const PASSWORD = 'E2ePortal123!'
const OWNER = 'e2e.owner@e2e.local'

async function login(page: Page, email: string) {
  await page.goto('/login')
  await page.fill('input[type="email"]', email)
  await page.fill('input[type="password"]', PASSWORD)
  await page.click('button[type="submit"]')
  await page.waitForURL((url) => !url.pathname.startsWith('/login'), { timeout: 15_000 })
}

test.describe('notifications', () => {
  test('owner creates a template and it appears in the list', async ({ page }) => {
    const stamp = Date.now()
    const code = `e2e_sablon_${stamp}`

    await login(page, OWNER)
    await page.goto('/notifications')
    await expect(page.getByRole('heading', { name: 'Bildirimler', exact: true })).toBeVisible()

    await page.fill('#tpl_code', code)
    await page.fill('#tpl_name', `E2E Şablon ${stamp}`)
    await page.fill('#tpl_body', 'Merhaba, üyeliğiniz yakında bitiyor.')
    await page.locator('form').filter({ has: page.locator('#tpl_code') }).getByRole('button', { name: 'Şablon oluştur' }).click()

    await expect(page.getByText('Şablon oluşturuldu.')).toBeVisible()
    await expect(page.getByRole('row', { name: new RegExp(code) })).toBeVisible()
  })

  test('a delivery without a recipient is refused inline, not by a browser dialog', async ({
    page,
  }) => {
    await login(page, OWNER)
    await page.goto('/notifications')
    await page
      .locator('form')
      .filter({ has: page.locator('#send_to') })
      .getByRole('button', { name: 'Gönderimi planla' })
      .click()
    await expect(page.getByText('Alıcı adresi gereklidir.')).toBeVisible()
  })
})

test.describe('reports', () => {
  test('owner creates a definition and runs it', async ({ page }) => {
    const stamp = Date.now()
    const code = `e2e_rapor_${stamp}`

    await login(page, OWNER)
    await page.goto('/reports')
    await expect(page.getByRole('heading', { name: 'Raporlar', exact: true })).toBeVisible()

    await page.fill('#def_code', code)
    await page.fill('#def_name', `E2E Rapor ${stamp}`)
    await page.getByRole('button', { name: 'Tanım oluştur' }).click()
    await expect(page.getByText('Rapor tanımı oluşturuldu.')).toBeVisible()

    const item = page.locator('li').filter({ hasText: code })
    await expect(item).toBeVisible()
    await item.getByRole('button', { name: 'Çalıştır' }).click()

    // The run is queued or already finished — either way the panel appears and
    // the status is rendered rather than swallowed.
    await expect(item.getByRole('button', { name: 'Durumu yenile' })).toBeVisible()
  })
})

test.describe('staff', () => {
  test('a malformed user id is rejected before any request', async ({ page }) => {
    await login(page, OWNER)
    await page.goto('/staff')
    await expect(page.getByRole('heading', { name: 'Personel', exact: true })).toBeVisible()

    await page.fill('#staff_user_id', 'not-a-uuid')
    await page.getByRole('button', { name: 'Personel bağla' }).click()
    await expect(page.getByText('Geçerli bir kullanıcı ID (UUID) girin.')).toBeVisible()
  })
})

test.describe('ops surfaces stay behind their roles', () => {
  for (const path of ['/notifications', '/reports', '/staff']) {
    test(`a member typing ${path} is sent back to its own portal`, async ({ page }) => {
      await login(page, 'e2e.member@e2e.local')
      await page.goto(path)
      await expect(page).not.toHaveURL(new RegExp(`${path}$`))
    })
  }
})
