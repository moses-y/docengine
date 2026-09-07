import { useNavigate } from "react-router-dom";
import { useState } from "react";
import * as documentsApi from "../../api/documents";
import { ApiClientError } from "../../api/client";
import { Button } from "../common/Button";

export function NewDocumentButton({ onCreated }: { onCreated: () => void }) {
  const navigate = useNavigate();
  const [creating, setCreating] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const handleClick = async () => {
    setCreating(true);
    setError(null);
    try {
      const doc = await documentsApi.createDocument();
      onCreated();
      navigate(`/d/${doc.id}`);
    } catch (err) {
      // Without this the button silently did nothing on failure, which is
      // indistinguishable from a dead click.
      setError(err instanceof ApiClientError ? err.message : "Could not create document");
    } finally {
      setCreating(false);
    }
  };

  return (
    <>
      <Button variant="primary" onClick={handleClick} disabled={creating}>
        {creating ? "Creating…" : "New document"}
      </Button>
      {error && <span role="alert">{error}</span>}
    </>
  );
}
