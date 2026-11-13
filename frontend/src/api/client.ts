export interface ApiErrorPayload {
  code: string;
  message: string;
  details?: unknown;
}

export class ApiError extends Error {
  code: string;
  details?: unknown;
  status: number;

  constructor(status: number, payload: ApiErrorPayload) {
    super(payload.message || 'API request failed');
    this.name = 'ApiError';
    this.status = status;
    this.code = payload.code || 'UNKNOWN_ERROR';
    this.details = payload.details;
  }
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(endpoint, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorPayload: ApiErrorPayload;
    try {
      errorPayload = await response.json();
    } catch {
      errorPayload = {
        code: `HTTP_${response.status}`,
        message: response.statusText || 'An unexpected error occurred',
      };
    }
    throw new ApiError(response.status, errorPayload);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}
