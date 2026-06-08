import type { GenerationListItem } from '../types/generation';
import { StatusBadge } from './StatusBadge';

interface Props {
  items: GenerationListItem[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function HistorySidebar({ items, selectedId, onSelect }: Props) {
  if (items.length === 0) return null;

  return (
    <aside className="history-sidebar">
      <h3>History</h3>
      <ul>
        {items.map((item) => (
          <li
            key={item.id}
            className={`history-item ${selectedId === item.id ? 'active' : ''}`}
            onClick={() => onSelect(item.id)}
          >
            <span className="history-prompt">{item.user_prompt}</span>
            <StatusBadge status={item.status} />
          </li>
        ))}
      </ul>
    </aside>
  );
}
