/** A labelled toolbar with `aria-pressed` toggles reflecting the marks/
 * blocks active at the cursor (PRD §7). Disabled entirely for viewers —
 * cosmetic, since the real enforcement is server-side, but it keeps the UI
 * honest about what a viewer can do.
 */
import type { Editor } from "@tiptap/react";

interface ToolbarProps {
  editor: Editor | null;
  disabled: boolean;
}

interface ToolButton {
  label: string;
  shortcut: string;
  isActive: (editor: Editor) => boolean;
  run: (editor: Editor) => void;
}

const buttons: ToolButton[] = [
  {
    label: "B",
    shortcut: "Bold (⌘B)",
    isActive: (e) => e.isActive("bold"),
    run: (e) => e.chain().focus().toggleBold().run(),
  },
  {
    label: "I",
    shortcut: "Italic (⌘I)",
    isActive: (e) => e.isActive("italic"),
    run: (e) => e.chain().focus().toggleItalic().run(),
  },
  {
    label: "U",
    shortcut: "Underline (⌘U)",
    isActive: (e) => e.isActive("underline"),
    run: (e) => e.chain().focus().toggleUnderline().run(),
  },
  {
    label: "H1",
    shortcut: "Heading 1 (⌘⌥1)",
    isActive: (e) => e.isActive("heading", { level: 1 }),
    run: (e) => e.chain().focus().toggleHeading({ level: 1 }).run(),
  },
  {
    label: "H2",
    shortcut: "Heading 2 (⌘⌥2)",
    isActive: (e) => e.isActive("heading", { level: 2 }),
    run: (e) => e.chain().focus().toggleHeading({ level: 2 }).run(),
  },
  {
    label: "H3",
    shortcut: "Heading 3 (⌘⌥3)",
    isActive: (e) => e.isActive("heading", { level: 3 }),
    run: (e) => e.chain().focus().toggleHeading({ level: 3 }).run(),
  },
  {
    label: "• List",
    shortcut: "Bulleted list",
    isActive: (e) => e.isActive("bulletList"),
    run: (e) => e.chain().focus().toggleBulletList().run(),
  },
  {
    label: "1. List",
    shortcut: "Numbered list",
    isActive: (e) => e.isActive("orderedList"),
    run: (e) => e.chain().focus().toggleOrderedList().run(),
  },
];

export function Toolbar({ editor, disabled }: ToolbarProps) {
  return (
    <div
      role="toolbar"
      aria-label="Formatting"
      aria-disabled={disabled}
      style={{
        display: "flex",
        gap: "4px",
        padding: "8px 12px",
        borderBottom: "1px solid var(--border)",
        background: "var(--surface)",
        position: "sticky",
        top: 0,
        zIndex: 1,
        flexWrap: "wrap",
      }}
    >
      {buttons.map((btn) => {
        const active = editor ? btn.isActive(editor) : false;
        return (
          <button
            key={btn.label}
            type="button"
            aria-pressed={active}
            aria-label={btn.shortcut}
            title={btn.shortcut}
            disabled={disabled || !editor}
            onClick={() => editor && btn.run(editor)}
            style={{
              minWidth: "34px",
              padding: "6px 8px",
              borderRadius: "4px",
              border: "1px solid transparent",
              background: active ? "var(--accent-soft)" : "transparent",
              color: active ? "var(--accent)" : "var(--text)",
              fontWeight: 600,
              cursor: disabled ? "not-allowed" : "pointer",
              opacity: disabled ? 0.5 : 1,
            }}
          >
            {btn.label}
          </button>
        );
      })}
    </div>
  );
}
