import { useState, useEffect, useCallback } from 'react';
import {
  getPackage,
  applyChange,
  undoPackage,
  rebuildPackage,
} from '../api/packages';
import type {
  PackageResponse,
  ComponentChangeRequest,
  CityPlan,
} from '../api/types';

export function usePackage(packageId: string | undefined) {
  const [data, setData] = useState<PackageResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [sideEffects, setSideEffects] = useState<string[]>([]);

  const fetchPackage = useCallback(async () => {
    if (!packageId) return;
    try {
      setLoading(true);
      setError(null);
      const res = await getPackage(packageId);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load package details');
    } finally {
      setLoading(false);
    }
  }, [packageId]);

  useEffect(() => {
    fetchPackage();
  }, [fetchPackage]);

  const handleChange = useCallback(
    async (changeReq: ComponentChangeRequest) => {
      if (!packageId) return;
      try {
        setActionLoading(true);
        setError(null);
        setWarnings([]);
        setSideEffects([]);
        const currentVersion = data?.version_no ?? data?.version;
        const res = await applyChange(packageId, {
          ...changeReq,
          base_version: changeReq.base_version ?? currentVersion,
        });
        if (res.warnings) setWarnings(res.warnings);
        if (res.side_effects) setSideEffects(res.side_effects);
        // Refresh full package
        await fetchPackage();
        return res;
      } catch (err: any) {
        setError(err.message || 'Failed to apply change');
        throw err;
      } finally {
        setActionLoading(false);
      }
    },
    [packageId, data, fetchPackage]
  );

  const handleUndo = useCallback(async () => {
    if (!packageId) return;
    try {
      setActionLoading(true);
      setError(null);
      const res = await undoPackage(packageId);
      setData(res);
      await fetchPackage();
      return res;
    } catch (err: any) {
      setError(err.message || 'Failed to undo package version');
      throw err;
    } finally {
      setActionLoading(false);
    }
  }, [packageId, fetchPackage]);

  const handleRebuild = useCallback(
    async (cityPlan: CityPlan) => {
      if (!packageId) return;
      try {
        setActionLoading(true);
        setError(null);
        const res = await rebuildPackage(packageId, cityPlan);
        setData(res);
        await fetchPackage();
        return res;
      } catch (err: any) {
        setError(err.message || 'Failed to rebuild package with city plan');
        throw err;
      } finally {
        setActionLoading(false);
      }
    },
    [packageId, fetchPackage]
  );

  return {
    data,
    loading,
    error,
    actionLoading,
    warnings,
    sideEffects,
    refetch: fetchPackage,
    applyChange: handleChange,
    undo: handleUndo,
    rebuild: handleRebuild,
  };
}
