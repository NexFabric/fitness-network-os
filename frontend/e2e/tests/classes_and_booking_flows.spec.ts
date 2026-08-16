import { test, expect, type Page } from '@playwright/test';
import { acceptOwnerStepUp, completeOwnerMfaIfNeeded } from './helpers/auth';

const PASSWORD = 'E2ePortal123!';
const OWNER = 'e2e.owner@e2e.local';
const MEMBER = 'e2e.member@e2e.local';
const TRAINER = 'e2e.trainer@e2e.local';

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

async function loginTrainer(page: Page) {
  await page.goto('/login');
  await page.fill('input[type="email"]', TRAINER);
  await page.fill('input[type="password"]', PASSWORD);
  await page.click('button[type="submit"]');
  await completeOwnerMfaIfNeeded(page, TRAINER);
  await page.waitForURL((url) => !url.pathname.startsWith('/login'), { timeout: 15_000 });
}

function toDatetimeLocal(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

test.describe.serial('Group Class & PT Booking Engine E2E Flows', () => {
  const uniqueClassName = `E2E Pilates ${Date.now() % 10000}`;
  const locationName = `E2E Ders Şube ${Date.now() % 10000}`;

  test('1. admin creates class type and session', async ({ page }) => {
    acceptOwnerStepUp(page);
    await loginOwner(page);

    // Role-matrix seed creates no locations; session create requires one.
    await page.goto('/locations');
    await page.fill('#location_name', locationName);
    await page.click('form button[type="submit"]');
    await expect(page.getByText('Şube başarıyla oluşturuldu.')).toBeVisible();

    await page.goto('/classes');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { name: 'Grup Dersi & PT Takvimi' })).toBeVisible();

    // Create Class Type
    await page.getByRole('button', { name: '+ Ders Tipi' }).click();
    await expect(page.getByText('Yeni Ders Tipi Ekle')).toBeVisible();

    await page.fill('input[placeholder*="Reformer Pilates"]', uniqueClassName);
    await page.getByRole('button', { name: 'Kaydet' }).click();
    await expect(page.getByText('Yeni ders tipi başarıyla oluşturuldu.')).toBeVisible({ timeout: 10_000 });

    // Create Session
    await page.getByRole('button', { name: '+ Yeni Seans Ekle' }).click();
    await expect(page.getByText('Yeni Ders Seansı Planla')).toBeVisible();

    const sessionForm = page.locator('form', { hasText: 'Ders Tipi' });
    await sessionForm.locator('select').nth(0).selectOption({ label: `${uniqueClassName} (45 dk)` });
    await sessionForm.locator('select').nth(1).selectOption({ label: locationName });
    await sessionForm.locator('select').nth(2).selectOption({ label: /e2e\.trainer@e2e\.local/ });

    const start = new Date(Date.now() + 86400000);
    start.setHours(14, 0, 0, 0);
    const end = new Date(start.getTime() + 45 * 60 * 1000);

    await sessionForm.locator('input[type="datetime-local"]').nth(0).fill(toDatetimeLocal(start));
    await sessionForm.locator('input[type="datetime-local"]').nth(1).fill(toDatetimeLocal(end));

    const created = page.waitForResponse(
      (res) => res.url().includes('/classes/sessions') && res.request().method() === 'POST',
    );
    await page.getByRole('button', { name: 'Seansı Ekle', exact: true }).click();
    const createRes = await created;
    expect(createRes.ok(), await createRes.text()).toBeTruthy();

    await expect(page.getByText('Ders seansı başarıyla takvime eklendi.')).toBeVisible({ timeout: 10_000 });
    await expect(page.getByRole('heading', { name: uniqueClassName })).toBeVisible();
  });

  test('2. member views class schedule and books session', async ({ page }) => {
    await loginMember(page);
    await page.goto('/member');
    await page.waitForLoadState('networkidle');

    // Switch to Classes tab
    await page.getByRole('button', { name: /Dersler/i }).click();

    // Locate the specific class session card and click Rezervasyon Yap
    const sessionCard = page.locator('div.p-4.rounded-2xl', { has: page.getByRole('heading', { name: uniqueClassName }) }).first();
    const bookButton = sessionCard.getByRole('button', { name: 'Rezervasyon Yap' });
    await expect(bookButton).toBeVisible({ timeout: 10_000 });
    await bookButton.click();

    // Verify confirmation banner and status
    await expect(page.getByText(/Rezervasyonunuz başarıyla onaylandı/i)).toBeVisible({ timeout: 10_000 });
    await expect(sessionCard.getByText(/Rezervasyonunuz Var/i)).toBeVisible();
  });

  test('3. admin opens attendance roster and marks member attendance', async ({ page }) => {
    await loginOwner(page);
    await page.goto('/classes');
    await page.waitForLoadState('networkidle');

    // Locate specific session card created in test 1
    const sessionCard = page.locator('div.p-5.rounded-xl', { has: page.getByRole('heading', { name: uniqueClassName }) }).first();
    const rosterBtn = sessionCard.getByRole('button', { name: /Katılımcı Listesi & Yoklama/i });
    await rosterBtn.click();

    await expect(page.getByText('YOKLAMA & KATILIMCI LİSTESİ')).toBeVisible();
    await expect(page.getByRole('button', { name: '✓ Geldi' }).first()).toBeVisible();

    // Mark attended
    await page.getByRole('button', { name: '✓ Geldi' }).first().click();
    await expect(page.getByText(/Yoklama kaydedildi: Katıldı/i)).toBeVisible({ timeout: 10_000 });

    // Close drawer
    await page.getByRole('button', { name: 'Kapat' }).click();
  });

  test('4. trainer portal displays assigned sessions and attendance roster', async ({ page }) => {
    await loginTrainer(page);
    await page.goto('/trainer');
    await page.waitForLoadState('networkidle');

    await expect(page.getByRole('heading', { name: 'Antrenör Portalı' })).toBeVisible();

    // Switch to Grup Derslerim tab
    await page.getByRole('button', { name: /Grup Derslerim/i }).click();
    await expect(
      page.getByText(/Planlanmış Grup Dersi/i).or(page.getByRole('button', { name: /Yoklama Listesini Aç/i }).first())
    ).toBeVisible();
  });
});
