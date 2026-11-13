import { apiClient } from './client';
import { normalizeCityPlan, normalizeOption, normalizePackageResponse } from './normalize';
import type {
  TripRequest,
  PackageResponse,
  ComponentChangeRequest,
  ChangeResponse,
  ChangeOption,
  CityPlan,
} from './types';

const pkgUrl = (id: string) => `/api/packages/${encodeURIComponent(id)}`;

export async function createPackage(payload: TripRequest): Promise<PackageResponse> {
  const raw = await apiClient<any>('/api/packages', { method: 'POST', body: JSON.stringify(payload) });
  return normalizePackageResponse(raw);
}

export async function getPackage(packageId: string): Promise<PackageResponse> {
  return normalizePackageResponse(await apiClient<any>(pkgUrl(packageId)));
}

async function options(packageId: string, kind: string, params: Record<string, string | undefined>) {
  const qs = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => v && qs.set(k, v));
  const raw = await apiClient<any>(`${pkgUrl(packageId)}/options/${kind}${qs.toString() ? `?${qs}` : ''}`);
  return { options: (raw.options || []).map(normalizeOption) as ChangeOption[] };
}

export function getHotelOptions(packageId: string, city?: string) {
  return options(packageId, 'hotel', { city });
}

export function getFlightOptions(packageId: string, leg: 'arrival' | 'return') {
  return options(packageId, 'flight', { leg });
}

export function getAttractionOptions(packageId: string, date?: string, city?: string) {
  return options(packageId, 'attraction', { date, city });
}

export async function applyChange(packageId: string, payload: ComponentChangeRequest): Promise<ChangeResponse> {
  return apiClient<ChangeResponse>(pkgUrl(packageId), { method: 'PATCH', body: JSON.stringify(payload) });
}

export async function undoPackage(packageId: string): Promise<PackageResponse> {
  const raw = await apiClient<any>(`${pkgUrl(packageId)}/undo`, { method: 'POST' });
  return normalizePackageResponse(raw.package || raw);
}

export async function getCityPlans(packageId: string): Promise<{ package_id: string; city_plans: CityPlan[] }> {
  const raw = await apiClient<any>(`${pkgUrl(packageId)}/city-plans`);
  return { package_id: raw.package_id, city_plans: (raw.city_plans || []).map(normalizeCityPlan) };
}

export async function rebuildPackage(packageId: string, cityPlan: CityPlan, baseVersion?: number): Promise<PackageResponse> {
  const raw = await apiClient<any>(`${pkgUrl(packageId)}/rebuild`, {
    method: 'POST',
    body: JSON.stringify({ city_plan: cityPlan.plan, base_version: baseVersion }),
  });
  return normalizePackageResponse(raw);
}

export function getExportPackageUrl(packageId: string): string {
  return `${pkgUrl(packageId)}/export`;
}
