/** Shared TypeScript types mirroring the backend's Pydantic schemas
 * (see `backend/app/schemas`). Kept hand-written and minimal rather than
 * codegen'd, since the surface area is small and stable.
 */

export type Role = "owner" | "editor" | "viewer";
export type ShareRole = "viewer" | "editor";

export interface User {
  id: string;
  email: string;
  display_name: string;
}

export interface DocumentSummary {
  id: string;
  title: string;
  owner_email: string;
  my_role: Role;
  updated_at: string;
}

/** A ProseMirror document node — the exact shape TipTap reads/writes and
 * the exact shape `app.content.sanitize` whitelists on the server. */
export interface ProseMirrorDoc {
  type: "doc";
  content?: unknown[];
}

export interface DocumentDetail {
  id: string;
  title: string;
  content: ProseMirrorDoc;
  version: number;
  owner_id: string;
  owner_email: string;
  my_role: Role;
  created_at: string;
  updated_at: string;
}

export interface ImportResult {
  document: DocumentDetail;
  dropped_features: string[];
}

export interface ShareGrant {
  id: string;
  user_id: string;
  email: string;
  display_name: string;
  role: ShareRole;
  granted_by: string;
  created_at: string;
}

export interface Attachment {
  id: string;
  document_id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  created_at: string;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    field: string | null;
  };
}
