import { apiClient } from './client';
import { normalizeParse } from './normalize';
import type { QuickRequestResponse } from './types';

export async function parseQuickRequest(text: string): Promise<QuickRequestResponse> {
  const raw = await apiClient<any>('/api/parse', {
    method: 'POST',
    body: JSON.stringify({ text }),
  });
  return normalizeParse(raw);
}
