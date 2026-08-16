# AGENTS.md - Project Global Engineering Guidelines

Bu iki specification (MASTER_SPEC.md ve PRODUCTION_READINESS.md) proje için source of truth'tur. Bütün geliştirme adımlarında bu belgelere uygunluk esastır.

**Devralıyorsan buradan başla: `docs/HANDOFF.md`** — tek giriş noktası: nerede ne var, ne yapıldı, sırada ne var, hangi tuzaklar seni bekliyor.

**Context map:** `.codesight/wiki/index.md` — AST-derived route/model/file map, ~200 tokens to load. Read it before searching the tree; load the targeted article (e.g. `plans.md`, `devices.md`) instead of scanning the codebase. It says *where* things are, never *how* they work — always read the source before changing it. Regenerated automatically by `.git/hooks/pre-commit`; refresh manually with `npx codesight --wiki`.

**Progress truth (2026-08-16):** Phase **27 / 27.1 / 27.2 / 27.3 / 27.4 + Waves 1–3 + Deep-Dive Hardening + Federation HQ + Milestone B1 + Phase 29 in-repo hardening** is **CODE LANDED** on `feat/public-site-modernization-and-seo`, Alembic head `xd5e6f7a8b9c`. Phase 29 closed same-tenant BOLA, step-up/idle, `fernet:hmac` device secrets, portal-account bind, scanner pairing, SMTP body, compose workers, hashed invites, and onboarding UI. Checklist authority: `docs/PROGRESS_CHECKLIST.md`. Phase **26 CORE MVP EXIT GATE remains NOT PASSED** — real-bucket S3 proof and independent pentest are missing; **not production-ready**.

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
