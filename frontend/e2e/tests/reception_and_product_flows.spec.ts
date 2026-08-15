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
    await expect(page.locator('body')).toContainText('Resepsiyon & Danışma Masası');
    await expect(page.locator('#member-search')).toBeVisible();
  });

  test('data migration import page loads with CSV template guidelines', async ({
    page,
  }) => {
    await loginOwner(page);

    // Open CSV import page
    await page.goto('/import');
    await expect(page.locator('body')).toContainText('Veri Göçü & CSV İçe Aktarma');
    await expect(page.locator('body')).toContainText('first_name/ad, last_name/soyad, email, phone');
  });

  test('member portal self-service renders multi-tab layout', async ({ page }) => {
    await loginMember(page);

    // Verify member portal self-service tabs
    await expect(page.locator('body')).toContainText('Sporcu Portalı');
    await expect(page.getByRole('button', { name: 'Giriş QR', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Paketler', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Geçmiş', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Ödemeler', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'İletişim', exact: true })).toBeVisible();
  });
});
