/** Debounced autosave with the optimistic-concurrency contract from PRD
 * §4.2: every save carries `base_version`, and a 409 means someone else's
 * write landed first — the caller decides what to do (`onConflict`), this
 * hook only tracks the save's own state machine
 * (`idle -> saving -> saved -> idle`, or `-> error` / `-> conflict`).
 *
 * The debounce is 800ms after the last keystroke (`AUTOSAVE_DEBOUNCE_MS`),
 * plus an explicit `flush()` for blur / visibilitychange, matching PRD §4.2.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import * as documentsApi from "../api/documents";
import { ApiClientError } from "../api/client";
import { AUTOSAVE_DEBOUNCE_MS } from "../lib/constants";
import type { ProseMirrorDoc } from "../types";

export type SaveStatus = "idle" | "saving" | "saved" | "error" | "conflict";

interface UseAutosaveOptions {
  documentId: string;
  initialVersion: number;
  onSaved?: (version: number) => void;
  onConflict?: () => void;
}

export function useAutosave({ documentId, initialVersion, onSaved, onConflict }: UseAutosaveOptions) {
  const [status, setStatus] = useState<SaveStatus>("idle");
  const versionRef = useRef(initialVersion);
  const pendingRef = useRef<ProseMirrorDoc | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const savingRef = useRef(false);

  useEffect(() => {
    versionRef.current = initialVersion;
  }, [initialVersion]);

  const flush = useCallback(async () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    if (savingRef.current || pendingRef.current === null) return;

    const content = pendingRef.current;
    pendingRef.current = null;
    savingRef.current = true;
    setStatus("saving");

    try {
      const updated = await documentsApi.updateDocument(documentId, {
        content,
        base_version: versionRef.current,
      });
      versionRef.current = updated.version;
      setStatus("saved");
      onSaved?.(updated.version);
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 409) {
        setStatus("conflict");
        onConflict?.();
      } else {
        setStatus("error");
      }
    } finally {
      savingRef.current = false;
    }
  }, [documentId, onConflict, onSaved]);

  const scheduleSave = useCallback(
    (content: ProseMirrorDoc) => {
      pendingRef.current = content;
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        void flush();
      }, AUTOSAVE_DEBOUNCE_MS);
    },
    [flush]
  );

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  return { status, scheduleSave, flush };
}
