/**
 * Screen WakeLock Utility & React Hook (Reference Counted)
 *
 * Keeps mobile devices awake during active workouts, rest timers, or turnstile QR presentation.
 * Uses reference counting so child components (e.g. Rest Timer overlays) do not inadvertently
 * release the lock held by the parent Workout Screen.
 * Automatically re-acquires the lock on document `visibilitychange` if the tab is backgrounded and restored.
 *
 * Attribution / Origin:
 * Adapted and re-engineered from openGym (DuarteSantos8 / TechLionDev) for GymClubNex.
 */

import { useEffect } from 'react';

export const isWakeLockSupported = (): boolean =>
  typeof navigator !== 'undefined' && 'wakeLock' in navigator;

interface WakeLockSentinelLike {
  release: () => Promise<void>;
  addEventListener: (type: 'release', listener: () => void) => void;
}

let activeSentinel: WakeLockSentinelLike | null = null;
let lockCount = 0;
let isAcquiring = false;

async function acquireScreenLock(): Promise<void> {
  if (lockCount <= 0 || activeSentinel || isAcquiring || !isWakeLockSupported()) {
    return;
  }
  if (typeof document !== 'undefined' && document.visibilityState !== 'visible') {
    return;
  }

  isAcquiring = true;
  try {
    const sentinel = await (
      navigator as unknown as {
        wakeLock: { request: (type: 'screen') => Promise<WakeLockSentinelLike> };
      }
    ).wakeLock.request('screen');

    if (lockCount <= 0) {
      sentinel.release().catch(() => {});
      return;
    }
    activeSentinel = sentinel;
    sentinel.addEventListener('release', () => {
      if (activeSentinel === sentinel) {
        activeSentinel = null;
      }
    });
  } catch {
    // Silently fall back if low-power mode or browser policy rejects
    activeSentinel = null;
  } finally {
    isAcquiring = false;
  }
}

const handleVisibilityChange = (): void => {
  if (typeof document !== 'undefined' && document.visibilityState === 'visible' && lockCount > 0) {
    acquireScreenLock().catch(() => {});
  }
};

export function requestScreenWakeLock(): void {
  lockCount++;
  if (lockCount > 1 && activeSentinel) return;

  if (typeof document !== 'undefined') {
    document.addEventListener('visibilitychange', handleVisibilityChange);
  }
  acquireScreenLock().catch(() => {});
}

export function releaseScreenWakeLock(): void {
  lockCount = Math.max(0, lockCount - 1);

  if (lockCount === 0) {
    if (typeof document !== 'undefined') {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    }
    if (activeSentinel) {
      activeSentinel.release().catch(() => {});
      activeSentinel = null;
    }
  }
}

/**
 * React hook to maintain screen wake lock while enabled is true.
 */
export function useScreenWakeLock(enabled: boolean): void {
  useEffect(() => {
    if (!enabled) return;
    requestScreenWakeLock();
    return () => {
      releaseScreenWakeLock();
    };
  }, [enabled]);
}
