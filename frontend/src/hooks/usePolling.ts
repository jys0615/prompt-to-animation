import { useEffect, useRef } from 'react';
import type { GenerationStatus } from '../types/generation';

const TERMINAL_STATUSES: GenerationStatus[] = ['completed', 'failed'];

export function usePolling(
  id: string | null,
  status: GenerationStatus | null,
  onPoll: (id: string) => void,
  intervalMs = 3000,
) {
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!id || !status || TERMINAL_STATUSES.includes(status)) return;

    timerRef.current = setTimeout(() => onPoll(id), intervalMs);
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [id, status, onPoll, intervalMs]);
}
