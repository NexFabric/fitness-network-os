# AGENTS.md - Project Global Engineering Guidelines

Bu iki specification (MASTER_SPEC.md ve PRODUCTION_READINESS.md) proje için source of truth'tur. Bütün geliştirme adımlarında bu belgelere uygunluk esastır.

**Progress truth (2026-08-09):** Phase **0–15** domain track on `main` is CI VERIFIED / LOCKED. **Active = Phase 15.5 Integrity Closure** before Phase 16 Notifications/Reports (see `docs/PROGRESS_CHECKLIST.md`). Do **not** claim production-ready.

## Temel Kurallar ve Mimari Kararlar

- Federation != Tenant.
- Gym = Tenant.
- Branch = Location.
- User != Member.
- Membership != Payment.
- PostgreSQL + shared DB + tenant_id + RLS varsayılan tenancy modelidir.
- IsolationProvider abstraction korunacaktır.
- Tenant-owned hiçbir tablo tenant_id, index, RLS policy ve tenancy testleri olmadan oluşturulamaz.
- RBAC + Scope + RLS birlikte uygulanacaktır.
- Raw PAN/CVV/card data saklanmayacak veya loglanmayacaktır.
- Payment işlemlerinde float kullanılmayacaktır (amount_minor kullanılacaktır).
- Dynamic signed short-lived QR + replay protection + key rotation kullanılacaktır.
- Transactional Outbox, webhook Inbox/Outbox ve idempotency kuralları korunacaktır.
- Domain sınırları ihlal edilmeyecektir (örn. Membership -> WhatsApp yasak; Membership -> Event -> Notification -> WhatsApp doğru).
- Gereksiz microservice, Kafka, Kubernetes veya premature infrastructure eklenmeyecektir.
- Mimari değişiklikler yalnız ADR (Architecture Decision Record) ile yapılacaktır.
- Her Wave tamamlandıktan sonra test, security ve tenancy gate'leri geçirilmeden sonraki Wave'e geçilmeyecektir.

## Çalışma Akışı
- Geliştirmeye Milestone FOUNDATION ile başlanacak ve dependencies'e uygun gidilecektir.
- Her aşamada testler çalıştırılacak ve hatalar temizlenmeden ilerlenmeyecektir.
- Her büyük iş mantıklı commitlere bölünecektir.
- Çalışma ağacı temiz bırakılacak ve yapılan işler açıklayıcı mesajlarla commit edilecektir.
