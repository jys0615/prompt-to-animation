import type { GenerationStatus } from '../types/generation';

const LABELS: Record<GenerationStatus, string> = {
  pending: 'Pending',
  processing: 'Processing...',
  completed: 'Completed',
  failed: 'Failed',
};

export function StatusBadge({ status }: { status: GenerationStatus }) {
  return <span className={`status-badge status-${status}`}>{LABELS[status]}</span>;
}
