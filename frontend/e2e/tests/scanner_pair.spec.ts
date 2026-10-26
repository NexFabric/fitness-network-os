import { test, expect } from '@playwright/test'
import { acceptOwnerStepUp, loginAsOwner } from './helpers/auth'

test('owner provisions a device and the scanner pairs with the API key', async ({
  page,
  context,
}) => {
  test.setTimeout(60_000)
  const stamp = Date.now()
  const locationName = `E2E Pair Şube ${stamp}`
  const deviceName = `E2E Pair Turnike ${stamp}`

  acceptOwnerStepUp(page)
  await loginAsOwner(page)
  await page.goto('/locations')
  await page.locator('#location_name').fill(locationName)
  await page.locator('form button[type="submit"]').click()
  await expect(page.getByText('Şube başarıyla oluşturuldu.')).toBeVisible()

  await page.goto('/devices')
  await page.locator('#device_name').fill(deviceName)
  await page.locator('#device_location').selectOption({ label: locationName })
  await page.locator('form').filter({ has: page.locator('#device_name') }).locator('button[type="submit"]').click()

  const keyPanel = page.getByRole('region', {
    name: `"${deviceName}" için eşleştirme anahtarı`,
  })
  await expect(keyPanel).toBeVisible({ timeout: 15_000 })
  const deviceId = (await keyPanel.locator('dd').nth(0).innerText()).trim()
  const apiKey = (await keyPanel.locator('dd.text-teal-300').innerText()).trim()
  expect(deviceId.length).toBeGreaterThan(8)
  expect(apiKey.length).toBeGreaterThan(20)

  const tenantId = await page.evaluate(() => localStorage.getItem('fnos_tenant_id'))
  expect(tenantId).toBeTruthy()

  const scanner = await context.newPage()
  await scanner.goto('http://localhost:5174/')
  await expect(scanner.getByRole('heading', { name: 'Kapı okuyucu' })).toBeVisible()
  const toggle = scanner.getByRole('button', { name: /Cihaz eşleme/i })
  if (await toggle.getAttribute('aria-expanded') === 'false') {
    await toggle.click()
  }
  await scanner.locator('#device-id').fill(deviceId)
  await scanner.locator('#api-key').fill(apiKey)
  await scanner.locator('#tenant').fill(tenantId as string)
  const auth = scanner.waitForResponse(
    (res) => res.url().includes('/devices/auth') && res.request().method() === 'POST',
  )
  await scanner.getByRole('button', { name: 'Eşle', exact: true }).click()
  const authRes = await auth
  expect(authRes.status(), await authRes.text()).toBe(200)
  await expect(scanner.getByText('Çevrimiçi')).toBeVisible({ timeout: 15_000 })

  await scanner.getByRole('button', { name: 'Klavyeden gir' }).click()
  await scanner.locator('input').last().fill('not-a-valid-qr')
  await scanner.getByRole('button', { name: 'Doğrula' }).click()
  await expect(
    scanner.getByText(/Reddedildi|Doğrulama|bağlantı|geçiş/i).first(),
  ).toBeVisible({ timeout: 15_000 })
  await scanner.close()
})
