import { apiClient } from './client';
import type { QuickRequestResponse } from './types';

export async function parseQuickRequest(text: string): Promise<QuickRequestResponse> {
  return apiClient<QuickRequestResponse>('/api/parse', {
    method: 'POST',
    body: JSON.stringify({ text }),
  });
}
