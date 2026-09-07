/** Auth state lives in React state, not a global store — the app is small
 * enough that lifting it to `AppShell` and passing it down is simpler than
 * wiring a context provider (see `App.tsx`). This hook just wraps the API
 * calls and exposes loading/error state for the login screen.
 */
import { useCallback, useState } from "react";
import * as authApi from "../api/auth";
import { ApiClientError } from "../api/client";
import type { User } from "../types";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [checking, setChecking] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  const checkSession = useCallback(async () => {
    setChecking(true);
    try {
      const current = await authApi.me();
      setUser(current);
    } catch {
      setUser(null);
    } finally {
      setChecking(false);
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setPending(true);
    setError(null);
    try {
      const { user: loggedIn } = await authApi.login(email, password);
      setUser(loggedIn);
      return true;
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Could not sign in");
      return false;
    } finally {
      setPending(false);
    }
  }, []);

  const logout = useCallback(async () => {
    await authApi.logout();
    setUser(null);
  }, []);

  return { user, checking, pending, error, login, logout, checkSession };
}
