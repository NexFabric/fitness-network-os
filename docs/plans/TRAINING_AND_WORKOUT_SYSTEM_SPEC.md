# GymClubNex Training, Workout & PT Programming System — Master Hardened Specification

**Status:** Target Architectural, Sports Science & Product Specification  
**Reviewed & Hardened:** 2026-08-20 (Post Multi-Agent Pre-Mortem & Architecture Review)  
**Context:** Multi-tenant Gym Operating System (Fitness Network OS)  
**Reference Document:** [`docs/plans/OPENGYM_ADAPTATION_REFERENCE.md`](./OPENGYM_ADAPTATION_REFERENCE.md)  
**Evaluation Reviewers:** Pre-Mortem Risk Auditor (`/challenge`), Senior Architecture Reviewer (`cs-senior-engineer`, `karpathy-check`), Product & Floor UX Reviewer (`product-manager`, `cs-ux-researcher`).

---

## 1. Executive Summary & North Star Metric

### 1.1 The Business Problem
In commercial fitness networks, **80% of member churn occurs within the first 90 days**. The root cause is **lack of structured progression and feeling lost on the gym floor**.
- Members without a plan do random exercises, plateau quickly, lose motivation, and cancel.
- Trainers are bogged down writing unstandardized programs in WhatsApp, with zero visibility into client execution.
- Gym owners have no operational data connecting facility equipment usage to member retention and Personal Training (PT) revenue.

### 1.2 The North Star Metric
$$\text{North Star Metric} = \text{D90 Retention Rate of Workout-Logging Members vs Non-Logging Members}$$
*Target Benchmark:* Increase 90-day member retention by $+25\%$ through frictionless mobile workout execution and automated trainer accountability.

---

## 2. Hardened Architecture & Schema (PostgreSQL + Hybrid RLS)

### 2.1 Critical Hybrid RLS Policy (Global Catalog + Custom Club Exercises)
To ensure the 1,324 global exercises are visible across all tenants without leaking custom club exercises between competing gyms, the following **Hybrid RLS Policy** is enforced:

```sql
ALTER TABLE exercises ENABLE ROW LEVEL SECURITY;
ALTER TABLE exercises FORCE ROW LEVEL SECURITY;

-- Read policy: Global catalog (tenant_id IS NULL) OR current tenant's custom exercises
CREATE POLICY exercises_tenant_read_policy ON exercises
FOR SELECT
USING (
    tenant_id IS NULL 
    OR tenant_id = nullif(current_setting('app.current_tenant_id', true), '')::uuid
);

-- Write policy: Strictly restricted to the current tenant (cannot modify global catalog)
CREATE POLICY exercises_tenant_write_policy ON exercises
FOR ALL
USING (
    tenant_id = nullif(current_setting('app.current_tenant_id', true), '')::uuid
)
WITH CHECK (
    tenant_id = nullif(current_setting('app.current_tenant_id', true), '')::uuid
);
```

### 2.2 Complete Relational Schema & Indexes

```sql
-- ============================================================================
-- 1. Master Egzersiz Kataloğu
-- ============================================================================
CREATE TABLE exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE, -- NULL: Global Shared Catalog
    code VARCHAR(64) NOT NULL,
    name_en VARCHAR(255) NOT NULL,
    name_tr VARCHAR(255) NOT NULL,
    body_part VARCHAR(64) NOT NULL,
    equipment VARCHAR(64) NOT NULL,
    target_muscle VARCHAR(64) NOT NULL,
    secondary_muscles VARCHAR(64)[] DEFAULT '{}',
    instructions_tr TEXT[] DEFAULT '{}',
    instructions_en TEXT[] DEFAULT '{}',
    media_image_url VARCHAR(512),
    media_gif_url VARCHAR(512),
    is_custom BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_exercises_tenant ON exercises(tenant_id);
CREATE INDEX idx_exercises_target_muscle ON exercises(target_muscle);
CREATE INDEX idx_exercises_body_part ON exercises(body_part);
CREATE INDEX idx_exercises_equipment ON exercises(equipment);

-- Trigram index for fuzzy <50ms exercise search in Turkish & English
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_exercises_search_trgm ON exercises USING gin ((name_tr || ' ' || name_en) gin_trgm_ops);

-- ============================================================================
-- 2. Antrenman Programları & Şablonları (Routines)
-- ============================================================================
CREATE TABLE workout_routines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    created_by_staff_id UUID REFERENCES staff(id) ON DELETE SET NULL,
    member_id UUID REFERENCES members(id) ON DELETE CASCADE, -- NULL: Club-wide template
    name VARCHAR(255) NOT NULL,
    description TEXT,
    emoji VARCHAR(16) DEFAULT '🏋️',
    progression_policy VARCHAR(32) DEFAULT 'linear', -- linear, greyskull, double, time, off
    is_template BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_routines_tenant_member ON workout_routines(tenant_id, member_id);

-- ============================================================================
-- 3. Program Egzersiz Detayları (Routine Exercises)
-- ============================================================================
CREATE TABLE routine_exercises (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    routine_id UUID NOT NULL REFERENCES workout_routines(id) ON DELETE CASCADE,
    exercise_id UUID NOT NULL REFERENCES exercises(id) ON DELETE RESTRICT,
    order_index INT NOT NULL DEFAULT 0,
    target_sets INT NOT NULL DEFAULT 3,
    target_reps INT,
    target_reps_min INT,
    target_reps_max INT,
    target_sec INT,
    rest_seconds INT DEFAULT 90,
    superset_group INT,
    notes TEXT
);

CREATE INDEX idx_routine_exercises_lookup ON routine_exercises(routine_id, order_index);

-- ============================================================================
-- 4. Gerçekleşen Antrenman Seansları (Workout Sessions)
-- ============================================================================
CREATE TABLE workout_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    client_session_id UUID NOT NULL, -- Client-generated UUID for offline idempotency
    routine_id UUID REFERENCES workout_routines(id) ON DELETE SET NULL,
    location_id UUID REFERENCES locations(id) ON DELETE SET NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    body_weight_kg NUMERIC(5,2),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_workout_sessions_client UNIQUE (tenant_id, member_id, client_session_id)
);

-- Partial index preventing multiple concurrent dangling active workouts per member
CREATE UNIQUE INDEX idx_workout_sessions_active_unique 
ON workout_sessions(tenant_id, member_id) 
WHERE completed_at IS NULL;

CREATE INDEX idx_workout_sessions_tenant_member ON workout_sessions(tenant_id, member_id, started_at DESC);

-- ============================================================================
-- 5. Set Düzeyinde Detaylı Kayıtlar (Set Logs)
-- ============================================================================
CREATE TABLE workout_set_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    session_id UUID NOT NULL REFERENCES workout_sessions(id) ON DELETE CASCADE,
    client_set_id UUID NOT NULL, -- Client-generated UUID for offline idempotency
    exercise_id UUID NOT NULL REFERENCES exercises(id) ON DELETE RESTRICT,
    set_index INT NOT NULL,
    set_type VARCHAR(16) DEFAULT 'normal', -- normal, warmup, failure, drop
    weight_kg NUMERIC(6,2),
    reps INT,
    duration_sec INT,
    rpe NUMERIC(3,1),
    rir INT,
    is_pr BOOLEAN DEFAULT FALSE,
    completed BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_workout_set_logs_client UNIQUE (session_id, client_set_id)
);

CREATE INDEX idx_workout_set_logs_tenant_session 
ON workout_set_logs(tenant_id, session_id, exercise_id, set_index);
```

---

## 3. Gym Floor Ergonomics & Mobile PWA Innovations

### 3.1 Zero-Keyboard Quick-Logging Steppers
- **Problem:** Opening mobile OS keyboard on every set with sweaty hands causes high friction.
- **Solution:** 1-Tap quick-adjust stepper chips: `[- 80kg +]`, `+1.25kg`, `+2.5kg`, `+5kg`, and 1-tap "Seti Tamamla" button ($56\text{dp}$ height, thumb-zone optimized).

### 3.2 Occupied Machine Alternative Swap (Dolu Makine Değişimi)
- **Problem:** When an assigned machine (e.g. Leg Extension) is occupied in peak gym hours, members skip the movement or get blocked.
- **Solution:** 1-Tap **"Alternatif Egzersiz"** drawer recommending exercises targeting the same primary muscle using available branch equipment (e.g. Sissy Squat, Goblet Squat).

### 3.3 Reference-Counted Screen WakeLock (`useScreenWakeLock`)
- Keeps display active during active workouts and rest timers.
- Reference counting prevents child timer components from releasing the lock held by the workout view.
- Auto-recovers on `visibilitychange` when returning from background apps (e.g. Spotify).

### 3.4 Web Worker Rest Timer with Sensory Feedback
- Accurate countdown independent of mobile browser tab background throttling.
- Soft haptic tick at $-3\text{s}$, $-2\text{s}$, $-1\text{s}$ (`navigator.vibrate(50)`); dual pulse + Web Audio chime at $0\text{s}$.

---

## 4. Offline Basement Queue & Transactional Sync

```
[Mobile PWA / IndexedDB Queue]
        │ (Stores sessions with client_session_id & client_set_id UUIDs)
        ▼ (On online event / sync trigger)
POST /api/v1/workouts/sync
        │ (Header: Idempotency-Key = syncBatchId)
        ▼
[FastAPI Idempotency Middleware]
        │
        ├── If syncBatchId already SUCCEEDED ➔ Return cached 200 OK
        │
        ▼ (In single DB Transaction)
[PostgreSQL Upsert]
        ├── INSERT ... ON CONFLICT (tenant_id, member_id, client_session_id) DO UPDATE ...
        ├── INSERT ... ON CONFLICT (session_id, client_set_id) DO UPDATE ...
        ├── INSERT INTO outbox (event_type: 'workout.session_completed', ...)
        │
        ▼
[Response 200 OK]
```

---

## 5. Pure Calculation Engine (`frontend/shared/workout-engine/`)

The pure TypeScript calculation engine is fully tested (14/14 tests passing) and strictly adheres to Karpathy's principles (zero `any`, deterministic math, no external runtime dependencies):

1. **`onerm.ts`:** Epley & Brzycki formulas capped at $\le 12$ reps (`REP_CAP = 12`).
2. **`progression.ts`:** Linear, Greyskull LP, Double progression, and $10\%$ deload logic.
3. **`muscles.ts`:** 18-region anatomical load calculation and 0–4 discrete heatmap shading.
4. **`effort.ts`:** Bidirectional $\text{RPE} \leftrightarrow \text{RIR}$ conversion ($RIR \le 3$ hard set filter).
5. **`wakelock.ts`:** Reference-counted Screen WakeLock manager.
6. **`importers.ts`:** Strong, Hevy, and FitNotes CSV header auto-detection and parsing.
