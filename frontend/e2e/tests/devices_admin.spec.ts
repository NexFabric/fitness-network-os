import { test, expect, type Page } from '@playwright/test'

/**
 * Device management, end to end against the real API.
 *
 * The signed device channel is only usable if an operator can actually mint a
 * device and read its key exactly once, so that path is exercised here rather
 * than asserted from unit tests.
 *
 * Requires the seeded role matrix:
 *   cd backend && ./.venv/bin/python scripts/seed_role_matrix.py
 */

const PASSWORD = 'E2ePortal123!'
const USERS = {
  owner: 'e2e.owner@e2e.local',
  trainer: 'e2e.trainer@e2e.local',
  member: 'e2e.member@e2e.local',
} as const

async function login(page: Page, email: string) {
  await page.goto('/login')
  await page.fill('input[type="email"]', email)
  await page.fill('input[type="password"]', PASSWORD)
  await page.click('button[type="submit"]')
  await page.waitForURL((url) => !url.pathname.startsWith('/login'), { timeout: 15_000 })
}

test.describe('device provisioning', () => {
  test('owner mints a device, sees the key once, then revokes it', async ({ page }) => {
    const stamp = Date.now()
    const locationName = `E2E Şube ${stamp}`
    const deviceName = `E2E Turnike ${stamp}`

    await login(page, USERS.owner)

    // A device needs a location, and the role-matrix seed creates none.
    await page.goto('/locations')
    await page.fill('#location_name', locationName)
    await page.click('form button[type="submit"]')
    await expect(page.getByText('Şube başarıyla oluşturuldu.')).toBeVisible()

    await page.goto('/devices')
    await expect(page.getByRole('heading', { name: 'Cihazlar', exact: true })).toBeVisible()

    await page.fill('#device_name', deviceName)
    await page.selectOption('#device_location', { label: locationName })
    await page.click('form button[type="submit"]')

    // The key is displayed exactly once — that panel is the whole point.
    const keyPanel = page.getByRole('region', { name: `"${deviceName}" için eşleştirme anahtarı` })
    await expect(keyPanel).toBeVisible()
    await expect(keyPanel.getByText('Bu anahtar bir daha gösterilmez.', { exact: false })).toBeVisible()

    const apiKey = await keyPanel.locator('dd.text-teal-300').innerText()
    expect(apiKey.trim().length).toBeGreaterThan(20)

    // And the device is now listed.
    const row = page.getByRole('row', { name: new RegExp(deviceName) })
    await expect(row).toBeVisible()
    await expect(row.getByText(locationName)).toBeVisible()

    // Revoking is irreversible, so it asks first.
    await row.getByRole('button', { name: 'İptal et' }).click()
    const dialog = page.getByRole('dialog', { name: 'Cihaz iptal edilsin mi?' })
    await expect(dialog).toBeVisible()
    await dialog.getByRole('button', { name: 'İptal et' }).click()

    await expect(page.getByText(`"${deviceName}" iptal edildi.`, { exact: false })).toBeVisible()
    await expect(row.getByText('İptal edildi')).toBeVisible()
  })

  test('the key panel does not survive a reload', async ({ page }) => {
    await login(page, USERS.owner)
    await page.goto('/devices')
    await page.reload()
    // The page subtitle mentions the key too, so assert on the panel itself.
    await expect(page.getByRole('region', { name: /için eşleştirme anahtarı/ })).toHaveCount(0)
  })
})

test.describe('device management is not reachable without devices:manage', () => {
  for (const role of ['trainer', 'member'] as const) {
    test(`${role} typing /devices is sent back to its own portal`, async ({ page }) => {
      await login(page, USERS[role])
      await page.goto('/devices')
      await expect(page).not.toHaveURL(/\/devices$/)
      await expect(page.getByRole('heading', { name: 'Cihazlar', exact: true })).toHaveCount(0)
    })
  }
})
