import { useState, useEffect } from 'react';
import { getMeta } from '../api/meta';
import type { MetaResponse } from '../api/types';

export function useMeta() {
  const [data, setData] = useState<MetaResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        setLoading(true);
        setError(null);
        const res = await getMeta();
        if (!cancelled) {
          setData(res);
        }
      } catch (err: any) {
        if (!cancelled) {
          setError(err.message || 'Failed to load travel catalogue metadata');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  return { data, loading, error };
}
