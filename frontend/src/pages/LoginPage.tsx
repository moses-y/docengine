/** Email/password sign-in with seeded-account hint chips (PRD §7) so a
 * reviewer can exercise sharing without reading the README first.
 */
import { useState } from "react";
import { Button } from "../components/common/Button";
import { ErrorBanner } from "../components/common/ErrorBanner";
import { SEEDED_ACCOUNTS, SEEDED_PASSWORD } from "../lib/constants";

interface LoginPageProps {
  onLogin: (email: string, password: string) => Promise<boolean>;
  pending: boolean;
  error: string | null;
}

export function LoginPage({ onLogin, pending, error }: LoginPageProps) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    void onLogin(email, password);
  };

  return (
    <div
      style={{
        minHeight: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
      }}
    >
      <form
        onSubmit={handleSubmit}
        className="card"
        style={{ width: "360px", padding: "28px", display: "grid", gap: "16px" }}
      >
        <div>
          <h1 style={{ margin: "0 0 4px", fontSize: "20px" }}>DocEngine</h1>
          <p style={{ margin: 0, color: "var(--text-soft)", fontSize: "13.5px" }}>
            Sign in to continue
          </p>
        </div>

        {error && <ErrorBanner message={error} />}

        <label style={{ display: "grid", gap: "6px", fontSize: "13px" }}>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />
        </label>
        <label style={{ display: "grid", gap: "6px", fontSize: "13px" }}>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>

        <Button type="submit" variant="primary" disabled={pending}>
          {pending ? "Signing in…" : "Sign in"}
        </Button>

        <div style={{ borderTop: "1px solid var(--border)", paddingTop: "12px" }}>
          <p style={{ margin: "0 0 8px", fontSize: "12px", color: "var(--text-faint)" }}>
            Seeded demo accounts (password: {SEEDED_PASSWORD})
          </p>
          <div style={{ display: "grid", gap: "4px" }}>
            {SEEDED_ACCOUNTS.map((acc) => (
              <button
                key={acc.email}
                type="button"
                onClick={() => {
                  setEmail(acc.email);
                  setPassword(SEEDED_PASSWORD);
                }}
                style={{
                  textAlign: "left",
                  background: "none",
                  border: "none",
                  color: "var(--accent)",
                  cursor: "pointer",
                  fontSize: "12.5px",
                  padding: "2px 0",
                }}
              >
                {acc.email} — {acc.label}
              </button>
            ))}
          </div>
        </div>
      </form>
    </div>
  );
}
