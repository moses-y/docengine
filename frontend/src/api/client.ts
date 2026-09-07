/** Thin fetch wrapper: JSON in/out, credentials for the auth cookie, and a
 * typed `ApiClientError` so callers can read the server's error envelope
 * (`{"error": {code, message, field}}`, per PRD §4.5) without re-parsing.
 */
import { API_BASE_URL } from "../lib/constants";
import { getToken } from "../lib/token";
import type { ApiErrorBody } from "../types";

export class ApiClientError extends Error {
  code: string;
  field: string | null;
  status: number;

  constructor(status: number, body: ApiErrorBody) {
    super(body.error.message);
    this.status = status;
    this.code = body.error.code;
    this.field = body.error.field;
  }
}

async function parseErrorBody(response: Response): Promise<ApiErrorBody> {
  try {
    return await response.json();
  } catch {
    return { error: { code: "unknown", message: response.statusText, field: null } };
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  isFormData?: boolean;
}

export async function apiFetch<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, isFormData = false } = options;

  // Send the token explicitly when we have one. `credentials: "include"` stays
  // so the httpOnly cookie still works same-origin, but the header is what
  // makes auth survive a split-hostname deployment where the cookie is
  // cross-site and therefore withheld. See ../lib/token.ts.
  const headers: Record<string, string> = isFormData ? {} : { "Content-Type": "application/json" };
  const token = getToken();
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const init: RequestInit = {
    method,
    credentials: "include",
    headers: Object.keys(headers).length > 0 ? headers : undefined,
    body: isFormData ? (body as FormData) : body !== undefined ? JSON.stringify(body) : undefined,
  };

  const response = await fetch(`${API_BASE_URL}${path}`, init);

  if (response.status === 204) {
    return undefined as T;
  }

  if (!response.ok) {
    throw new ApiClientError(response.status, await parseErrorBody(response));
  }

  return (await response.json()) as T;
}
