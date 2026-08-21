# openGym Reference, Security Audit and Fitness Network OS Adaptation Plan

**Status:** Reference / target design; not an implementation claim  
**Reviewed:** 2026-08-20  
**Fitness Network OS baseline:** `main`  
**Upstream repository:** <https://github.com/TechLionDev/openGym> (Public restore mirror of `DuarteSantos8/openGym`)  
**Upstream exercise dataset:** <https://github.com/hasaneyldrm/exercises-dataset>  
**Upstream license:** [AGPL-3.0](https://github.com/TechLionDev/openGym/blob/main/LICENSE) (Code) / [CC / Open](https://github.com/hasaneyldrm/exercises-dataset) (Dataset)

---

## 1. Executive Decision

`openGym` is an excellent product, mathematical, and algorithmic reference for the future **Member Training, PT Programming & Exercise Tracking** bounded context of Fitness Network OS (GymClubNex).

It is **NOT** an architectural reference for authentication, database storage, tenant isolation, or enterprise security:
- `openGym` is designed as a single-tenant, hobbyist, file-based (`./data/*.json`) personal application.
- GymClubNex is an enterprise multi-tenant B2B Gym Operating System governed by PostgreSQL + Row Level Security (RLS), Transactional Outbox, and strict tenant-scoped RBAC (`MASTER_SPEC.md`, `PRODUCTION_READINESS.md`).

**Adoption Strategy:**
1. **Clean-Room Implementation:** Do not copy-paste AGPL-3.0 server code. Re-implement the training algorithms as pure, deterministic TypeScript/Python functions.
2. **Leverage Open Datasets:** Adapt the 1,324-exercise dataset with anatomical muscle mappings and Turkish translations for gym trainer programming and member workout logging.
3. **PWA & Member UX Innovations:** Adopt the Screen WakeLock lifecycle management (`navigator.wakeLock`) and biometric WebAuthn passkey concepts within our multi-tenant auth architecture.
4. **Third-Party Tracker Importers:** Adapt CSV parser schemas for Strong, Hevy, FitNotes, and Apple Health to allow seamless member onboarding.

---

## 2. Comprehensive Security & Code Quality Audit of openGym

A rigorous security review of `TechLionDev/openGym` (`api/server.js`, `frontend/src/lib/*`, and Docker configurations) reveals several strengths alongside critical vulnerabilities and architectural limitations:

### 2.1 Security Strengths (What openGym Does Right)
- **Constant-Time Crypto Verification:** HMAC session cookie validation uses `crypto.timingSafeEqual` (`api/server.js:158`) to prevent timing side-channel attacks.
- **WebAuthn Verification:** Proper origin and RP ID validation with signature counter tracking via `@simplewebauthn/server` to prevent credential replay.
- **Atomic File Writes:** Writes use temporary files and atomic renames (`fs.renameSync`) to prevent corrupt JSON reads during crashes.
- **Global Session Revocation:** Bumping the user's `sv` counter invalidates all issued HMAC tokens globally (`POST /api/logout/all`).

### 2.2 Critical Security Deficiencies & Vulnerabilities (Why openGym Cannot Be Used As-Is)

| # | Vulnerability / Deficiency | openGym Implementation | GymClubNex Enterprise Standard | Risk Level |
|---|---|---|---|---|
| **SEC-1** | **Zero Rate Limiting** | No throttling on `/api/register/options`, `/api/login/options`, `/api/data`, or invite validation. | Redis token-bucket rate limiter keyed by `user_id` / `tenant_id` on all public endpoints. | **HIGH** (DoS & brute-force) |
| **SEC-2** | **Unencrypted Plaintext JSON Storage** | All users, passkey public keys, push tokens, and full workout histories are stored in plain `.json` files in `./data`. | PostgreSQL with disk encryption, connection pooling, column-level protection, and strict RLS. | **HIGH** (Data breach if disk exposed) |
| **SEC-3** | **Single Master Secret Point of Failure** | `./data/secret` contains a single raw HMAC key. Compromise of this one file allows arbitrary cookie forgery for any user. | KMS-backed key rotation, JWT/session store with distinct tenant secrets, and isolated user credentials. | **HIGH** (Full instance takeover) |
| **SEC-4** | **Unbounded In-Memory State (Memory Exhaustion)** | `presence` Map and `restTimers` Map grow in memory with no cap on total entries. | Redis-backed TTL caches and asynchronous workers with strict quotas. | **MEDIUM** (OOM Crash under load) |
| **SEC-5** | **Weak Input Validation** | Only checks `typeof body.state === 'object'` without schema validation; accepts up to 5MB arbitrary JSON trees. | Strict Pydantic / Zod schema validation at the API boundary before business logic runs. | **MEDIUM** (Payload injection & corruption) |
| **SEC-6** | **Lack of Multi-Tenant Isolation** | No `tenant_id` concept; all users share a global `db.json` and file directory. | Mandatory `tenant_id` on all tables, indexes, and queries with transaction-scoped RLS policies. | **CRITICAL** (Multi-tenant data leak) |
| **SEC-7** | **Admin Overexposure** | Admins (`ADMIN_UIDS`) have unrestricted access to all user profiles, workout logs, and weights across the system. | Scoped RBAC, audit logging, purpose-bound support sessions, and member privacy controls. | **HIGH** (GDPR/KVKK violation) |

---

## 3. Algorithmic Domain Breakdown (Archived Logic)

The core mathematical training logic in openGym's `frontend/src/lib/` is purely functional and provides high business value for GymClubNex's member and trainer features.

### 3.1 Estimated One-Rep Max (1RM) Engine
Standardized submaximal load formulas with safety thresholds:
- **Safety Cap:** Estimates are restricted to $\le 12$ reps (`REP_CAP = 12`). Above 12 reps, formulas test endurance/work capacity rather than strength.
- **Epley Formula (Default):**
  $$1\text{RM}_{\text{Epley}} = w \cdot \left(1 + \frac{r}{30}\right)$$
- **Brzycki Formula:**
  $$1\text{RM}_{\text{Brzycki}} = w \cdot \frac{36}{37 - r}$$
- **Lombardi Formula:**
  $$1\text{RM}_{\text{Lombardi}} = w \cdot r^{0.10}$$
- **Measurement Invariant:** If $r = 1$, the estimate is the measured weight ($1\text{RM} = w$). Non-positive weights or reps $> 12$ return `null`.

### 3.2 Progressive Overload & Prescription Engine
Derived prescriptions based on historical session evaluation without mutating previous workout records:

1. **Session Outcome Evaluation (`readSession`):**
   - **Hit (`ok: true`):** All prescribed sets performed and completed with reps/time $\ge$ target.
   - **Miss (`ok: false`):** Any prescribed set uncompleted, skipped, or logged with fewer reps than the target.
   - **Stall Count (`stallCount`):** Number of consecutive missed sessions counting back from the latest session.

2. **Progression Policies:**
   - **Linear Progression:**
     - Success $\rightarrow$ Add load increment ($\Delta w = 2.5\text{ kg}$ upper body, $5.0\text{ kg}$ lower body).
     - 3 consecutive misses $\rightarrow$ Deload by $10\%$ ($\text{Deload} = \max(\text{step}, \text{snap}(w \times 0.9, \text{step}))$).
   - **Greyskull LP:**
     - 2 standard sets + 1 AMRAP (As Many Reps As Possible) final set.
     - Final set $\ge 2\times \text{target}$ $\rightarrow$ Double increment jump ($2 \times \Delta w$).
     - Single failure $\rightarrow$ Immediate $10\%$ deload.
   - **Double Progression (Rep Range):**
     - Work within range $[r_{\min}, r_{\max}]$ (e.g., $8\text{--}12$ reps).
     - Reach $r_{\max}$ on all sets $\rightarrow$ Add weight ($\Delta w$), reset reps to $r_{\min}$.
     - Miss $\rightarrow$ Hold weight, attempt $r_{\text{low}} + 1$ reps.
   - **Bodyweight Progression:**
     - Load $= 0\text{ kg}$. Progress by increasing reps up to ceiling $r_{\text{top}}$ (e.g., $20\text{--}30$ reps).
     - Upon reaching ceiling $\rightarrow$ Add an extra set (up to $\max = 6$ sets) and reset reps to baseline.
     - Beyond 6 sets $\rightarrow$ Prompt trainer/member to add external load (dip belt) or switch to a harder variation.
   - **Timed Exercise Progression:**
     - Increment duration by $5\text{ s}$ on full hold; deload after 3 consecutive failures.

### 3.3 Muscle Group Volume & Heatmap Aggregation
- **18 Anatomical Muscle Regions:** `trapezius`, `deltoids`, `chest`, `upper-back`, `serratus`, `biceps`, `triceps`, `forearm`, `abs`, `obliques`, `lower-back`, `gluteal`, `quadriceps`, `hamstring`, `adductors`, `hip-flexors`, `calves`, `tibialis`.
- **Effective Load Calculation:**
  $$\text{Load}(m) = \sum_{e \in \text{exercises}} \text{Sets}(e) \times \text{Multiplier}(e, m)$$
  - Primary muscle target: Multiplier $= 1.0$
  - Secondary supporting muscles: Multiplier $= 0.4$
- **Relative Intensity Shading:** Normalized buckets $(0\text{--}4)$ relative to the most trained muscle in the selected timeframe ($7\text{ days}$, $30\text{ days}$, or all-time). Identifies neglected/untrained muscle groups.

### 3.4 Effort Scales (RPE vs RIR)
- **Bidirectional Mapping:** $\text{RPE} = 10 - \text{RIR}$ (e.g., RPE 8.0 = 2 Reps in Reserve).
- **Hard Set Filter:** Sets with $\text{RIR} \le 3$ (or $\text{RPE} \ge 7$) are categorized as adaptive working sets; warm-up sets ($\text{RIR} > 3$) are excluded from fatigue metrics.

---

## 4. Exercise Dataset & Turkish Localization Asset

The upstream repository incorporates a structured dataset of 1,324 exercises with:
- Target muscles, secondary muscles, and body part categories.
- Equipment requirements (`body weight`, `barbell`, `dumbbell`, `cable`, `leverage machine`, `band`, `kettlebell`, etc.).
- Animated demonstration GIF/JPG media mappings.
- **Turkish (`tr.js`) full UI and instruction translations** for exercise execution.

### Schema Mapping to GymClubNex

```sql
-- Target relational schema for GymClubNex (PostgreSQL + RLS)
CREATE TABLE exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE, -- NULL for global system exercises
    code VARCHAR(32) NOT NULL,
    name_en VARCHAR(255) NOT NULL,
    name_tr VARCHAR(255) NOT NULL,
    body_part VARCHAR(64) NOT NULL,
    equipment VARCHAR(64) NOT NULL,
    target_muscle VARCHAR(64) NOT NULL,
    secondary_muscles VARCHAR(64)[] DEFAULT '{}',
    instructions_en TEXT[] DEFAULT '{}',
    instructions_tr TEXT[] DEFAULT '{}',
    media_image_url VARCHAR(512),
    media_gif_url VARCHAR(512),
    is_custom BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_exercises_tenant ON exercises(tenant_id);
CREATE INDEX idx_exercises_target_muscle ON exercises(target_muscle);
CREATE INDEX idx_exercises_body_part ON exercises(body_part);
```

---

## 5. PWA & Mobile UX Innovations

### 5.1 Screen WakeLock Integration (`navigator.wakeLock`)
- **Use Case:** Keeps the mobile device screen active during workouts, rest timers, and turnstile QR validation, preventing frustrating device lockouts.
- **Re-acquisition Lifecycle:** Automatically listens to `visibilitychange` events to re-acquire the lock when the user switches back from background apps or notifications.

---

## 6. Tracker Importers (FitNotes, Strong, Hevy, Apple Health)

Robust CSV parsing engine handling quotes, commas, BOM, and distinct column headers:
- **Hevy:** `exercise_title`, `weight_kg`, `reps`, `rpe`, `set_index`
- **Strong:** `Exercise Name`, `Weight`, `Reps`, `RPE`, `Set Order`
- **FitNotes:** `Exercise`, `Weight`, `Weight Unit`, `Reps`, `Category`
- **Apple Health:** XML stream parser extracting `HKQuantityTypeIdentifierBodyMass` without building memory-heavy DOM trees.

---

## 7. Adopt, Adapt, or Reject Matrix

| Capability / Component | Decision | Fitness Network OS Architecture Plan |
|---|---|---|
| **1RM & Progression Math** | **ADOPT** | Implement as pure TypeScript functions in `frontend/shared/workout-engine/` and Python backend service. |
| **Muscle Map & Load Formulas** | **ADOPT** | Implement front/back anatomical SVG heatmaps in Member Portal (`/me/workouts`). |
| **Exercise Dataset (1,324 items)** | **ADAPT** | Seed into global multi-tenant catalog with Turkish translations and equipment filters. |
| **Screen WakeLock Utility** | **ADOPT** | Add `useWakeLock` hook to Member Portal and Scanner Turnstile apps. |
| **CSV Importers (Strong/Hevy)** | **ADAPT** | Build secure `/api/v1/members/me/import-workouts` endpoint with strict Zod validation. |
| **File-based JSON Database** | **REJECT** | Incompatible with multi-tenancy. Retain PostgreSQL + RLS + Transactional Outbox. |
| **Single HMAC Secret File** | **REJECT** | Retain multi-tenant token isolation, KMS rotation, and role-scoped session cookies. |
| **Hobbyist Server (`api/server.js`)** | **REJECT** | Discard single-file Node server; build enterprise FastAPI/Next.js services. |
