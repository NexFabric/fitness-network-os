import { test, expect, type Page } from '@playwright/test';
import { completeOwnerMfaIfNeeded } from './helpers/auth';

const PASSWORD = 'E2ePortal123!';
const OWNER = 'e2e.owner@e2e.local';
const MEMBER = 'e2e.member@e2e.local';

async function loginOwner(page: Page) {
  await page.goto('/login');
  await page.fill('input[type="email"]', OWNER);
  await page.fill('input[type="password"]', PASSWORD);
  await page.click('button[type="submit"]');
  await completeOwnerMfaIfNeeded(page, OWNER);
  await page.waitForURL((url) => !url.pathname.startsWith('/login'), { timeout: 15_000 });
}

async function loginMember(page: Page) {
  await page.goto('/login');
  await page.fill('input[type="email"]', MEMBER);
  await page.fill('input[type="password"]', PASSWORD);
  await page.click('button[type="submit"]');
  await page.waitForURL((url) => !url.pathname.startsWith('/login'), { timeout: 15_000 });
}

test.describe('Reception Workspace & MVP Product Flows', () => {
  test('reception workspace loads and displays member search & turnstile actions', async ({
    page,
  }) => {
    await loginOwner(page);

    // Open reception workspace
    await page.goto('/reception');
    await expect(page.locator('body')).toContainText('Danışma & Resepsiyon');
    await expect(
      page.locator('input[placeholder*="İsim, telefon, e-posta veya üye no"]')
    ).toBeVisible();
  });

  test('data migration import page loads with CSV template guidelines', async ({
    page,
  }) => {
    await loginOwner(page);

    // Open CSV import page
    await page.goto('/import');
    await expect(page.locator('body')).toContainText('CSV Veri İçe Aktarma');
    await expect(page.locator('body')).toContainText('first_name, last_name, email, phone');
  });

  test('member portal self-service renders multi-tab layout', async ({ page }) => {
    await loginMember(page);

    // Verify member portal self-service tabs
    await expect(page.locator('body')).toContainText('Sporcu Portalı');
    await expect(page.getByRole('button', { name: 'Giriş QR' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Paketler' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Geçmiş' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Finans' })).toBeVisible();
  });
});
