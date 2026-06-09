import type { Generation, GenerationListItem } from '../types/generation';

const BASE_URL = '';

export async function startGeneration(prompt: string): Promise<Generation> {
  const res = await fetch(`${BASE_URL}/api/generations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) throw new Error(`Failed to start generation: ${res.statusText}`);
  return res.json();
}

export async function getGeneration(id: string): Promise<Generation> {
  const res = await fetch(`${BASE_URL}/api/generations/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch generation: ${res.statusText}`);
  return res.json();
}

export async function listGenerations(): Promise<GenerationListItem[]> {
  const res = await fetch(`${BASE_URL}/api/generations`);
  if (!res.ok) throw new Error(`Failed to list generations: ${res.statusText}`);
  return res.json();
}

export async function regenerate(id: string): Promise<Generation> {
  const res = await fetch(`${BASE_URL}/api/generations/${id}/regenerate`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error(`Failed to regenerate: ${res.statusText}`);
  return res.json();
}
