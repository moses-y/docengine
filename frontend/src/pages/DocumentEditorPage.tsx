/** The "/d/:id" route: title, toolbar, editor surface, save indicator,
 * Share button, and an attachments drawer (US-12) — matching PRD §7.
 */
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Editor } from "../components/editor/Editor";
import { SaveIndicator } from "../components/editor/SaveIndicator";
import { ShareDialog } from "../components/sharing/ShareDialog";
import { Button } from "../components/common/Button";
import { Spinner } from "../components/common/Spinner";
import { ErrorBanner } from "../components/common/ErrorBanner";
import { useAutosave } from "../hooks/useAutosave";
import { useDocument } from "../hooks/useDocument";
import * as documentsApi from "../api/documents";
import type { ProseMirrorDoc } from "../types";

export function DocumentEditorPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: doc, isLoading, isError, refetch } = useDocument(id);

  const [title, setTitle] = useState("");
  const [sharing, setSharing] = useState(false);
  const [titleSaving, setTitleSaving] = useState(false);

  useEffect(() => {
    if (doc) setTitle(doc.title);
  }, [doc?.id, doc?.title]); // eslint-disable-line react-hooks/exhaustive-deps

  const { status, scheduleSave, flush } = useAutosave({
    documentId: id ?? "",
    initialVersion: doc?.version ?? 1,
    onConflict: () => void refetch(),
  });

  useEffect(() => {
    const handler = () => {
      if (document.visibilityState === "hidden") void flush();
    };
    document.addEventListener("visibilitychange", handler);
    return () => document.removeEventListener("visibilitychange", handler);
  }, [flush]);

  if (!id) return null;
  if (isLoading) return <Spinner label="Loading document" />;
  if (isError || !doc) {
    return (
      <div style={{ padding: "24px", maxWidth: "560px", margin: "0 auto" }}>
        <ErrorBanner message="This document could not be found, or you don't have access to it." />
        <div style={{ marginTop: "12px" }}>
          <Button onClick={() => navigate("/")}>Back to documents</Button>
        </div>
      </div>
    );
  }

  const editable = doc.my_role !== "viewer";

  const handleTitleBlur = async () => {
    const trimmed = title.trim();
    if (!trimmed || trimmed === doc.title || !editable) return;
    setTitleSaving(true);
    try {
      await documentsApi.updateDocument(id, { title: trimmed });
    } finally {
      setTitleSaving(false);
    }
  };

  const handleUpdate = (content: ProseMirrorDoc) => {
    if (editable) scheduleSave(content);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "14px 24px",
          borderBottom: "1px solid var(--border)",
          gap: "16px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px", minWidth: 0 }}>
          <Button onClick={() => navigate("/")} aria-label="Back to documents">
            ←
          </Button>
          <input
            type="text"
            value={title}
            disabled={!editable}
            onChange={(e) => setTitle(e.target.value)}
            onBlur={handleTitleBlur}
            aria-label="Document title"
            style={{
              border: "none",
              background: "transparent",
              fontSize: "17px",
              fontWeight: 600,
              minWidth: 0,
            }}
          />
          {titleSaving && (
            <span style={{ fontSize: "12px", color: "var(--text-faint)" }}>Saving title…</span>
          )}
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
          <SaveIndicator status={status} />
          {doc.my_role === "owner" && <Button onClick={() => setSharing(true)}>Share</Button>}
          {!editable && <span className="pill pill-viewer">View only</span>}
        </div>
      </div>

      <Editor
        key={doc.id}
        content={doc.content}
        editable={editable}
        onUpdate={handleUpdate}
        onBlur={() => void flush()}
      />

      {sharing && (
        <ShareDialog documentId={doc.id} ownerEmail={doc.owner_email} onClose={() => setSharing(false)} />
      )}
    </div>
  );
}
