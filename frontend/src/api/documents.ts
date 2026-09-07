import { apiFetch } from "./client";
import type { DocumentDetail, DocumentSummary, ImportResult, ProseMirrorDoc } from "../types";

export type DocumentScope = "owned" | "shared" | "all";

export function listDocuments(scope: DocumentScope = "all"): Promise<DocumentSummary[]> {
  return apiFetch<DocumentSummary[]>(`/documents?scope=${scope}`);
}

export function createDocument(title?: string): Promise<DocumentDetail> {
  return apiFetch<DocumentDetail>("/documents", { method: "POST", body: { title } });
}

export function getDocument(id: string): Promise<DocumentDetail> {
  return apiFetch<DocumentDetail>(`/documents/${id}`);
}

export interface UpdateDocumentBody {
  title?: string;
  content?: ProseMirrorDoc;
  base_version?: number;
}

export function updateDocument(id: string, body: UpdateDocumentBody): Promise<DocumentDetail> {
  return apiFetch<DocumentDetail>(`/documents/${id}`, { method: "PATCH", body });
}

export function deleteDocument(id: string): Promise<void> {
  return apiFetch<void>(`/documents/${id}`, { method: "DELETE" });
}

export function importDocument(file: File): Promise<ImportResult> {
  const form = new FormData();
  form.append("file", file);
  return apiFetch<ImportResult>("/documents/import", {
    method: "POST",
    body: form,
    isFormData: true,
  });
}
