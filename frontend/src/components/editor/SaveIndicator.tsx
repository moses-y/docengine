/** Renders the four autosave states from PRD §4.2 as plain text — the
 * lowest-drama UI possible for something that runs constantly in a
 * peripheral part of the screen.
 */
import type { SaveStatus } from "../../hooks/useAutosave";

const COPY: Record<SaveStatus, string> = {
  idle: "",
  saving: "Saving…",
  saved: "Saved",
  error: "Save failed — retry",
  conflict: "This document changed elsewhere — reload to continue.",
};

export function SaveIndicator({ status }: { status: SaveStatus }) {
  if (status === "idle") return null;

  const color =
    status === "error" || status === "conflict" ? "var(--danger)" : "var(--text-faint)";

  return (
    <span role="status" aria-live="polite" style={{ fontSize: "13px", color }}>
      {COPY[status]}
    </span>
  );
}
