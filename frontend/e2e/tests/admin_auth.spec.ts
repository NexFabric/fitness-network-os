import { test, expect } from '@playwright/test';
import { completeOwnerMfaIfNeeded } from './helpers/auth';

test.describe('Admin Web Cookie Auth & Operations', () => {
  test('should load login page and display GymClubNex branding', async ({ page }) => {
    await page.goto('http://localhost:5173/login');
    await expect(page.locator('body')).toContainText('GymClubNex');
  });

  test('should authenticate an owner with MFA and load dashboard', async ({ page }) => {
    await page.goto('http://localhost:5173/login');
    await page.fill('input[type="email"]', 'e2e.owner@e2e.local');
    await page.fill('input[type="password"]', 'E2ePortal123!');
    await page.click('button[type="submit"]');
    await completeOwnerMfaIfNeeded(page, 'e2e.owner@e2e.local');

    // Dashboard should display Operations header
    await expect(page.locator('body')).toContainText('Operasyonlar');
  });
});
