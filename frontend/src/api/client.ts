export interface ApiErrorPayload {
  code: string;
  message: string;
  details?: unknown;
}

/** Turns the backend's {code, message, details} into one readable sentence. */
function describeError(payload: ApiErrorPayload): string {
  const base = payload.message || 'API request failed';
  const d = (payload.details || {}) as Record<string, any>;
  if (d.field_errors && typeof d.field_errors === 'object') {
    const parts = Object.entries(d.field_errors).map(([f, m]) => (f === 'request' ? String(m) : `${f.replace(/_/g, ' ')}: ${m}`));
    if (parts.length) return parts.join(' • ');
  }
  if (Array.isArray(d.violations) && d.violations.length) {
    return `${base}: ${d.violations.map((v: any) => v.message || v.rule_id).join(' • ')}`;
  }
  return base;
}

export class ApiError extends Error {
  code: string;
  details?: unknown;
  status: number;

  constructor(status: number, payload: ApiErrorPayload) {
    super(describeError(payload));
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

  let response: Response;
  try {
    response = await fetch(endpoint, { ...options, headers });
  } catch {
    throw new ApiError(0, {
      code: 'NETWORK_ERROR',
      message: 'Cannot reach the backend. Is it running on http://localhost:8000?',
    });
  }

  if (!response.ok) {
    let errorPayload: ApiErrorPayload;
    try {
      errorPayload = await response.json();
      if (!errorPayload || typeof errorPayload !== 'object') throw new Error('bad error body');
    } catch {
      errorPayload =
        response.status >= 500
          ? {
              code: 'BACKEND_UNAVAILABLE',
              message: 'The backend did not answer. Start it with: uvicorn app.main:app --reload (in backend/).',
            }
          : { code: `HTTP_${response.status}`, message: response.statusText || 'An unexpected error occurred' };
    }
    throw new ApiError(response.status, errorPayload);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}
