import { test, expect } from '@playwright/test';

test.describe('Scanner PWA Access Verification', () => {
  test('should load scanner interface and display Access brand', async ({ page }) => {
    await page.goto('http://localhost:5174/');
    await expect(page.locator('body')).toContainText('GymClubNex');
  });
});
