import { apiFetch } from "./client";
import { clearToken, setToken } from "../lib/token";
import type { User } from "../types";

interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const result = await apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    body: { email, password },
  });
  setToken(result.access_token);
  return result;
}

export async function register(
  email: string,
  displayName: string,
  password: string
): Promise<TokenResponse> {
  const result = await apiFetch<TokenResponse>("/auth/register", {
    method: "POST",
    body: { email, display_name: displayName, password },
  });
  setToken(result.access_token);
  return result;
}

export async function logout(): Promise<void> {
  try {
    await apiFetch<void>("/auth/logout", { method: "POST" });
  } finally {
    // Drop the local token even if the request failed, so the UI cannot be
    // left holding a credential it just tried to discard.
    clearToken();
  }
}

export function me(): Promise<User> {
  return apiFetch<User>("/auth/me");
}
