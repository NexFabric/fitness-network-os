## Ne değişti

<!-- Bir paragraf. Neden, sadece ne değil. -->

## Kanıt

<!-- Sadece "testler geçti" yetmez. Gerçek çalışma zamanında ne denendi? -->

- [ ] Özellik gerçek runtime'da denendi (tarayıcı / gerçek HTTP)
- [ ] Hata yolu denendi (timeout, çift gönderim veya retry)

## Kapılar

- [ ] `ruff check` + `ruff format --check` + `mypy app`
- [ ] `alembic check` yeşil; **tek head**
- [ ] `check_tenancy` / `check_permissions` / `check_no_money_floats` / `check_release_truth`
- [ ] Çok kiracılı sorgular `tenant_id` ile filtreliyor
- [ ] `console.log` yok, gömülü secret yok, üretim yolunda sentetik veri yok
- [ ] Kullanıcıya görünen metinler Türkçe, kısa, eyleme dönük

## Doküman doğruluğu

- [ ] `docs/PROGRESS_CHECKLIST.md` gerçeği yansıtıyor
- [ ] Production-ready / Phase 26 PASS **iddia edilmedi** (dış kanıt olmadan)

## Riskli mi

<!-- Geri alma planı, veri migrasyonu, geriye dönük uyumluluk. Yoksa "yok" yaz. -->
