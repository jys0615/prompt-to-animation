import type { Generation } from '../types/generation';
import { CutCard } from './CutCard';
import { StatusBadge } from './StatusBadge';

interface Props {
  generation: Generation;
  onRegenerate: (id: string) => void;
}

export function GenerationDetail({ generation, onRegenerate }: Props) {
  const isTerminal = generation.status === 'completed' || generation.status === 'failed';

  return (
    <div className="generation-detail">
      <div className="generation-header">
        <div>
          <h2>{generation.title ?? 'Generating...'}</h2>
          {generation.scenario && <p className="scenario">{generation.scenario}</p>}
        </div>
        <div className="generation-header-right">
          <StatusBadge status={generation.status} />
          {isTerminal && (
            <button
              className="btn-secondary"
              onClick={() => onRegenerate(generation.id)}
              disabled={generation.status === 'processing'}
            >
              Regenerate
            </button>
          )}
        </div>
      </div>

      {generation.error_message && (
        <div className="error-banner">
          <strong>Error:</strong> {generation.error_message}
        </div>
      )}

      {generation.cuts.length > 0 ? (
        <div className="cuts-grid">
          {generation.cuts.map((cut) => (
            <CutCard key={cut.id} cut={cut} />
          ))}
        </div>
      ) : (
        <div className="empty-cuts">
          <div className="spinner" />
          <p>Generating scene structure...</p>
        </div>
      )}
    </div>
  );
}
