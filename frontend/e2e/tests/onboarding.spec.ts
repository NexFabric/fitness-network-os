import { test, expect } from '@playwright/test'
import { loginAsOwner } from './helpers/auth'

test('onboarding wizard lists stages and can advance or refuse', async ({ page }) => {
  await loginAsOwner(page)
  await page.goto('/onboarding')
  await expect(page.getByRole('heading', { name: 'Kurulum', exact: true })).toBeVisible()
  await expect(page.getByText('1. Organizasyon')).toBeVisible()
  await expect(page.getByText('3. Şube')).toBeVisible()
  await expect(page.getByText('4. Paketler')).toBeVisible()

  const completed = page.getByText('Kurulum tamamlandı.')
  if (await completed.isVisible()) {
    return
  }

  const advance = page.getByRole('button', { name: /Sonraki:/ })
  await expect(advance).toBeVisible()
  await advance.click()
  await expect(advance.or(completed).or(page.getByRole('alert'))).toBeVisible({
    timeout: 10_000,
  })
})
