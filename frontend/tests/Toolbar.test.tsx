/** Toolbar toggles marks (PRD §8 frontend test list). Uses a real TipTap
 * editor instance (not a mock) so the assertion is about the actual
 * `isActive` wiring, not a stand-in for it.
 */
import { EditorContent, useEditor } from "@tiptap/react";
import { useState } from "react";
import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { editorExtensions } from "../src/components/editor/extensions";
import { Toolbar } from "../src/components/editor/Toolbar";

function Harness() {
  const [, forceRerender] = useState(0);
  const editor = useEditor({
    extensions: editorExtensions,
    content: { type: "doc", content: [{ type: "paragraph", content: [{ type: "text", text: "hello" }] }] },
    onTransaction: () => forceRerender((n) => n + 1),
    onSelectionUpdate: () => forceRerender((n) => n + 1),
  });

  return (
    <div>
      <Toolbar editor={editor} disabled={false} />
      <EditorContent editor={editor} />
    </div>
  );
}

describe("Toolbar", () => {
  it("toggles the Bold button's pressed state when clicked", async () => {
    render(<Harness />);

    const boldButton = await screen.findByRole("button", { name: /Bold/i });
    expect(boldButton).toHaveAttribute("aria-pressed", "false");

    // Select all text in the editor so the bold command has something to act on.
    const editable = document.querySelector('[contenteditable="true"]') as HTMLElement;
    const range = document.createRange();
    range.selectNodeContents(editable);
    const selection = window.getSelection();
    selection?.removeAllRanges();
    selection?.addRange(range);
    await act(async () => {
      fireEvent.select(editable);
    });

    await act(async () => {
      fireEvent.click(boldButton);
    });
    expect(boldButton).toHaveAttribute("aria-pressed", "true");

    await act(async () => {
      fireEvent.click(boldButton);
    });
    expect(boldButton).toHaveAttribute("aria-pressed", "false");
  });

  it("disables every button when disabled=true", async () => {
    function DisabledHarness() {
      const editor = useEditor({
        extensions: editorExtensions,
        content: { type: "doc", content: [{ type: "paragraph", content: [] }] },
      });
      return <Toolbar editor={editor} disabled />;
    }

    render(<DisabledHarness />);
    const boldButton = await screen.findByRole("button", { name: /Bold/i });
    expect(boldButton).toBeDisabled();
  });
});
