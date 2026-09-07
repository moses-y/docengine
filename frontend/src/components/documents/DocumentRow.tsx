import { Link } from "react-router-dom";
import type { DocumentSummary } from "../../types";

const pillClass: Record<DocumentSummary["my_role"], string> = {
  owner: "pill pill-owner",
  editor: "pill pill-editor",
  viewer: "pill pill-viewer",
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function DocumentRow({ doc }: { doc: DocumentSummary }) {
  return (
    <Link
      to={`/d/${doc.id}`}
      style={{
        display: "grid",
        gridTemplateColumns: "1fr auto auto",
        gap: "16px",
        alignItems: "center",
        padding: "14px 18px",
        borderBottom: "1px solid var(--border)",
        textDecoration: "none",
        color: "var(--text)",
      }}
    >
      <div style={{ minWidth: 0 }}>
        <div style={{ fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
          {doc.title}
        </div>
        <div style={{ fontSize: "12.5px", color: "var(--text-faint)" }}>
          {doc.my_role === "owner" ? "You" : doc.owner_email}
        </div>
      </div>
      <span style={{ fontSize: "12.5px", color: "var(--text-faint)" }}>
        {formatDate(doc.updated_at)}
      </span>
      <span className={pillClass[doc.my_role]}>{doc.my_role}</span>
    </Link>
  );
}
