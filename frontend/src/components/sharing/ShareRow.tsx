import { Button } from "../common/Button";
import type { ShareGrant } from "../../types";

interface ShareRowProps {
  share: ShareGrant;
  onRevoke: (userId: string) => void;
  revoking: boolean;
}

export function ShareRow({ share, onRevoke, revoking }: ShareRowProps) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "8px 0",
        borderBottom: "1px solid var(--border)",
      }}
    >
      <div>
        <div style={{ fontWeight: 500 }}>{share.display_name}</div>
        <div style={{ fontSize: "12.5px", color: "var(--text-faint)" }}>{share.email}</div>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
        <span className={share.role === "editor" ? "pill pill-editor" : "pill pill-viewer"}>
          {share.role}
        </span>
        <Button
          variant="danger"
          onClick={() => onRevoke(share.user_id)}
          disabled={revoking}
          aria-label={`Revoke access for ${share.email}`}
        >
          Revoke
        </Button>
      </div>
    </div>
  );
}
