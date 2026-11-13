import { apiClient } from './client';
import { normalizeReservation } from './normalize';
import type { ConfirmPackageRequest, ReservationResponse } from './types';

export async function confirmPackage(
  packageId: string,
  payload?: ConfirmPackageRequest
): Promise<ReservationResponse> {
  const raw = await apiClient<any>(`/api/packages/${encodeURIComponent(packageId)}/confirm`, {
    method: 'POST',
    body: JSON.stringify(payload || {}),
  });
  return normalizeReservation(raw);
}

export async function getReservation(ref: string): Promise<ReservationResponse> {
  return normalizeReservation(await apiClient<any>(`/api/reservations/${encodeURIComponent(ref)}`));
}
