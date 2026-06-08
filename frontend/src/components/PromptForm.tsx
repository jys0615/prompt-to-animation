import { useState } from 'react';

interface Props {
  onSubmit: (prompt: string) => void;
  loading: boolean;
}

export function PromptForm({ onSubmit, loading }: Props) {
  const [value, setValue] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = value.trim();
    if (!trimmed) return;
    onSubmit(trimmed);
  };

  return (
    <form onSubmit={handleSubmit} className="prompt-form">
      <textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        placeholder="Describe the animation you want to create... (e.g. 'A lone astronaut walking on Mars at sunset')"
        rows={4}
        disabled={loading}
        maxLength={2000}
      />
      <div className="prompt-form-footer">
        <span className="char-count">{value.length} / 2000</span>
        <button type="submit" disabled={loading || !value.trim()}>
          {loading ? 'Generating...' : 'Generate Animation'}
        </button>
      </div>
    </form>
  );
}
