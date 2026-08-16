import { test, expect } from '@playwright/test'
import { completeOwnerMfaIfNeeded } from './helpers/auth'

const PASSWORD = 'E2ePortal123!'
const OWNER = 'e2e.owner@e2e.local'

test('owner can provision a staff account and see the one-time password once', async ({
  page,
}) => {
  await page.goto('/login')
  await page.fill('input[type="email"]', OWNER)
  await page.fill('input[type="password"]', PASSWORD)
  await page.click('button[type="submit"]')
  await completeOwnerMfaIfNeeded(page, OWNER)
  await page.waitForURL((url) => !url.pathname.startsWith('/login'), {
    timeout: 15_000,
  })

  await page.goto('/staff')
  await expect(page.getByRole('heading', { name: 'Personel', exact: true })).toBeVisible()

  const email = `e2e.hire.${Date.now()}@e2e.local`
  await page.fill('#new_staff_email', email)
  await page.locator('#new_staff_role').selectOption('FRONT_DESK')
  await page.getByRole('button', { name: 'Hesap oluştur' }).click()

  await expect(page.getByText('Davet yalnızca şimdi görünür')).toBeVisible({
    timeout: 15_000,
  })
  await expect(page.getByText(email)).toBeVisible()
  const secret = page.locator('code.select-all')
  await expect(secret).toBeVisible()
  await expect(secret).toHaveText(/.{16,}/)
})
