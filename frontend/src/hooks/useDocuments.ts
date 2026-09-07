/** The document list screen's data — both scopes ("My documents" and
 * "Shared with me" from PRD §7) fetched together so the two-tab UI never
 * shows a stale count while switching tabs.
 */
import { useQuery, useQueryClient } from "@tanstack/react-query";
import * as documentsApi from "../api/documents";

export function useDocuments() {
  const queryClient = useQueryClient();

  const owned = useQuery({
    queryKey: ["documents", "owned"],
    queryFn: () => documentsApi.listDocuments("owned"),
  });

  const shared = useQuery({
    queryKey: ["documents", "shared"],
    queryFn: () => documentsApi.listDocuments("shared"),
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["documents"] });
  };

  return { owned, shared, invalidate };
}
