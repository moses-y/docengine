import { Link } from "react-router-dom";
import { Button } from "../common/Button";
import type { User } from "../../types";

interface HeaderProps {
  user: User;
  onLogout: () => void;
}

export function Header({ user, onLogout }: HeaderProps) {
  return (
    <header
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 24px",
        borderBottom: "1px solid var(--border)",
        background: "var(--surface)",
      }}
    >
      <Link
        to="/"
        style={{ fontWeight: 700, fontSize: "16px", color: "var(--text)", textDecoration: "none" }}
      >
        DocEngine
      </Link>
      <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
        <span style={{ color: "var(--text-soft)", fontSize: "13.5px" }}>
          {user.display_name} <span style={{ color: "var(--text-faint)" }}>({user.email})</span>
        </span>
        <Button onClick={onLogout}>Sign out</Button>
      </div>
    </header>
  );
}
