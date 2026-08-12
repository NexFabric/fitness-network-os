import { test, expect } from '@playwright/test';

test.describe('Admin Web Cookie Auth & Operations', () => {
  test('should load login page and display GymClubNex branding', async ({ page }) => {
    await page.goto('http://localhost:5173/login');
    await expect(page.locator('body')).toContainText('GymClubNex');
  });

  test('should authenticate with demo credentials and load dashboard', async ({ page }) => {
    await page.goto('http://localhost:5173/login');
    await page.fill('input[type="email"]', 'demo.admin@demo.local');
    await page.fill('input[type="password"]', 'DemoAdmin123!');
    await page.click('button[type="submit"]');

    // Dashboard should display Operations header
    await expect(page.locator('body')).toContainText('Operasyonlar');
  });
});
