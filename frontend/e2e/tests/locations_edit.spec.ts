import { test, expect } from '@playwright/test'

test('owner edits a location and the list reflects it', async ({ page }) => {
  const stamp = Date.now()
  await page.goto('/login')
  await page.fill('input[type="email"]', 'e2e.owner@e2e.local')
  await page.fill('input[type="password"]', 'E2ePortal123!')
  await page.click('button[type="submit"]')
  await page.waitForURL((u) => !u.pathname.startsWith('/login'))

  await page.goto('/locations')
  await page.fill('#location_name', `Düzenlenecek ${stamp}`)
  await page.click('form button[type="submit"]')
  await expect(page.getByText('Şube başarıyla oluşturuldu.')).toBeVisible()

  const row = page.getByRole('row', { name: new RegExp(`Düzenlenecek ${stamp}`) })
  await row.getByRole('button', { name: 'Düzenle' }).click()
  const dialog = page.getByRole('dialog', { name: 'Şubeyi düzenle' })
  await expect(dialog).toBeVisible()
  await dialog.locator('#edit_location_name').fill(`Yeni ad ${stamp}`)
  await dialog.locator('#edit_location_address').fill('Bağdat Cad. 1')
  await dialog.getByRole('button', { name: 'Kaydet' }).click()

  await expect(page.getByText('Şube güncellendi.')).toBeVisible()
  // Scope to the edited row: earlier runs leave rows with the same address.
  const updated = page.getByRole('row', { name: new RegExp(`Yeni ad ${stamp}`) })
  await expect(updated).toBeVisible()
  await expect(updated.getByText('Bağdat Cad. 1')).toBeVisible()
})
