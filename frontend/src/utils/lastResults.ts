/**
 * Remembers the last search's "Pick your trip" results for this browser tab, so the traveler can go back to
 * them after opening one of the three options. Stored in sessionStorage; everything still works without it.
 */
import type { PackageResponse, TripRequest } from '../api/types';

const KEY = 'bmh:lastResults';

export interface LastResults {
  request: TripRequest;
  outcome: PackageResponse;
}

export function saveLastResults(value: LastResults): void {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(value));
  } catch {
    /* storage unavailable or full: going back just shows an empty search */
  }
}

export function loadLastResults(): LastResults | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as LastResults) : null;
  } catch {
    return null;
  }
}

/** True when this package was opened from the remembered results (one of the 3 options, or the cheapest trip). */
export function isFromLastResults(packageId: string | undefined): boolean {
  if (!packageId) return false;
  const last = loadLastResults();
  if (!last) return false;
  return (
    last.outcome.package_id === packageId ||
    Object.values(last.outcome.alternatives || {}).some((a) => a?.package_id === packageId)
  );
}
