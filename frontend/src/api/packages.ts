import { apiClient } from './client';
import type {
  TripRequest,
  PackageResponse,
  ComponentChangeRequest,
  ChangeResponse,
  ChangeOption,
  CityPlan,
} from './types';

export async function createPackage(payload: TripRequest): Promise<PackageResponse> {
  return apiClient<PackageResponse>('/api/packages', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getPackage(packageId: string): Promise<PackageResponse> {
  return apiClient<PackageResponse>(`/api/packages/${encodeURIComponent(packageId)}`);
}

export async function getHotelOptions(
  packageId: string,
  city?: string
): Promise<{ options: ChangeOption[] }> {
  const query = city ? `?city=${encodeURIComponent(city)}` : '';
  return apiClient<{ options: ChangeOption[] }>(
    `/api/packages/${encodeURIComponent(packageId)}/options/hotel${query}`
  );
}

export async function getFlightOptions(
  packageId: string,
  leg: 'arrival' | 'return'
): Promise<{ options: ChangeOption[] }> {
  return apiClient<{ options: ChangeOption[] }>(
    `/api/packages/${encodeURIComponent(packageId)}/options/flight?leg=${encodeURIComponent(leg)}`
  );
}

export async function getAttractionOptions(
  packageId: string,
  date?: string,
  city?: string
): Promise<{ options: ChangeOption[] }> {
  const params = new URLSearchParams();
  if (date) params.set('date', date);
  if (city) params.set('city', city);
  const qs = params.toString() ? `?${params.toString()}` : '';
  return apiClient<{ options: ChangeOption[] }>(
    `/api/packages/${encodeURIComponent(packageId)}/options/attraction${qs}`
  );
}

export async function applyChange(
  packageId: string,
  payload: ComponentChangeRequest
): Promise<ChangeResponse> {
  return apiClient<ChangeResponse>(`/api/packages/${encodeURIComponent(packageId)}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
  });
}

export async function undoPackage(packageId: string): Promise<PackageResponse> {
  return apiClient<PackageResponse>(`/api/packages/${encodeURIComponent(packageId)}/undo`, {
    method: 'POST',
  });
}

export async function getCityPlans(
  packageId: string
): Promise<{ package_id: string; city_plans: CityPlan[] }> {
  return apiClient<{ package_id: string; city_plans: CityPlan[] }>(
    `/api/packages/${encodeURIComponent(packageId)}/city-plans`
  );
}

export async function rebuildPackage(
  packageId: string,
  cityPlan: CityPlan
): Promise<PackageResponse> {
  return apiClient<PackageResponse>(`/api/packages/${encodeURIComponent(packageId)}/rebuild`, {
    method: 'POST',
    body: JSON.stringify({ city_plan: cityPlan }),
  });
}

export function getExportPackageUrl(packageId: string): string {
  return `/api/packages/${encodeURIComponent(packageId)}/export`;
}
