/**
 * Effort & Fatigue Rating Engine (RPE vs RIR)
 *
 * Implements bidirectional mapping between Rate of Perceived Exertion (RPE)
 * and Reps In Reserve (RIR), along with effective fatigue aggregations.
 *
 * Attribution / Origin:
 * Adapted and re-engineered from openGym (DuarteSantos8 / TechLionDev) for GymClubNex.
 */

export interface RatedSet {
  rir?: number | null;
  rpe?: number | null;
  done?: boolean;
}

export const HARD_RIR_THRESHOLD = 3; // RIR <= 3 (or RPE >= 7) represents an effective adaptive set

/**
 * Extract normalized RIR from a set record.
 */
export function extractRir(set: RatedSet | null | undefined): number | null {
  if (!set) return null;
  if (typeof set.rir === 'number' && Number.isFinite(set.rir)) return set.rir;
  if (typeof set.rpe === 'number' && Number.isFinite(set.rpe)) return 10 - set.rpe;
  return null;
}

/**
 * Convert RIR to user's preferred display scale.
 */
export function convertRirToScale(scale: 'rpe' | 'rir', rir: number | null): number | null {
  if (rir === null || !Number.isFinite(rir)) return null;
  const value = scale === 'rpe' ? 10 - rir : rir;
  return Math.round(value * 10) / 10;
}

/**
 * Test whether a set is a hard working set (close to muscular failure).
 */
export function isHardSet(set: RatedSet): boolean {
  const rir = extractRir(set);
  return rir !== null && rir <= HARD_RIR_THRESHOLD;
}

/**
 * Calculate average RIR across completed sets.
 */
export function calculateAverageRir(sets: RatedSet[]): number | null {
  const rirValues = sets.map(extractRir).filter((v): v is number => v !== null);
  if (!rirValues.length) return null;
  const sum = rirValues.reduce((a, b) => a + b, 0);
  return Math.round((sum / rirValues.length) * 10) / 10;
}
