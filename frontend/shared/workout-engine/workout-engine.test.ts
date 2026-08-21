import { describe, it, expect } from 'vitest';
import { estimate1RM, bestSetOf } from './onerm';
import {
  determineNextPrescription,
  calculateDeload,
  evaluateSession,
} from './progression';
import {
  calculateMuscleLoad,
  calculateHeatmapLevels,
  getMuscleWeights,
} from './muscles';
import {
  extractRir,
  convertRirToScale,
  isHardSet,
  calculateAverageRir,
} from './effort';
import { parseCsvRows, detectSourceApp } from './importers';

describe('Workout Engine - 1RM Estimations', () => {
  it('calculates accurate 1RM using Epley formula', () => {
    // 100kg x 10 reps = 100 * (1 + 10/30) = 133.3 kg
    const est = estimate1RM(100, 10, 'epley');
    expect(est).toBe(133.3);
  });

  it('calculates accurate 1RM using Brzycki formula', () => {
    // 100kg x 5 reps = 100 * 36 / (37 - 5) = 112.5 kg
    const est = estimate1RM(100, 5, 'brzycki');
    expect(est).toBe(112.5);
  });

  it('calculates accurate 1RM using Lombardi, Lander, Mayhew, OConner, Wathan formulas', () => {
    expect(estimate1RM(100, 5, 'lombardi')).toBe(117.5);
    expect(estimate1RM(100, 5, 'lander')).toBe(113.7);
    expect(estimate1RM(100, 5, 'mayhew')).toBe(119.0);
    expect(estimate1RM(100, 5, 'oconner')).toBe(112.5);
    expect(estimate1RM(100, 5, 'wathan')).toBe(116.5);
  });

  it('returns exact weight for a 1-rep set', () => {
    expect(estimate1RM(140, 1)).toBe(140);
  });

  it('returns null for reps exceeding safety cap (> 12 reps)', () => {
    expect(estimate1RM(50, 15)).toBeNull();
  });

  it('identifies the best set from an entry', () => {
    const entry = {
      id: 'bench-press',
      sets: [
        { w: 80, r: 10, done: true }, // 106.7
        { w: 90, r: 8, done: true },  // 114.0
        { w: 100, r: 5, done: true }, // 116.7
        { w: 110, r: 2, done: false }, // not done
      ],
    };
    const best = bestSetOf(entry);
    expect(best).not.toBeNull();
    expect(best?.est).toBe(116.7);
    expect(best?.w).toBe(100);
    expect(best?.r).toBe(5);
  });
});

describe('Workout Engine - Progressive Overload', () => {
  it('increments load on successful linear progression session', () => {
    const pastSessions = [
      {
        mode: 'reps' as const,
        goal: 5,
        weight: 100,
        ok: true,
        reps: [5, 5, 5],
      },
    ];
    const prescription = determineNextPrescription(
      pastSessions,
      { id: 'squat', prog: 'linear', inc: 5 }
    );
    expect(prescription.kind).toBe('up');
    expect(prescription.weight).toBe(105);
  });

  it('triggers a 10% deload after 3 consecutive stalled sessions in linear progression', () => {
    const failedSession = {
      mode: 'reps' as const,
      goal: 5,
      weight: 100,
      ok: false,
      reps: [5, 4, 3],
    };
    const pastSessions = [failedSession, failedSession, failedSession];
    const prescription = determineNextPrescription(
      pastSessions,
      { id: 'squat', prog: 'linear', inc: 2.5 }
    );
    expect(prescription.kind).toBe('deload');
    expect(prescription.weight).toBe(90); // 100 * 0.9 = 90
  });

  it('triggers double jump on Greyskull LP when AMRAP >= 2x target', () => {
    const pastSessions = [
      {
        mode: 'reps' as const,
        goal: 5,
        weight: 60,
        ok: true,
        reps: [5, 5, 11], // 11 >= 5*2
        amrap: 11,
      },
    ];
    const prescription = determineNextPrescription(
      pastSessions,
      { id: 'bench-press', prog: 'greyskull', inc: 2.5 }
    );
    expect(prescription.kind).toBe('up');
    expect(prescription.weight).toBe(65); // 60 + 2*2.5 = 65
  });

  it('handles bodyweight rep ceiling and adds extra set', () => {
    const pastSessions = [
      {
        mode: 'reps' as const,
        goal: 20,
        weight: 0,
        ok: true,
        reps: [20, 20, 20],
        count: 3,
      },
    ];
    const prescription = determineNextPrescription(
      pastSessions,
      { id: 'push-up', prog: 'linear', reps: 10, repsMax: 20, sets: 3 }
    );
    expect(prescription.kind).toBe('up');
    expect(prescription.weight).toBe(0);
    expect(prescription.sets).toBe(4);
    expect(prescription.reps).toBe(10);
  });
});

describe('Workout Engine - Muscle & Volume Map', () => {
  it('calculates primary and secondary muscle load correctly', () => {
    const benchPress = {
      targetMuscle: 'pectorals',
      secondaryMuscles: ['triceps', 'shoulders'],
    };
    const weights = getMuscleWeights(benchPress);
    expect(weights.chest).toBe(1.0);
    expect(weights.triceps).toBe(0.4);
    expect(weights.deltoids).toBe(0.4);

    const load = calculateMuscleLoad([
      { exercise: benchPress, completedSetsCount: 5 },
    ]);
    expect(load.chest).toBe(5.0);
    expect(load.triceps).toBe(2.0);
    expect(load.deltoids).toBe(2.0);

    const levels = calculateHeatmapLevels(load);
    expect(levels.chest).toBe(4); // Max gets level 4
    expect(levels.triceps).toBe(2); // 2.0 / 5.0 * 4 = 1.6 -> ceil = 2
  });
});

describe('Workout Engine - Effort & Fatigue', () => {
  it('converts RPE and RIR bidirectionally', () => {
    expect(extractRir({ rpe: 8 })).toBe(2);
    expect(extractRir({ rir: 1 })).toBe(1);
    expect(convertRirToScale('rpe', 2)).toBe(8);
  });

  it('filters hard sets', () => {
    expect(isHardSet({ rir: 2 })).toBe(true);
    expect(isHardSet({ rir: 4 })).toBe(false);
  });

  it('calculates average RIR across multiple sets', () => {
    const avg = calculateAverageRir([{ rir: 1 }, { rir: 2 }, { rpe: 7 }]); // 1, 2, 3
    expect(avg).toBe(2.0);
  });
});

describe('Workout Engine - CSV Importers', () => {
  it('correctly parses CSV quotes and commas', () => {
    const csv = 'Date,Exercise,Weight\n2026-08-01,"Bench Press, Close Grip",80\n2026-08-02,Squat,100';
    const rows = parseCsvRows(csv);
    expect(rows.length).toBe(3);
    expect(rows[1][1]).toBe('Bench Press, Close Grip');
  });

  it('identifies source apps from headers', () => {
    expect(detectSourceApp(['Date', 'Exercise Name', 'Set Order', 'Weight', 'Reps'])).toBe('Strong');
    expect(detectSourceApp(['title', 'exercise_title', 'set_index', 'weight_kg'])).toBe('Hevy');
  });
});
