import { test, expect } from '@playwright/test'
import { acceptOwnerStepUp, loginAsOwner } from './helpers/auth'

test('owner binds a portal account and receives an invite token', async ({ page }) => {
  acceptOwnerStepUp(page)
  await loginAsOwner(page)
  await page.goto('/members')
  await page.getByRole('button', { name: 'Üye oluştur' }).click()

  const stamp = Date.now()
  const first = `Portal${stamp}`
  await page.locator('#member_number').fill(`P-${stamp}`)
  await page.locator('#first_name').fill(first)
  await page.locator('#last_name').fill('Hesap')
  await page.locator('form').getByRole('button', { name: 'Üye oluştur' }).click()
  const row = page.getByRole('row', { name: new RegExp(first) })
  await expect(row).toBeVisible()
  await row.getByRole('button', { name: 'Düzenle' }).click()

  await expect(page.getByRole('heading', { name: /Üye Detayı/ })).toBeVisible()
  await page.locator('#edit_email').fill(`portal.${stamp}@e2e.local`)
  const posted = page.waitForResponse(
    (res) =>
      res.url().includes('/portal-account') &&
      res.request().method() === 'POST' &&
      res.status() === 201,
  )
  await page.getByRole('button', { name: 'Portal hesabı aç' }).click()
  await posted
  await expect(page.getByText(/Davet jetonu/)).toBeVisible({ timeout: 20_000 })
})
