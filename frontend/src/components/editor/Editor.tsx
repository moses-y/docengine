/** The rich-text surface itself. Content flows in one direction on mount
 * (`content` is only used to *initialize* TipTap — see the `key` prop the
 * caller passes so React remounts on document switch) and changes flow out
 * via `onUpdate`; the caller (DocumentEditorPage) owns autosave scheduling
 * and the base_version bookkeeping described in PRD §4.2.
 */
import { EditorContent, useEditor } from "@tiptap/react";
import { useEffect, useState } from "react";
import { editorExtensions } from "./extensions";
import { Toolbar } from "./Toolbar";
import type { ProseMirrorDoc } from "../../types";

interface EditorProps {
  content: ProseMirrorDoc;
  editable: boolean;
  onUpdate: (doc: ProseMirrorDoc) => void;
  onBlur: () => void;
}

export function Editor({ content, editable, onUpdate, onBlur }: EditorProps) {
  // TipTap's editor instance is stable across transactions; without a tick
  // that changes on every one, the Toolbar's aria-pressed states would only
  // catch up whenever some unrelated re-render happened to fire.
  const [, forceRerender] = useState(0);

  const editor = useEditor({
    extensions: editorExtensions,
    content: content as unknown as Record<string, unknown>,
    editable,
    onUpdate: ({ editor: e }) => {
      onUpdate(e.getJSON() as ProseMirrorDoc);
    },
    onBlur: () => onBlur(),
    onTransaction: () => forceRerender((n) => n + 1),
    onSelectionUpdate: () => forceRerender((n) => n + 1),
    editorProps: {
      attributes: {
        "aria-label": "Document content",
        style: "padding: 24px 32px; min-height: 100%; outline: none;",
      },
    },
  });

  useEffect(() => {
    editor?.setEditable(editable);
  }, [editable, editor]);

  return (
    <div style={{ display: "flex", flexDirection: "column", flex: 1, minHeight: 0 }}>
      <Toolbar editor={editor} disabled={!editable} />
      <div style={{ flex: 1, overflowY: "auto" }}>
        <EditorContent editor={editor} />
      </div>
    </div>
  );
}
