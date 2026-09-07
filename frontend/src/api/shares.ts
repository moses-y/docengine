import { apiFetch } from "./client";
import type { ShareGrant, ShareRole } from "../types";

export function listShares(documentId: string): Promise<ShareGrant[]> {
  return apiFetch<ShareGrant[]>(`/documents/${documentId}/shares`);
}

export function grantShare(
  documentId: string,
  email: string,
  role: ShareRole
): Promise<ShareGrant> {
  return apiFetch<ShareGrant>(`/documents/${documentId}/shares`, {
    method: "POST",
    body: { email, role },
  });
}

export function revokeShare(documentId: string, userId: string): Promise<void> {
  return apiFetch<void>(`/documents/${documentId}/shares/${userId}`, { method: "DELETE" });
}
