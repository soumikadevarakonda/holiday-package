import { apiClient } from './client';
import { normalizeMeta } from './normalize';
import type { MetaResponse } from './types';

export async function getMeta(): Promise<MetaResponse> {
  return normalizeMeta(await apiClient<any>('/api/meta'));
}
