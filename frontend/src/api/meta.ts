import { apiClient } from './client';
import type { MetaResponse } from './types';

export async function getMeta(): Promise<MetaResponse> {
  return apiClient<MetaResponse>('/api/meta');
}
