/**
 * One-Rep Max (1RM) Estimation Engine
 *
 * Provides submaximal strength estimations using standard sports science formulas.
 * Estimates are capped at 12 repetitions (REP_CAP = 12) to ensure validity.
 *
 * Attribution / Origin:
 * Adapted and re-engineered from openGym (DuarteSantos8 / TechLionDev) for GymClubNex.
 */

export const REP_CAP = 12;

export type OneRmFormula = 'epley' | 'brzycki' | 'lombardi';

export interface SetRecord {
  w: number; // weight in kg / lbs
  r: number; // repetitions completed
  done?: boolean;
}

export interface EntryRecord {
  id: string;
  sets: SetRecord[];
}

export interface EstimatedMaxResult {
  est: number;
  w: number;
  r: number;
}

export const ONE_RM_FORMULAS: Record<OneRmFormula, (w: number, r: number) => number> = {
  // Epley 1985 — w * (1 + r / 30)
  epley: (w: number, r: number) => w * (1 + r / 30),
  // Brzycki 1993 — w * 36 / (37 - r)
  brzycki: (w: number, r: number) => (w * 36) / (37 - r),
  // Lombardi 1989 — w * (r ^ 0.10)
  lombardi: (w: number, r: number) => w * Math.pow(r, 0.1),
};

export const DEFAULT_FORMULA: OneRmFormula = 'epley';

/**
 * Estimate 1RM from a single set.
 * Returns null if input is invalid, load <= 0, reps < 1, or reps > REP_CAP.
 */
export function estimate1RM(
  weightInput: number | string,
  repsInput: number | string,
  formula: OneRmFormula = DEFAULT_FORMULA
): number | null {
  const weight = Number(weightInput);
  const reps = Number(repsInput);

  if (!Number.isFinite(weight) || !Number.isFinite(reps)) return null;
  if (weight <= 0 || reps < 1) return null;
  if (reps > REP_CAP) return null;

  if (reps === 1) {
    return Math.round(weight * 10) / 10;
  }

  const calculationFn = ONE_RM_FORMULAS[formula] ?? ONE_RM_FORMULAS[DEFAULT_FORMULA];
  const roundedReps = Math.round(reps);
  const estimated = calculationFn(weight, roundedReps);

  if (!Number.isFinite(estimated) || estimated <= 0) return null;

  return Math.round(estimated * 10) / 10;
}

/**
 * Determine the best 1RM estimate from an exercise's completed sets in a single workout entry.
 */
export function bestSetOf(
  entry: EntryRecord | null | undefined,
  formula: OneRmFormula = DEFAULT_FORMULA
): EstimatedMaxResult | null {
  if (!entry?.sets?.length) return null;

  let best: EstimatedMaxResult | null = null;

  for (const set of entry.sets) {
    if (!set.done) continue;
    const est = estimate1RM(set.w, set.r, formula);
    if (est !== null && (!best || est > best.est)) {
      best = {
        est,
        w: Number(set.w),
        r: Math.round(Number(set.r)),
      };
    }
  }

  return best;
}
