import { apiFetch } from "./client";
import type { User } from "../types";

interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export function login(email: string, password: string): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/login", { method: "POST", body: { email, password } });
}

export function register(
  email: string,
  displayName: string,
  password: string
): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/auth/register", {
    method: "POST",
    body: { email, display_name: displayName, password },
  });
}

export function logout(): Promise<void> {
  return apiFetch<void>("/auth/logout", { method: "POST" });
}

export function me(): Promise<User> {
  return apiFetch<User>("/auth/me");
}
