import { test, expect } from '@playwright/test';
import { completeOwnerMfaIfNeeded } from './helpers/auth';

test.describe('Reception Workspace & MVP Product Flows', () => {
  test('reception workspace loads and displays member search & turnstile actions', async ({
    page,
  }) => {
    await page.goto('http://localhost:5173/login');
    await page.fill('input[type="email"]', 'e2e.owner@e2e.local');
    await page.fill('input[type="password"]', 'E2ePortal123!');
    await page.click('button[type="submit"]');
    await completeOwnerMfaIfNeeded(page, 'e2e.owner@e2e.local');

    // Open reception workspace
    await page.goto('http://localhost:5173/reception');
    await expect(page.locator('body')).toContainText('Danışma & Resepsiyon');
    await expect(
      page.locator('input[placeholder*="İsim, telefon, e-posta veya üye no"]')
    ).toBeVisible();
  });

  test('data migration import page loads with CSV template guidelines', async ({
    page,
  }) => {
    await page.goto('http://localhost:5173/login');
    await page.fill('input[type="email"]', 'e2e.owner@e2e.local');
    await page.fill('input[type="password"]', 'E2ePortal123!');
    await page.click('button[type="submit"]');
    await completeOwnerMfaIfNeeded(page, 'e2e.owner@e2e.local');

    // Open CSV import page
    await page.goto('http://localhost:5173/import');
    await expect(page.locator('body')).toContainText('CSV Veri İçe Aktarma');
    await expect(page.locator('body')).toContainText('first_name, last_name, email, phone');
  });

  test('member portal self-service renders multi-tab layout', async ({ page }) => {
    await page.goto('http://localhost:5173/login');
    await page.fill('input[type="email"]', 'e2e.member@e2e.local');
    await page.fill('input[type="password"]', 'E2ePortal123!');
    await page.click('button[type="submit"]');

    // Verify member portal self-service tabs
    await expect(page.locator('body')).toContainText('Sporcu Portalı');
    await expect(page.locator('text=Dijital Kart & QR')).toBeVisible();
    await expect(page.locator('text=Abonelikler')).toBeVisible();
    await expect(page.locator('text=Giriş Geçmişi')).toBeVisible();
    await expect(page.locator('text=Faturalar & Ödemeler')).toBeVisible();
  });
});
