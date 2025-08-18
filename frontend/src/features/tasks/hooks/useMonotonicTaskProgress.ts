import { useEffect, useState } from 'react';
import type { TaskStatus } from '@/types/api';

// Module-level cache to persist across component instances within the session
const progressMaxCache = new Map<string, number>();

function clamp01(n: number) {
  if (Number.isNaN(n)) return 0;
  return Math.max(0, Math.min(1, n));
}

/**
 * Monotonic progress for a task: never decreases for the same task_id.
 * - Caches the max seen progress in-memory (per browser session)
 * - If status becomes completed, snaps to 1.0
 * - For failed/cancelled, keeps the max seen value
 */
export function useMonotonicTaskProgress(
  taskId?: string,
  progress?: number,
  status?: TaskStatus
) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (!taskId) return;

    const prev = progressMaxCache.get(taskId) ?? 0;
    let next = prev;

    const p = typeof progress === 'number' ? clamp01(progress) : undefined;
    if (typeof p === 'number') {
      next = Math.max(prev, p);
    }

    if (status === 'completed') {
      next = 1;
    }

    if (next !== prev) {
      progressMaxCache.set(taskId, next);
    }

    if (display !== next) {
      setDisplay(next);
    }
  }, [taskId, progress, status]);

  return display;
}

