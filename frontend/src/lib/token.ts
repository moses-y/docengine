/** Bearer-token storage for the API client.
 *
 * The API sets an httpOnly `access_token` cookie on login and also accepts a
 * `Bearer` Authorization header. The cookie alone is enough when the frontend
 * and API share an origin (locally, nginx proxies `/api` — see
 * `frontend/nginx.conf`), but not when they are deployed as separate services
 * on separate hostnames: browsers treat that as cross-site and withhold a
 * `SameSite=Lax` cookie, so every authenticated request fails while login
 * itself appears to succeed.
 *
 * Keeping the token here and sending it explicitly makes auth work in both
 * topologies without depending on cross-site cookie behavior, which browsers
 * are progressively restricting anyway. The tradeoff is that the token is
 * readable by JavaScript, so it is exposed to XSS in a way an httpOnly cookie
 * is not — acceptable here because the editor already sanitizes rich-text
 * content server-side (PRD §10), and the cookie remains in place for clients
 * that can use it.
 */
const STORAGE_KEY = "docengine.access_token";

let cached: string | null = null;

export function getToken(): string | null {
  if (cached !== null) return cached;
  try {
    cached = window.localStorage.getItem(STORAGE_KEY);
  } catch {
    // Private mode or blocked storage: fall back to the cookie path.
    cached = null;
  }
  return cached;
}

export function setToken(token: string): void {
  cached = token;
  try {
    window.localStorage.setItem(STORAGE_KEY, token);
  } catch {
    // Non-fatal: the in-memory copy carries this tab's session.
  }
}

export function clearToken(): void {
  cached = null;
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Nothing to do.
  }
}
