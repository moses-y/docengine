import type { ReactNode } from "react";
import { Header } from "./Header";
import type { User } from "../../types";

interface AppShellProps {
  user: User;
  onLogout: () => void;
  children: ReactNode;
}

export function AppShell({ user, onLogout, children }: AppShellProps) {
  return (
    <div style={{ minHeight: "100%", display: "flex", flexDirection: "column" }}>
      <Header user={user} onLogout={onLogout} />
      <main style={{ flex: 1, display: "flex", flexDirection: "column", minHeight: 0 }}>
        {children}
      </main>
    </div>
  );
}
