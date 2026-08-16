# RBAC — Roller, İzinler ve Kapsamlar

**Son güncelleme:** 2026-08-12

Bu doküman canlı referanstır. Daha önce yalnızca arşiv olarak işaretlenmiş
`docs/CORE_GATE_CLOSURE.md` içinde duruyordu.

**Kaynak-of-truth kod tarafındadır:** `backend/permissions.yml`. Bu dosya CI'da
iki kez doğrulanır — `scripts/check_permissions.py` (YAML iç tutarlılığı) ve
`scripts/check_permissions_db.py` (YAML ↔ PostgreSQL). Doküman ile YAML
ayrışırsa **YAML doğrudur**.

---

## 1. Roller (11)

| Rol | Kapsam düzeyi | Özet |
|---|---|---|
| `PLATFORM_SUPER_ADMIN` | PLATFORM | Tüm platform (`*` izni) |
| `FEDERATION_ADMIN` | FEDERATION | Bir organizasyon ve altındaki kulüpler |
| `FEDERATION_ANALYST` | FEDERATION | Organizasyon analitiği, salt okunur |
| `FEDERATION_SUPPORT` | FEDERATION | Destek erişimi, salt okunur |
| `GYM_OWNER` | TENANT | Kulüp sahibi — finans + cihaz dahil tam yetki |
| `GYM_ADMIN` | TENANT | Kulüp yöneticisi (+ kullanıcı yönetimi) |
| `GYM_MANAGER` | TENANT | Operasyon yöneticisi (finans kısıtlı) |
| `ACCOUNTANT` | TENANT | Yalnız finans + rapor |
| `FRONT_DESK` | TENANT | Resepsiyon: üye, check-in, QR verme |
| `TRAINER` | ASSIGNED | Yalnızca **kendisine atanmış** üyeler |
| `MEMBER` | SELF | Yalnızca kendi kayıtları (`*:self`) |

---

## 2. Kapsamlar

| Kapsam | Uygulanma şekli |
|---|---|
| `SELF` | `require_self` — izin adı `:self` ile bitmeli **ve** `resource_owner_id == user.id`. Tenant eşleşmesi tek başına asla yeterli değildir (BOLA önlemi). |
| `ASSIGNED` | `trainer_assignments` tablosu. `members:read` çağrıyı, `members:read:all` tüm tenant'ı açar. İkincisi yoksa satırlar atamalarla sınırlanır (`app/services/member_visibility.py`). |
| `LOCATION` | Bugün TENANT ile aynı şekilde davranır; ayrı şube kısıtı henüz uygulanmıyor. |
| `TENANT` | `require_tenant` + `UserRole.tenant_id` eşleşmesi + RLS. |
| `FEDERATION_AGGREGATE` | `get_federation_scope` — kapsam kullanıcının kendi `UserRole.organization_id` kayıtlarından türetilir, istemciden gelmez. Bkz. ADR-043. |
| `PLATFORM` | `is_superuser` veya platform düzeyinde `PLATFORM_SUPER_ADMIN` ataması. |

---

## 3. Önemli izin ayrımları

| İzin çifti | Fark |
|---|---|
| `access:issue` / `access:issue:self` | İlki personelin herhangi bir üye için QR üretmesi; ikincisi üyenin yalnızca kendisi için. Self uç `member_id` alanını hiç kabul etmez. |
| `access:override` | Turnike arızası, unutan üye veya acil durumlarda resepsiyonun zorunlu gerekçeli manuel giriş izni (`FRONT_DESK`, `GYM_ADMIN`, `GYM_OWNER`). |
| `members:read` / `members:read:all` | İlki uca erişimi, ikincisi **satır kapsamını** verir. TRAINER ikincisini almaz. |
| `reception:read` | Resepsiyon arama ve üye kartı. `GYM_OWNER` / `GYM_ADMIN` / `GYM_MANAGER` / `FRONT_DESK`. TRAINER almaz — `members:read` resepsiyonu açmaz. |
| `memberships:read` / `memberships:read:self` | Personel geneli vs. bağlı üyenin kendi kayıtları. |
| `finance:read:self` | Üyenin kendi fatura ve ödeme geçmişini görmesi (`MEMBER` rolü). |
| `devices:manage` | Cihaz sağlama/iptal. `GYM_OWNER` + `GYM_ADMIN`. |
| `staff:write` | Antrenör↔üye ataması bunun arkasındadır — TRAINER bu izne sahip değildir, yani kendi görünürlüğünü genişletemez. |
| `passport:manage` | Federasyon çapraz salon dolaşım (pasaport) kuralları ve mahsuplaşma ayarlarını yönetme (`FEDERATION_ADMIN`). |
| `compliance:read` / `compliance:write` | Kulüplerin TSE, ISO ve hijyen denetim sicilini görüntüleme ve yeni muayene kaydı ekleme (`FEDERATION_ADMIN`). |
| `alerts:broadcast` | Federasyon ağı genelinde veya belirli kulübe anlık uyarı/duyuru yayınlama (`FEDERATION_ADMIN`). |

---

## 4. Yeni izin eklerken

1. `backend/permissions.yml` içine izni ve rol grant'larını ekle.
2. Alembic migration ile `permissions` + `role_permissions` satırlarını seed'le
   (mevcut örnek: `r1e2f3a4b5c6`, `s2f3a4b5c6d7`).
3. `scripts/check_permissions.py` ve `check_permissions_db.py` yeşil olmalı.
4. ALLOW **ve** DENY testi yaz — pozitif test tek başına yeterli değildir.
