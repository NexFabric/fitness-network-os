import { test, expect, type Page } from '@playwright/test'

/**
 * The full commercial round trip, which was impossible before the plan
 * catalogue landed: create a product, price it, publish it, sell it to a member,
 * then act on the resulting membership.
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

test('owner prices a plan, publishes it, and starts a membership with it', async ({
  page,
}) => {
  const stamp = Date.now()
  const planName = `E2E Plan ${stamp}`
  const memberName = `Abone${stamp}`

  await login(page, OWNER)

  // 1. Product + price
  await page.goto('/plans')
  await expect(page.getByRole('heading', { name: 'Planlar', exact: true })).toBeVisible()
  await page.fill('#plan_name', planName)
  await page.getByRole('button', { name: 'Plan oluştur' }).click()
  await expect(page.getByText('Plan oluşturuldu.', { exact: false })).toBeVisible()

  await page.selectOption('#version_plan', { label: planName })
  await page.fill('#version_price', '499,90')
  await page.fill('#version_cycle', '1')
  await page.getByRole('button', { name: 'Sürüm ekle' }).click()
  await expect(page.getByText('Sürüm 1 taslak olarak oluşturuldu.')).toBeVisible()

  // Money is rendered from minor units, so the comma survives the round trip.
  const row = page.getByRole('row', { name: new RegExp(planName) })
  await expect(row.getByText('499,90 TRY')).toBeVisible()

  // 2. A draft is not sellable until published, and publishing is one-way.
  await row.getByRole('button', { name: 'Yayımla' }).click()
  const dialog = page.getByRole('dialog', { name: 'Sürüm yayımlansın mı?' })
  await expect(dialog).toContainText('düzenlenemez')
  await dialog.getByRole('button', { name: 'Yayımla' }).click()
  await expect(page.getByText('yayımlandı ve artık satılabilir', { exact: false })).toBeVisible()
  await expect(row.getByText('Satılabilir')).toBeVisible()

  // 3. A member to sell it to
  await page.goto('/members')
  // The create form is collapsed behind the header button.
  await page.getByRole('button', { name: 'Üye oluştur' }).click()
  await page.fill('#member_number', `M-${stamp}`)
  await page.fill('#first_name', memberName)
  await page.fill('#last_name', 'Test')
  await page.locator('form').getByRole('button', { name: 'Üye oluştur' }).click()
  const memberRow = page.getByRole('row', { name: new RegExp(memberName) })
  await expect(memberRow).toBeVisible()
  // The membership panel lives in the member's edit modal.
  await memberRow.getByRole('button', { name: 'Düzenle' }).click()

  // 4. Sell it
  const starter = page.getByLabel('Plan sürümü')
  await expect(starter).toBeVisible()
  // selectOption takes exact labels only; resolve the option by its text.
  const optionValue = await starter
    .locator('option', { hasText: `${planName} v1` })
    .getAttribute('value')
  expect(optionValue).toBeTruthy()
  await starter.selectOption(optionValue as string)
  await page.getByRole('button', { name: 'Başlat', exact: true }).click()
  await expect(page.getByText('Abonelik başlatıldı.')).toBeVisible()
  await expect(page.getByText('Aktif', { exact: true })).toBeVisible()

  // 5. And the lifecycle surface now has something real to act on.
  await page.getByRole('button', { name: 'Dondur' }).click()
  await page.fill('input[id^="freeze_reason_"]', 'tatil')
  await page.getByRole('button', { name: 'Onayla' }).click()
  await expect(page.getByText('Abonelik donduruldu.')).toBeVisible()
  await expect(page.getByText('Dondurulmuş', { exact: true })).toBeVisible()

  await page.getByRole('button', { name: 'Dondurmayı kaldır' }).click()
  await expect(page.getByText('Dondurma kaldırıldı.')).toBeVisible()
})

test('a member cannot reach the plan catalogue', async ({ page }) => {
  await login(page, 'e2e.member@e2e.local')
  await page.goto('/plans')
  await expect(page).not.toHaveURL(/\/plans$/)
})
