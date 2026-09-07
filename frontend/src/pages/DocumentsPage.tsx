/** The "/" route: two tabs — My documents / Shared with me — matching
 * US-9 (a visible distinction between owned and shared documents).
 */
import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { DocumentList } from "../components/documents/DocumentList";
import { ImportDialog } from "../components/documents/ImportDialog";
import { NewDocumentButton } from "../components/documents/NewDocumentButton";
import { Button } from "../components/common/Button";
import { useDocuments } from "../hooks/useDocuments";

type Tab = "owned" | "shared";

export function DocumentsPage() {
  const navigate = useNavigate();
  const { owned, shared, invalidate } = useDocuments();
  const [tab, setTab] = useState<Tab>("owned");
  const [importing, setImporting] = useState(false);

  const activeQuery = tab === "owned" ? owned : shared;

  return (
    <div style={{ maxWidth: "760px", margin: "0 auto", width: "100%", padding: "28px 20px" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "20px",
          gap: "12px",
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", gap: "4px" }}>
          <TabButton active={tab === "owned"} onClick={() => setTab("owned")}>
            My documents{owned.data ? ` (${owned.data.length})` : ""}
          </TabButton>
          <TabButton active={tab === "shared"} onClick={() => setTab("shared")}>
            Shared with me{shared.data ? ` (${shared.data.length})` : ""}
          </TabButton>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          <Button onClick={() => setImporting(true)}>Import file</Button>
          <NewDocumentButton onCreated={invalidate} />
        </div>
      </div>

      <DocumentList
        documents={activeQuery.data}
        isLoading={activeQuery.isLoading}
        emptyTitle={tab === "owned" ? "No documents yet" : "Nothing has been shared with you yet"}
        emptyDescription={
          tab === "owned"
            ? "Create a new document or import a file to get started."
            : "When someone shares a document with you, it will show up here."
        }
      />

      {importing && (
        <ImportDialog
          onClose={() => setImporting(false)}
          onImported={(id) => {
            setImporting(false);
            invalidate();
            navigate(`/d/${id}`);
          }}
        />
      )}
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        padding: "8px 14px",
        borderRadius: "6px",
        border: "1px solid transparent",
        background: active ? "var(--surface)" : "transparent",
        boxShadow: active ? "var(--shadow)" : "none",
        fontWeight: 600,
        color: active ? "var(--text)" : "var(--text-soft)",
        cursor: "pointer",
      }}
    >
      {children}
    </button>
  );
}
