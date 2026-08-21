# GymClubNex Antrenman ve Akıllı Arama (Search & Discovery) Sistemi Spesifikasyonu

**Durum:** Hedef Mimari ve İcra Spesifikasyonu  
**Tarih:** 2026-08-20  
**Kapsam:** Çok Kiracılı Spor Salonu İşletim Sistemi (GymClubNex)  
**Referans Dokümanlar:** [`docs/plans/OPENGYM_ADAPTATION_REFERENCE.md`](./OPENGYM_ADAPTATION_REFERENCE.md), [`docs/plans/TRAINING_AND_WORKOUT_SYSTEM_SPEC.md`](./TRAINING_AND_WORKOUT_SYSTEM_SPEC.md)

---

## 1. Akıllı Arama & Keşif (Search & Discovery) Mimarisi

1.324 egzersiz arasından antrenörün veya üyenin aradığı hareketi milisaniyeler içinde bulabilmesi için çok katmanlı bir arama mekanizması kurulmuştur:

### 1.1 Türkçe / İngilizce Eş Anlamlı ve Argo Eşleme Motoru (Synonym Normalization)
Kullanıcıların kullandığı yaygın salon dili otomatik olarak standart egzersiz kodlarına dönüştürülür:

- `"bench"` / `"göğüs pres"` $\rightarrow$ `barbell bench press`, `dumbbell bench press`, `incline bench press`, `smith machine bench press`
- `"omuz pres"` / `"ohp"` $\rightarrow$ `overhead press`, `military press`, `dumbbell shoulder press`, `arnold press`
- `"barfiks"` / `"barfiks çekme"` $\rightarrow$ `pull up`, `chin up`, `assisted pull up`
- `"şınav"` $\rightarrow$ `push up`, `diamond push up`, `decline push up`
- `"arka kol"` / `"triceps"` $\rightarrow$ `cable triceps pushdown`, `skull crusher`, `overhead extension`, `dips`
- `"ön kol"` / `"pazu"` / `"biceps"` $\rightarrow$ `barbell curl`, `dumbbell hammer curl`, `preacher curl`
- `"squat"` / `"çökme"` $\rightarrow$ `barbell back squat`, `front squat`, `goblet squat`, `leg press`

### 1.2 Çok Boyutlu Filtreleme (Faceted Search)
1. **Şube Ekipmanı Filtresi:** Salonda olan ekipmanlara göre filtreleme (Dambıl, Halter, Kablo, Makine, Vücut Ağırlığı, Direnç Bandı).
2. **Hedef Kas Grubu:** Göğüs, Sırt, Omuz, Kol, Karın/Bel, Bacak, Kalça.
3. **Zorluk / Deneyim Düzeyi:** Başlangıç, Orta, İleri seviye.

---

## 2. Çoklu Ajan Görev Dağılımı (Multi-Agent Workflows)

1. **`cs-product-manager`:** Kullanıcı hikayeleri, kabul kriterleri ve RICE skorlaması ile kapsam disiplini.
2. **`challenge` (`/challenge`):** Pre-mortem arıza modu analizi (offline bodrum katı, makine dara farkları, unutulan antrenmanlar).
3. **`cs-senior-engineer`:** PostgreSQL RLS uyumlu veritabanı şeması, FastAPI endpoint'leri ve Transactional Outbox olayları.
4. **`cs-ux-researcher` & `a11y`:** Mobil PWA antrenman ergonomisi (tek elle giriş, geniş dokunma alanları, WakeLock ve titreşimli dinlenme sayacı).
5. **`web-performance-optimization`:** 1.324 egzersiz görselinin CDN lazy-load yapılandırması ve <50ms arama performansı.
6. **`generate` / `coverage`:** Vitest ve Playwright ile %100 otomatik test kapsamı.

---

## 3. Uygulama Fazları

1. **Faz 1: Veritabanı, RLS ve Arama Motoru:** 1.324 egzersiz tohumlaması ve arama API'si.
2. **Faz 2: Eğitmen Program Oluşturucu:** Trainer Workspace arayüzü ve hazır şablonlar.
3. **Faz 3: Mobil Üye Portalı (`/me/workouts`):** Salonda kesintisiz set kaydı, WakeLock ve IndexedDB offline kuyruğu.
4. **Faz 4: İçe Aktarım & Retention Guard:** Strong/Hevy CSV aktarımı ve riskli üye uyarı panosu.
