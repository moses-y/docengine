import { useNavigate } from "react-router-dom";
import { useState } from "react";
import * as documentsApi from "../../api/documents";
import { Button } from "../common/Button";

export function NewDocumentButton({ onCreated }: { onCreated: () => void }) {
  const navigate = useNavigate();
  const [creating, setCreating] = useState(false);

  const handleClick = async () => {
    setCreating(true);
    try {
      const doc = await documentsApi.createDocument();
      onCreated();
      navigate(`/d/${doc.id}`);
    } finally {
      setCreating(false);
    }
  };

  return (
    <Button variant="primary" onClick={handleClick} disabled={creating}>
      {creating ? "Creating…" : "New document"}
    </Button>
  );
}
