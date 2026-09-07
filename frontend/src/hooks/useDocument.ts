import { useQuery } from "@tanstack/react-query";
import * as documentsApi from "../api/documents";

export function useDocument(documentId: string | undefined) {
  return useQuery({
    queryKey: ["document", documentId],
    queryFn: () => documentsApi.getDocument(documentId as string),
    enabled: Boolean(documentId),
  });
}
