/**
 * Progressive Overload & Prescription Engine
 *
 * Implements deterministic progression models:
 * - Linear Progression (standard periodic increment with deload on 3 consecutive stalls)
 * - Greyskull LP (AMRAP top-set double jump, 10% deload on single failure)
 * - Double Progression (rep range progression before load increase)
 * - Bodyweight Progression (rep ladders with set additions up to 6 sets)
 * - Timed Progression (isometric holds with second-based steps)
 *
 * Attribution / Origin:
 * Adapted and re-engineered from openGym (DuarteSantos8 / TechLionDev) for GymClubNex.
 */

export type ProgressionPolicy = 'off' | 'linear' | 'greyskull' | 'double' | 'time';
export type ExerciseMode = 'reps' | 'time' | 'cardio';
export type PrescriptionKind = 'first' | 'up' | 'hold' | 'deload' | 'off';

export interface ExerciseConfig {
  id: string;
  prog?: ProgressionPolicy;
  mode?: ExerciseMode;
  inc?: number;
  sets?: number;
  reps?: number;
  repsMin?: number;
  repsMax?: number;
  sec?: number;
  isUnilateral?: boolean;
}

export interface ExecutedSet {
  w?: number;
  r?: number;
  sec?: number;
  done?: boolean;
}

export interface WorkoutSessionSummary {
  mode: ExerciseMode;
  goal: number;
  weight: number;
  ok: boolean;
  reps?: number[];
  held?: number[];
  amrap?: number;
  low?: number;
  count?: number;
}

export interface Prescription {
  policy: ProgressionPolicy;
  kind: PrescriptionKind;
  weight?: number;
  reps?: number;
  sets?: number;
  sec?: number;
  why: (string | number)[];
}

export const DELOAD_AFTER: Record<ProgressionPolicy, number> = {
  off: 999,
  linear: 3,
  greyskull: 1,
  double: 3,
  time: 3,
};

export const DELOAD_FACTOR = 0.9;
export const MAX_BW_SETS = 6;
export const DEFAULT_SEC_INCREMENT = 5;

const snap = (v: number, step: number): number => {
  if (step <= 0) return Math.round(v * 10) / 10;
  return Math.round((Math.round(v / step) * step) * 10) / 10;
};

export function calculateDeload(currentWeight: number, step: number): number {
  let next = snap(currentWeight * DELOAD_FACTOR, step);
  if (next >= currentWeight) {
    next = snap(currentWeight - step, step);
  }
  return Math.max(step, next);
}

export function evaluateSession(
  sets: ExecutedSet[],
  target: ExerciseConfig
): WorkoutSessionSummary {
  const mode = target.mode ?? 'reps';
  const plannedSets = target.sets ?? sets.length;
  const enoughSets = sets.length >= plannedSets;

  if (mode === 'time') {
    const goal = target.sec ?? 0;
    const held = sets.map((s) => (s.done ? s.sec ?? 0 : 0));
    const completedSets = sets.filter((s) => s.done);
    const weight = Math.max(0, ...completedSets.map((s) => s.w ?? 0));
    const ok = goal > 0 && enoughSets && held.length > 0 && held.every((h) => h >= goal);

    return {
      mode: 'time',
      goal,
      held,
      weight,
      ok,
    };
  }

  const goal = target.reps ?? 0;
  const reps = sets.map((s) => (s.done ? s.r ?? 0 : 0));
  const completedSets = sets.filter((s) => s.done);
  const weight = Math.max(0, ...completedSets.map((s) => s.w ?? 0));
  const ok = goal > 0 && enoughSets && reps.length > 0 && reps.every((r) => r >= goal);

  return {
    mode: 'reps',
    goal,
    reps,
    weight,
    count: reps.length,
    low: reps.length ? Math.min(...reps) : 0,
    amrap: reps.length ? reps[reps.length - 1] : 0,
    ok,
  };
}

export function calculateStallCount(sessions: WorkoutSessionSummary[]): number {
  let count = 0;
  for (let i = sessions.length - 1; i >= 0; i--) {
    if (sessions[i].ok) break;
    count++;
  }
  return count;
}

export function determineNextPrescription(
  pastSessions: WorkoutSessionSummary[],
  cfg: ExerciseConfig,
  unit: 'kg' | 'lb' = 'kg'
): Prescription {
  const mode = cfg.mode ?? 'reps';
  const policy = cfg.prog ?? (mode === 'reps' ? 'linear' : 'off');
  const defaultInc = unit === 'lb' ? 5 : 2.5;
  const inc = cfg.inc && cfg.inc > 0 ? cfg.inc : mode === 'time' ? DEFAULT_SEC_INCREMENT : defaultInc;

  if (policy === 'off') {
    return { policy: 'off', kind: 'off', why: ['Automatic progression is disabled.'] };
  }

  const filteredSessions = pastSessions.filter((s) => s.mode === mode);
  const last = filteredSessions[filteredSessions.length - 1];

  if (!last) {
    return {
      policy,
      kind: 'first',
      why: ['No completed sessions recorded yet — this session establishes the initial baseline.'],
    };
  }

  const stalls = calculateStallCount(filteredSessions);
  const deloadThreshold = DELOAD_AFTER[policy] ?? 3;

  if (mode === 'time') {
    if (last.ok) {
      const sec = (last.goal || cfg.sec || 0) + inc;
      return {
        policy,
        kind: 'up',
        sec,
        why: ['Successfully held all sets for target duration — increasing target by', inc, 'seconds.'],
      };
    }
    if (stalls >= deloadThreshold) {
      const sec = calculateDeload(last.goal || cfg.sec || 0, 5);
      return {
        policy,
        kind: 'deload',
        sec,
        why: ['Target missed for', stalls, 'consecutive sessions — deloading duration to', sec, 'seconds.'],
      };
    }
    return {
      policy,
      kind: 'hold',
      sec: last.goal || cfg.sec,
      why: ['Previous session fell short of time target — repeating target duration.'],
    };
  }

  const weight = last.weight;

  // Bodyweight progression (load <= 0)
  if (weight <= 0) {
    const goal = last.goal || cfg.reps || 0;
    if (!last.ok || goal <= 0) {
      return {
        policy,
        kind: 'hold',
        weight: 0,
        reps: goal || undefined,
        why: ['Bodyweight exercise — maintain reps until all sets are completed with clean form.'],
      };
    }

    const maxRepsCeiling = cfg.repsMax ?? 0;
    if (maxRepsCeiling > 0 && goal >= maxRepsCeiling) {
      const currentSets = cfg.sets || last.count || 1;
      const nextSets = currentSets + 1;
      const baseReps = Math.max(1, cfg.reps || maxRepsCeiling);

      if (nextSets <= MAX_BW_SETS) {
        return {
          policy,
          kind: 'up',
          weight: 0,
          reps: baseReps,
          sets: nextSets,
          why: ['Reached rep ceiling across all sets — adding an extra set and resetting reps to baseline.'],
        };
      }

      return {
        policy,
        kind: 'hold',
        weight: 0,
        reps: goal,
        why: ['Reached maximum volume (6 sets) — recommend adding external load (dip belt) or harder variation.'],
      };
    }

    const step = cfg.isUnilateral ? 2 : 1;
    const nextReps = goal + step;
    return {
      policy,
      kind: 'up',
      weight: 0,
      reps: nextReps,
      why: ['All reps completed in previous session — increasing target reps to', nextReps],
    };
  }

  // Double progression (work up through rep range)
  if (policy === 'double') {
    const top = cfg.reps || last.goal || 10;
    const bottom = Math.min(cfg.repsMin || Math.max(1, top - 2), top);

    if (last.ok) {
      return {
        policy,
        kind: 'up',
        weight: snap(weight + inc, inc),
        reps: bottom,
        why: ['Top of rep range achieved across all sets — increasing weight by', inc, unit, 'and resetting reps to', bottom],
      };
    }

    if (stalls >= deloadThreshold) {
      const deloadWeight = calculateDeload(weight, inc);
      return {
        policy,
        kind: 'deload',
        weight: deloadWeight,
        reps: bottom,
        why: ['Stalled for', stalls, 'sessions — deloading weight to', deloadWeight, unit],
      };
    }

    const aimReps = Math.min(top, Math.max(bottom, (last.low ?? 0) + 1));
    return {
      policy,
      kind: 'hold',
      weight,
      reps: aimReps,
      why: ['Maintaining weight — aiming for', aimReps, 'reps on next attempt.'],
    };
  }

  // Linear / Greyskull progression
  if (last.ok) {
    const isGreyskullDoubleJump =
      policy === 'greyskull' && last.goal > 0 && (last.amrap ?? 0) >= last.goal * 2;
    const step = isGreyskullDoubleJump ? inc * 2 : inc;

    return {
      policy,
      kind: 'up',
      weight: snap(weight + step, inc),
      why: isGreyskullDoubleJump
        ? ['AMRAP final set achieved double target reps — double jump of', step, unit]
        : ['All target reps achieved — increasing load by', step, unit],
    };
  }

  if (stalls >= deloadThreshold) {
    const deloadWeight = calculateDeload(weight, inc);
    return {
      policy,
      kind: 'deload',
      weight: deloadWeight,
      why: ['Stalled for', stalls, 'consecutive sessions — resetting load by 10% to', deloadWeight, unit],
    };
  }

  return {
    policy,
    kind: 'hold',
    weight,
    why: ['Missed target reps in previous session — attempting same load again.'],
  };
}
