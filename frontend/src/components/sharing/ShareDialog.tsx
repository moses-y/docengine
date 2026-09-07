/** Grant/revoke access to a document (PRD §4.4). The owner row is shown
 * pinned and un-removable — ownership isn't a share grant at all (it lives
 * on `documents.owner_id`), so there's nothing here to revoke for it.
 */
import { useEffect, useState } from "react";
import * as sharesApi from "../../api/shares";
import { ApiClientError } from "../../api/client";
import { Button } from "../common/Button";
import { ErrorBanner } from "../common/ErrorBanner";
import { ShareRow } from "./ShareRow";
import type { ShareGrant, ShareRole } from "../../types";

interface ShareDialogProps {
  documentId: string;
  ownerEmail: string;
  onClose: () => void;
}

export function ShareDialog({ documentId, ownerEmail, onClose }: ShareDialogProps) {
  const [shares, setShares] = useState<ShareGrant[]>([]);
  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<ShareRole>("viewer");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [revokingId, setRevokingId] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      setShares(await sharesApi.listShares(documentId));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentId]);

  const handleGrant = async () => {
    setError(null);
    if (!email.trim()) return;
    setSubmitting(true);
    try {
      await sharesApi.grantShare(documentId, email.trim(), role);
      setEmail("");
      await load();
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message : "Could not grant access");
    } finally {
      setSubmitting(false);
    }
  };

  const handleRevoke = async (userId: string) => {
    setRevokingId(userId);
    try {
      await sharesApi.revokeShare(documentId, userId);
      await load();
    } finally {
      setRevokingId(null);
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Share document"
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.35)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 10,
      }}
    >
      <div className="card" style={{ width: "440px", padding: "20px", display: "grid", gap: "14px" }}>
        <h2 style={{ margin: 0, fontSize: "17px" }}>Share document</h2>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            padding: "8px 0",
            borderBottom: "1px solid var(--border)",
          }}
        >
          <div>
            <div style={{ fontWeight: 500 }}>{ownerEmail}</div>
            <div style={{ fontSize: "12.5px", color: "var(--text-faint)" }}>Owner</div>
          </div>
          <span className="pill pill-owner">owner</span>
        </div>

        {loading ? (
          <p style={{ color: "var(--text-faint)", margin: 0 }}>Loading access list…</p>
        ) : (
          shares.map((share) => (
            <ShareRow
              key={share.id}
              share={share}
              onRevoke={handleRevoke}
              revoking={revokingId === share.user_id}
            />
          ))
        )}

        {error && <ErrorBanner message={error} />}

        <div style={{ display: "flex", gap: "8px" }}>
          <input
            type="email"
            placeholder="Email address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{ flex: 1 }}
          />
          <select value={role} onChange={(e) => setRole(e.target.value as ShareRole)}>
            <option value="viewer">Viewer</option>
            <option value="editor">Editor</option>
          </select>
          <Button variant="primary" onClick={handleGrant} disabled={submitting}>
            Grant
          </Button>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <Button onClick={onClose}>Done</Button>
        </div>
      </div>
    </div>
  );
}
