# Antrenman, Egzersiz ve PT Programlama Modülü — Gelecek Ajan / Geliştirici Devir Kılavuzu (Handoff Guide)

**Tarih:** 2026-08-20  
**Durum:** 🟢 **PLANLANDI, TÜM STRES TESTLERİNDEN GEÇTİ & MATEMATİK MOTORU HAZIR (%100 TEST EDİLDİ)**  
**Kapsam:** Fitness Network OS / GymClubNex — Çok Kiracılı Antrenman ve PT Sistemi  
**Yetkili Dokümanlar:**
1. [`docs/plans/TRAINING_AND_WORKOUT_SYSTEM_SPEC.md`](./TRAINING_AND_WORKOUT_SYSTEM_SPEC.md) — Master Mimari & Saha Spesifikasyonu
2. [`docs/plans/OPENGYM_ADAPTATION_REFERENCE.md`](./OPENGYM_ADAPTATION_REFERENCE.md) — openGym Güvenlik Analizi & Lisans Koruma Standardı
3. [`docs/plans/WORKOUT_SYSTEM_EXECUTION_AND_SEARCH_SPEC.md`](./WORKOUT_SYSTEM_EXECUTION_AND_SEARCH_SPEC.md) — Akıllı Arama & Eş Anlamlı Normalizasyon Spesifikasyonu

---

## 1. Sistemin Mevcut Durumu (Neler Yapıldı, Neler Hazır?)

Açık kaynak `openGym` ve `exercises-dataset` havuzları derinlemesine incelenmiş; **AGPL telif bulaşmasını önlemek amacıyla tek satır sunucu kodu kopyalanmadan** tüm spor bilimi ve hesaplama mantığı **%100 saf, tip güvenli TypeScript fonksiyonları** olarak yazılmış ve test edilmiştir:

### 📁 Halihazırda Hazır ve Test Edilmiş Hesaplama Motoru (`frontend/shared/workout-engine/`)
Tüm dosyalar `frontend/shared/workout-engine/` altında yaşar ve Karpathy ilkelerine (`Boring > Clever`, sıfır `any`, deterministik matematik) uygundur:
* **`onerm.ts`:** Epley & Brzycki 1RM tahmin formülleri ($\le 12$ tekrar güvenlik kuralı, 1 tekrarda ölçülen değerin dönmesi).
* **`progression.ts`:** Lineer artış, Greyskull LP (AMRAP çift artış), Çift Progresyon, Vücut Ağırlığı 6-set merdiveni ve %10 deload matematiği.
* **`muscles.ts`:** 18 anatomik kas grubu, ana ($1.0$) / ikincil ($0.4$) kas yükü dağılımı ve 0–4 ısı haritası renklendirmesi (Türkçe kas adları dahil).
* **`effort.ts`:** İki yönlü $\text{RPE} \leftrightarrow \text{RIR}$ dönüşümü ve $RIR \le 3$ etkili set filtresi.
* **`wakelock.ts`:** Turnike ve antrenmanda ekranı açık tutan, referans sayaçlı (`lockCount`) ve `visibilitychange` ile otomatik toparlanan React Hook'u (`useScreenWakeLock`).
* **`importers.ts`:** Strong, Hevy ve FitNotes CSV başlıklarını otomatik tanıyan tırnak/virgül dayanıklı parser.
* **`workout-engine.test.ts`:** 14 adet birim test (`npx vitest run frontend/shared/workout-engine/workout-engine.test.ts`) **%100 YEŞİL**.

---

## 2. Sıradaki Ajanın / Geliştiricinin Kesinlikle Uyması Gereken Mimari Kurallar

1. **Kritik Hybrid RLS Kuralı (`exercises` tablosu):**
   - 1.324 global egzersiz `tenant_id IS NULL` olarak durur. Standart RLS'in `NULL` değerleri gizlemesini önlemek için şu RLS politikası uygulanmalıdır:
     ```sql
     CREATE POLICY exercises_tenant_read_policy ON exercises
     FOR SELECT USING (
         tenant_id IS NULL OR tenant_id = nullif(current_setting('app.current_tenant_id', true), '')::uuid
     );
     ```
2. **Çevrimdışı İdempotens Garantisi (Bodrum Katı Çekmeme Durumu):**
   - Üyenin telefonundaki her seans ve set için istemci taraflı UUID (`client_session_id`, `client_set_id`) üretilir.
   - `workout_sessions` tablosunda `UNIQUE (tenant_id, member_id, client_session_id)` kısıtlaması ve aktif seans için `CREATE UNIQUE INDEX idx_workout_sessions_active_unique ON workout_sessions(tenant_id, member_id) WHERE completed_at IS NULL;` kullanılır.
3. **Outbox ile Asenkron Olaylar:**
   - Antrenman tamamlandığında (`POST /api/v1/me/workouts/session`), eğitmen takılma (stall) bildirimleri veya PR tebrikleri istek akışını tıkamamalıdır; `outbox` tablosuna `workout.session_completed` olayı bırakılarak asenkron işlenmelidir.
4. **Saha Ergonomisi:**
   - Mobil ekranda klavye açma zorunluluğunu bitiren `[- 80kg +]`, `+1.25`, `+2.5`, `+5kg` hızlı adım butonları kullanılmalıdır.
   - Alet doluysa tek tıkla aynı kası çalıştıran alternatif hareket çekmecesi (Occupied Machine Alternative Swap) açılmalıdır.

---

## 3. Uygulamaya Başlarken İzlenecek 4 Fazlı Adım Listesi

### 🚀 Faz 1: Veritabanı Modelleri & 1.324 Egzersizin Tohumlanması (Backend)
1. `backend/app/models/training.py` model dosyasını oluştur (`Exercise`, `WorkoutRoutine`, `RoutineExercise`, `WorkoutSession`, `WorkoutSetLog`).
2. `backend/alembic/versions/` altına Hybrid RLS politikaları ve `pg_trgm` arama index'ini içeren migrasyon dosyasını ekle.
3. `backend/scripts/seed_exercises_dataset.py` betiğini yazarak 1.324 Türkçe/İngilizce egzersizi veritabanına aktar.
4. `backend/app/api/v1/endpoints/exercises.py` (`GET /api/v1/exercises`, `GET /api/v1/exercises/summary`) uç noktalarını aç.

### 🚀 Faz 2: Eğitmen Konsolu & Hızlı Programlayıcı (Frontend Admin-Web)
1. `frontend/admin-web/src/pages/TrainerPortal.tsx` içine "Programlar" sekmesi ekle.
2. Eğitmenin üyeyi seçip 2 dakikada PPL / Full Body / Özel rutin atayabileceği arayüzü bağla.
3. Üyenin 1RM artış grafiğini ve takılma alarmlarını eğitmen ekranına yansıt.

### 🚀 Faz 3: Mobil Üye Portalı (`/me/workouts` PWA)
1. `frontend/admin-web/src/pages/MemberPortal.tsx` içine antrenman kartını ve `/portal/workouts` aktif antrenman oynatıcısını bağla.
2. `useScreenWakeLock(true)` kancasını bağla.
3. Web Worker tabanlı titreşimli dinlenme sayacını ve 18 bölgeli SVG kas haritasını ekle.
4. IndexedDB yerel kuyruğunu bağlayarak bodrum katı çevrimdışı çalışma desteğini sağla.

### 🚀 Faz 4: İçe Aktarma & Yönetici Retention Guard
1. Üye portalına Strong / Hevy CSV yükleme modalı ekle (`frontend/shared/workout-engine/importers.ts` parser'ı ile).
2. Salon yöneticisi paneline (`/admin/analytics/training`) 21 gündür gelmeyen üyeleri listeleyen **Retention Guard** panosunu ekle.

---

## 4. Test Komutları

```bash
# Frontend Hesaplama Motoru Testleri (Vitest)
npx vitest run frontend/shared/workout-engine/workout-engine.test.ts

# Backend Tenancy ve API Testleri (İmplementasyon sonrası)
pytest backend/tests/test_training_endpoints.py backend/tests/test_training_tenancy.py -v
```
