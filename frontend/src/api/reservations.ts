import { apiClient } from './client';
import type { ConfirmPackageRequest, ReservationResponse } from './types';

export async function confirmPackage(
  packageId: string,
  payload?: ConfirmPackageRequest
): Promise<ReservationResponse> {
  return apiClient<ReservationResponse>(
    `/api/packages/${encodeURIComponent(packageId)}/confirm`,
    {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    }
  );
}

export async function getReservation(ref: string): Promise<ReservationResponse> {
  return apiClient<ReservationResponse>(`/api/reservations/${encodeURIComponent(ref)}`);
}
