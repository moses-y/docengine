import { EmptyState } from "../common/EmptyState";
import { Spinner } from "../common/Spinner";
import { DocumentRow } from "./DocumentRow";
import type { DocumentSummary } from "../../types";

interface DocumentListProps {
  documents: DocumentSummary[] | undefined;
  isLoading: boolean;
  emptyTitle: string;
  emptyDescription: string;
}

export function DocumentList({
  documents,
  isLoading,
  emptyTitle,
  emptyDescription,
}: DocumentListProps) {
  if (isLoading) return <Spinner label="Loading documents" />;

  if (!documents || documents.length === 0) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  }

  return (
    <div className="card" style={{ overflow: "hidden" }}>
      {documents.map((doc) => (
        <DocumentRow key={doc.id} doc={doc} />
      ))}
    </div>
  );
}
