import { useCallback, useEffect, useState } from 'react';
import { getGeneration, listGenerations, regenerate, startGeneration } from './api/generations';
import { GenerationDetail } from './components/GenerationDetail';
import { HistorySidebar } from './components/HistorySidebar';
import { PromptForm } from './components/PromptForm';
import { usePolling } from './hooks/usePolling';
import type { Generation, GenerationListItem } from './types/generation';
import './index.css';

export default function App() {
  const [history, setHistory] = useState<GenerationListItem[]>([]);
  const [current, setCurrent] = useState<Generation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listGenerations().then(setHistory).catch(console.error);
  }, []);

  const fetchCurrent = useCallback(async (id: string) => {
    try {
      const gen = await getGeneration(id);
      setCurrent(gen);
      setHistory((prev) =>
        prev.map((h) =>
          h.id === id ? { ...h, status: gen.status, title: gen.title } : h,
        ),
      );
    } catch (e) {
      console.error(e);
    }
  }, []);

  usePolling(current?.id ?? null, current?.status ?? null, fetchCurrent);

  const handleSubmit = async (prompt: string) => {
    setLoading(true);
    setError(null);
    try {
      const gen = await startGeneration(prompt);
      setCurrent(gen);
      setHistory((prev) => [
        {
          id: gen.id,
          user_prompt: gen.user_prompt,
          title: gen.title,
          status: gen.status,
          created_at: gen.created_at,
        },
        ...prev,
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to start generation');
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = async (id: string) => {
    const gen = await getGeneration(id);
    setCurrent(gen);
  };

  const handleRegenerate = async (id: string) => {
    try {
      const gen = await regenerate(id);
      setCurrent(gen);
      setHistory((prev) =>
        prev.map((h) => (h.id === id ? { ...h, status: gen.status } : h)),
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to regenerate');
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Prompt-to-Animation</h1>
        <p>Turn your words into animated videos</p>
      </header>

      <div className="app-body">
        <HistorySidebar
          items={history}
          selectedId={current?.id ?? null}
          onSelect={handleSelect}
        />

        <main className="app-main">
          <PromptForm onSubmit={handleSubmit} loading={loading} />
          {error && <div className="error-banner">{error}</div>}
          {current && (
            <GenerationDetail generation={current} onRegenerate={handleRegenerate} />
          )}
        </main>
      </div>
    </div>
  );
}
