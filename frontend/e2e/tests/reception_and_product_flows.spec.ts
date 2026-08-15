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
  test('reception workspace supports search, detail display, and manual turnstile override submit', async ({
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
    const resultCard = page.locator('button:has-text("Aktif Paket"), button:has-text("Paket Yok")').first();
    await expect(resultCard).toBeVisible({ timeout: 10_000 });
    await resultCard.click();

    // Verify member detail view loaded
    await expect(page.getByText('Abonelik Durumu')).toBeVisible();
    await expect(page.getByText('Manuel Turnike / Giriş Onayı (Override)')).toBeVisible();

    // Fill override reason
    const reasonInput = page.locator('#override-reason');
    await expect(reasonInput).toBeVisible();
    await reasonInput.fill('E2E Manual entry override verified by desk staff');

    // Confirm override
    const submitBtn = page.getByRole('button', { name: 'Manuel Girişi Onayla & Kaydet' });
    await expect(submitBtn).toBeEnabled();
    await submitBtn.click();

    // Verify success banner and history reload
    await expect(page.getByText('Manuel giriş başarıyla onaylandı ve kaydedildi.')).toBeVisible();
    await expect(page.getByText('Başarılı Giriş').first()).toBeVisible();
  });

  test('data migration import page previews CSV input, commits batch, and updates status', async ({
    page,
  }) => {
    await loginOwner(page);

    // Open CSV import page
    await page.goto('/import');
    await expect(page.locator('body')).toContainText('Veri Göçü & CSV İçe Aktarma');

    const stamp = Date.now();
    const filename = `import_${stamp}.csv`;
    const testMemberNumber = `MBR-${stamp.toString().slice(-4)}`;
    const testEmail = `e2e.import.${stamp}@test.local`;

    await page.locator('#csv-filename').fill(filename);
    const csvContent = `first_name,last_name,email,phone,member_number\nE2E,ImportUser,${testEmail},5551234567,${testMemberNumber}`;
    await page.locator('#csv-content').fill(csvContent);

    // Generate Preview
    await page.getByRole('button', { name: 'CSV Doğrula ve Önizleme Oluştur' }).click();

    // Verify Preview & Staging Table
    await expect(page.getByText('geçerli üye aktarılmaya hazır')).toBeVisible();
    await expect(page.getByText('Satır Detayları & Doğrulama Raporu')).toBeVisible();
    await expect(page.getByRole('cell', { name: testMemberNumber })).toBeVisible();
    await expect(page.getByRole('cell', { name: 'VALID' })).toBeVisible();

    // Commit Valid Records
    const commitBtn = page.getByRole('button', { name: 'Geçerli Kayıtları İçe Aktar' });
    await expect(commitBtn).toBeVisible();
    await commitBtn.click();

    // Verify Commit Success
    await expect(page.getByText('Bu grup başarıyla tamamlandı')).toBeVisible();
    await expect(page.getByRole('cell', { name: 'IMPORTED' })).toBeVisible();
    await expect(page.getByRole('button', { name: /COMPLETED/ }).first()).toBeVisible();
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


