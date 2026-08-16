import { test, expect } from '@playwright/test'
import { acceptOwnerStepUp, loginAsOwner } from './helpers/auth'

test('owner provisions staff and the invite sets a password', async ({ page }) => {
  acceptOwnerStepUp(page)
  await loginAsOwner(page)
  await page.goto('/staff')
  await expect(page.getByRole('heading', { name: 'Personel', exact: true })).toBeVisible()

  const email = `e2e.invite.${Date.now()}@e2e.local`
  await page.locator('#new_staff_email').fill(email)
  await page.locator('#new_staff_role').selectOption('FRONT_DESK')
  const created = page.waitForResponse(
    (res) =>
      res.url().includes('/staff/accounts') && res.request().method() === 'POST',
  )
  await page.getByRole('button', { name: 'Hesap oluştur' }).click()
  const response = await created
  expect(response.status(), await response.text()).toBe(201)
  await expect(page.getByText('Davet yalnızca şimdi görünür')).toBeVisible({
    timeout: 15_000,
  })

  const token = (await page.locator('code.select-all').innerText()).trim()
  expect(token.length).toBeGreaterThan(16)

  await page.goto(`/invite?token=${encodeURIComponent(token)}`)
  await expect(page.getByRole('heading', { name: 'Daveti kabul et' })).toBeVisible()
  await page.locator('#invite-pass').fill('InvitePassphrase9!')
  await page.locator('#invite-confirm').fill('InvitePassphrase9!')
  await page.getByRole('button', { name: 'Parolayı kaydet' }).click()
  await expect(page.getByText(/için parola ayarlandı/)).toBeVisible()
  await expect(page.getByRole('link', { name: 'Giriş yap' })).toBeVisible()
})
