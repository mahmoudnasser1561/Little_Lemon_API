/**
 * The one place that knows how to talk to the Django API: base URL, auth header,
 * JSON handling, and error shape. Every resource module (menu.ts, categories.ts, ...)
 * goes through `request()` rather than calling fetch directly.
 *
 * Requests are relative (`/api/...`) by default, not absolute - in dev, Vite's server
 * proxy forwards them to the real backend (see vite.config.ts), same-origin, no CORS
 * needed (CORS is explicitly not set up on the API - see API_WORK_PLAN.md). In
 * production behind an ingress, the same relative-path pattern holds: the ingress
 * routes /api to the backend service, same-origin from the browser's point of view.
 * VITE_API_BASE_URL overrides this for the rare case of pointing at a deployed API
 * with no proxy in front of it.
 */

const TOKEN_KEY = 'll_token';

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null; // private browsing / storage blocked - fail to "signed out", never throw
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // nothing to do if storage is unavailable - the app just won't stay logged in
  }
}

export function clearToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // ignore
  }
}

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, body: unknown) {
    super(`API error ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}

/** Called on a 401 so the app can react (e.g. clear stale state and redirect to
 * login). Set once by the app shell; a no-op until then. */
let onUnauthorized: () => void = () => {};
export function setUnauthorizedHandler(handler: () => void): void {
  onUnauthorized = handler;
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers);
  headers.set('Accept', 'application/json');
  if (init.body && !(init.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  if (token) {
    headers.set('Authorization', `Token ${token}`);
  }

  const response = await fetch(`${BASE_URL}${path}`, { ...init, headers });

  if (response.status === 401) {
    onUnauthorized();
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const isJson = response.headers.get('Content-Type')?.includes('application/json');
  const body = isJson ? await response.json() : await response.text();

  if (!response.ok) {
    throw new ApiError(response.status, body);
  }

  return body as T;
}
