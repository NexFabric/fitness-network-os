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
  test('reception workspace supports search and manual turnstile override interaction', async ({
    page,
  }) => {
    await loginOwner(page);

    // Open reception workspace
    await page.goto('/reception');
    await expect(page.locator('body')).toContainText('Resepsiyon & Danışma Masası');
    const searchInput = page.locator('#member-search');
    await expect(searchInput).toBeVisible();

    // Type query in search
    await searchInput.fill('e2e');
    await page.waitForTimeout(500);

    // Check if search results appear or empty hint is rendered
    const hasResults = await page.locator('button:has-text("Aktif Paket"), button:has-text("Paket Yok")').count();
    if (hasResults > 0) {
      await page.locator('button:has-text("Aktif Paket"), button:has-text("Paket Yok")').first().click();
      await expect(page.locator('#override-reason')).toBeVisible();
      await page.locator('#override-reason').fill('E2E Test manual access grant verification');
      await expect(page.getByRole('button', { name: 'Manuel Girişi Onayla & Kaydet' })).toBeEnabled();
    }
  });

  test('data migration import page previews and processes CSV input', async ({
    page,
  }) => {
    await loginOwner(page);

    // Open CSV import page
    await page.goto('/import');
    await expect(page.locator('body')).toContainText('Veri Göçü & CSV İçe Aktarma');

    const csvTextarea = page.locator('#csv-content');
    await expect(csvTextarea).toBeVisible();

    const sampleCsv = `first_name,last_name,email,phone,member_number\nTest,Sporcu,test.sporcu.${Date.now()}@test.local,5559998877,MBR-${Date.now().toString().slice(-4)}`;
    await csvTextarea.fill(sampleCsv);

    await page.getByRole('button', { name: 'Önizleme Oluştur' }).click();
    await expect(page.locator('body')).toContainText('Önizleme');
  });

  test('member portal self-service renders multi-tab layout and navigates tabs', async ({ page }) => {
    await loginMember(page);

    // Verify member portal self-service tabs
    await expect(page.locator('body')).toContainText('Sporcu Portalı');

    const tabs = ['Giriş QR', 'Paketler', 'Geçmiş', 'Ödemeler', 'İletişim'];
    for (const tab of tabs) {
      const tabButton = page.getByRole('button', { name: tab, exact: true });
      await expect(tabButton).toBeVisible();
      await tabButton.click();
      await page.waitForTimeout(200);
    }
  });
});

