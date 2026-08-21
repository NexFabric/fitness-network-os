/**
 * Muscle Group & Volume Distribution Engine
 *
 * Maps exercises and completed sets to 18 anatomical muscle regions
 * for front/back body heatmap visualization and workout volume balance analysis.
 *
 * Attribution / Origin:
 * Adapted and re-engineered from openGym (DuarteSantos8 / TechLionDev) for GymClubNex.
 */

export const ANATOMICAL_MUSCLES = [
  'trapezius',
  'deltoids',
  'chest',
  'upper-back',
  'serratus',
  'biceps',
  'triceps',
  'forearm',
  'abs',
  'obliques',
  'lower-back',
  'gluteal',
  'quadriceps',
  'hamstring',
  'adductors',
  'hip-flexors',
  'calves',
  'tibialis',
] as const;

export type AnatomicalMuscle = (typeof ANATOMICAL_MUSCLES)[number];

export const MUSCLE_LABELS_TR: Record<AnatomicalMuscle, string> = {
  trapezius: 'Trapez',
  deltoids: 'Omuz',
  chest: 'Göğüs',
  'upper-back': 'Üst Sırt / Kanat',
  serratus: 'Serratus',
  biceps: 'Biceps (Ön Kol)',
  triceps: 'Triceps (Arka Kol)',
  forearm: 'Bilek & Ön Kol',
  abs: 'Karın (Abs)',
  obliques: 'Oblik (Yan Karın)',
  'lower-back': 'Bel (Alt Sırt)',
  gluteal: 'Kalça (Glute)',
  quadriceps: 'Ön Bacak (Quad)',
  hamstring: 'Arka Bacak (Hamstring)',
  adductors: 'İç Bacak (Adductor)',
  'hip-flexors': 'Kalça Fleksörleri',
  calves: 'Kalf',
  tibialis: 'Kaval Kemiği Kası (Tibialis)',
};

const MUSCLE_ALIAS: Record<string, AnatomicalMuscle | null> = {
  // Primaries
  abs: 'abs',
  pectorals: 'chest',
  biceps: 'biceps',
  glutes: 'gluteal',
  delts: 'deltoids',
  triceps: 'triceps',
  'upper back': 'upper-back',
  lats: 'upper-back',
  calves: 'calves',
  quads: 'quadriceps',
  forearms: 'forearm',
  hamstrings: 'hamstring',
  spine: 'lower-back',
  traps: 'trapezius',
  adductors: 'adductors',
  'serratus anterior': 'serratus',
  abductors: 'gluteal',
  'levator scapulae': 'trapezius',
  'cardiovascular system': null,

  // Secondaries
  shoulders: 'deltoids',
  deltoids: 'deltoids',
  'rear deltoids': 'deltoids',
  'rotator cuff': 'deltoids',
  quadriceps: 'quadriceps',
  core: 'abs',
  abdominals: 'abs',
  'lower abs': 'abs',
  chest: 'chest',
  'upper chest': 'chest',
  'hip flexors': 'hip-flexors',
  obliques: 'obliques',
  'lower back': 'lower-back',
  rhomboids: 'upper-back',
  trapezius: 'trapezius',
  back: 'upper-back',
  'latissimus dorsi': 'upper-back',
  brachialis: 'biceps',
  soleus: 'calves',
  shins: 'tibialis',
  wrists: 'forearm',
  'wrist flexors': 'forearm',
  'wrist extensors': 'forearm',
  'grip muscles': 'forearm',
  groin: 'adductors',
  'inner thighs': 'adductors',
  ankles: null,
  feet: null,
  hands: null,
};

const SECONDARY_WEIGHT = 0.4;

export interface ExerciseMuscleMapping {
  targetMuscle?: string;
  secondaryMuscles?: string[];
  bodyPart?: string;
}

export interface VolumeItem {
  exercise: ExerciseMuscleMapping;
  completedSetsCount: number;
}

/**
 * Determine muscle involvement ratios (0.0 - 1.0) for a given exercise.
 */
export function getMuscleWeights(ex: ExerciseMuscleMapping): Partial<Record<AnatomicalMuscle, number>> {
  const result: Partial<Record<AnatomicalMuscle, number>> = {};

  const add = (name: string | undefined, weight: number) => {
    if (!name) return;
    const normalized = name.toLowerCase().trim();
    const slug = MUSCLE_ALIAS[normalized];
    if (slug) {
      result[slug] = Math.max(result[slug] ?? 0, weight);
    }
  };

  add(ex.targetMuscle, 1.0);
  (ex.secondaryMuscles ?? []).forEach((m) => add(m, SECONDARY_WEIGHT));

  return result;
}

/**
 * Calculate effective sets per muscle region from workout sets volume.
 */
export function calculateMuscleLoad(items: VolumeItem[]): Record<AnatomicalMuscle, number> {
  const load = {} as Record<AnatomicalMuscle, number>;
  for (const m of ANATOMICAL_MUSCLES) {
    load[m] = 0;
  }

  for (const item of items) {
    if (item.completedSetsCount <= 0) continue;
    const weights = getMuscleWeights(item.exercise);
    for (const [muscleKey, weightRatio] of Object.entries(weights) as [AnatomicalMuscle, number][]) {
      load[muscleKey] = (load[muscleKey] ?? 0) + (weightRatio ?? 0) * item.completedSetsCount;
    }
  }

  return load;
}

/**
 * Calculate shading levels (0 - 4) for front/back body heatmap representation.
 */
export function calculateHeatmapLevels(load: Record<AnatomicalMuscle, number>): Record<AnatomicalMuscle, number> {
  const max = Math.max(0, ...ANATOMICAL_MUSCLES.map((m) => load[m] ?? 0));
  const levels = {} as Record<AnatomicalMuscle, number>;

  for (const m of ANATOMICAL_MUSCLES) {
    const val = load[m] ?? 0;
    if (val <= 0 || max <= 0) {
      levels[m] = 0;
    } else {
      levels[m] = Math.max(1, Math.min(4, Math.ceil((val / max) * 4)));
    }
  }

  return levels;
}
