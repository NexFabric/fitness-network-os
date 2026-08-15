import { test, expect, type Page } from '@playwright/test'

const PASSWORD = 'E2ePortal123!'
const ANALYST_EMAIL = 'e2e.analyst@e2e.local'

async function loginFederationAdmin(page: Page) {
  await page.goto('/login')
  await page.fill('input[type="email"]', ANALYST_EMAIL)
  await page.fill('input[type="password"]', PASSWORD)
  await page.click('button[type="submit"]')
  await page.waitForURL((u) => !u.pathname.startsWith('/login'), { timeout: 15_000 })
}

test.describe('Federation HQ Console & 6-Tab Workflows', () => {
  test('renders 6 tabs, switches views, and displays network KPIs', async ({ page }) => {
    await loginFederationAdmin(page)
    await page.goto('/superadmin')
    await page.waitForLoadState('networkidle')

    // Verify Header & Overview
    await expect(page.getByRole('heading', { name: 'Federasyon Konsolu' })).toBeVisible()
    await expect(page.getByText('Toplam Kulüp (Tenant)')).toBeVisible()
    await expect(page.getByText('Ağ Geneli Toplam Üye')).toBeVisible()
    await expect(page.getByText('Aktif Turnike Aboneliği')).toBeVisible()
    await expect(page.getByText('Tahsil Edilen Ağ Cirosu')).toBeVisible()

    // 1. Switch to Kulüpler & Salonlar Tab
    await page.getByRole('button', { name: /Kulüpler & Salonlar/i }).click()
    await expect(page.getByPlaceholder('Kulüp adı veya kod ile ara…')).toBeVisible()
    await expect(page.getByRole('button', { name: '+ Yeni Kulüp Aç' })).toBeVisible()

    // 2. Switch to Federasyon Pasaportu Tab
    await page.getByRole('button', { name: /Federasyon Pasaportu/i }).click()
    await expect(page.getByText('Federasyon Pasaportu ve Dolaşım Matrisi')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Kuralları Düzenle' }).first()).toBeVisible()

    // 3. Switch to Uyumluluk & Denetim Tab
    await page.getByRole('button', { name: /Uyumluluk & Denetim/i }).click()
    await expect(page.getByText('Federasyon Muayene, Kalite ve Sertifikasyon Kayıtları')).toBeVisible()
    await expect(page.getByRole('button', { name: '+ Yeni Denetim Kaydı Ekle' })).toBeVisible()

    // 4. Switch to Ağ Duyuruları Tab
    await page.getByRole('button', { name: /Ağ Duyuruları/i }).click()
    await expect(page.getByText('Federasyon ve Ağ Düzeyinde Duyuru Yayını')).toBeVisible()
    await expect(page.getByRole('button', { name: '+ Yeni Duyuru Yayınla' })).toBeVisible()

    // 5. Switch to Raporlar & Analitik Tab
    await page.getByRole('button', { name: /Raporlar & Analitik/i }).click()
    await expect(page.getByText('Konsolide Ağ Analitiği & Finansal Raporlar')).toBeVisible()
    await expect(page.getByRole('button', { name: '📥 Konsolide Ağ Verisini İndir (.csv)' })).toBeVisible()
  })

  test('interactive lifecycle: creates gym, updates passport, adds compliance, and broadcasts alert', async ({
    page,
  }) => {
    const stamp = Date.now().toString().slice(-4)
    const newClubName = `E2E Test Kulübü ${stamp}`
    const newClubCode = `E2E-K${stamp}`

    await loginFederationAdmin(page)
    await page.goto('/superadmin')
    await page.waitForLoadState('networkidle')

    // --- Action A: Create Gym ---
    await page.getByRole('button', { name: /Kulüpler & Salonlar/i }).click()
    await page.getByRole('button', { name: '+ Yeni Kulüp Aç' }).click()
    await page.fill('input[placeholder="Örn: FitClub Beşiktaş"]', newClubName)
    await page.fill('input[placeholder="Örn: FIT-BESIKTAS"]', newClubCode)
    await page.fill('input[placeholder="Örn: Çarşı Şubesi"]', 'Merkez Şube')
    await page.getByRole('button', { name: 'Kulübü Oluştur' }).click()

    // Verify creation success
    await expect(page.getByText('Yeni kulüp ve ana şubesi başarıyla oluşturuldu.')).toBeVisible()
    await expect(page.getByText(newClubName)).toBeVisible()

    // --- Action B: Update Passport Config ---
    await page.getByRole('button', { name: /Federasyon Pasaportu/i }).click()
    await page.getByRole('button', { name: 'Kuralları Düzenle' }).first().click()
    await page.fill('input[placeholder="Örn: VIP,GOLD,PLATINUM"]', 'VIP,PLATINUM,DIAMOND')
    await page.getByRole('button', { name: 'Ayarları Kaydet' }).click()
    await expect(page.getByText('federasyon pasaport ayarları güncellendi.')).toBeVisible()

    // --- Action C: Add Compliance Record ---
    await page.getByRole('button', { name: /Uyumluluk & Denetim/i }).click()
    await page.getByRole('button', { name: '+ Yeni Denetim Kaydı Ekle' }).click()
    await page.fill('input[placeholder="Örn: TSE-ISO 9001 Hijyen & Güvenlik Standardı"]', `TSE-ISO-${stamp}`)
    await page.fill('textarea[placeholder="Örn: İlkyardım ekipmanı ve yangın tüpü kontrolleri yapıldı."]', 'Tam denetim onayı verildi.')
    await page.getByRole('button', { name: 'Denetimi Kaydet' }).click()
    await expect(page.getByText('Denetim muayene kaydı başarıyla eklendi.')).toBeVisible()
    await expect(page.getByText(`TSE-ISO-${stamp}`)).toBeVisible()

    // --- Action D: Broadcast Network Alert & Delete ---
    await page.getByRole('button', { name: /Ağ Duyuruları/i }).click()
    await page.getByRole('button', { name: '+ Yeni Duyuru Yayınla' }).click()
    const alertTitle = `Acil Sistem Uyarısı ${stamp}`
    await page.fill('input[placeholder="Örn: Planlı Turnike Bakım Çalışması"]', alertTitle)
    await page.fill('textarea[placeholder="Örn: Saat 02:00 ile 04:00 arasında turnike okuyucularda yazılım güncellemesi yapılacaktır."]', 'Turnike geçiş testleri yapılacaktır.')
    await page.getByRole('button', { name: 'Duyuruyu Yayınla' }).click()

    await expect(page.getByText('Ağ duyurusu başarıyla yayınlandı.')).toBeVisible()
    await expect(page.getByRole('heading', { name: alertTitle })).toBeVisible()

    // Delete alert
    await page.getByRole('button', { name: 'Yayından Kaldır' }).first().click()
    await expect(page.getByText('Duyuru yayından kaldırıldı.')).toBeVisible()
  })
})
