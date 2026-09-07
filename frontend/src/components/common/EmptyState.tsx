import type { ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div
      style={{
        padding: "48px 24px",
        textAlign: "center",
        color: "var(--text-soft)",
        display: "grid",
        gap: "10px",
        justifyItems: "center",
      }}
    >
      <p style={{ margin: 0, fontWeight: 600, color: "var(--text)" }}>{title}</p>
      {description && <p style={{ margin: 0, maxWidth: "40ch" }}>{description}</p>}
      {action}
    </div>
  );
}
