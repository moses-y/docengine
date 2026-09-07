/** Save indicator transitions (PRD §8 frontend test list) — the four states
 * `useAutosave` can produce, each rendered as the copy PRD §4.2 specifies.
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SaveIndicator } from "../src/components/editor/SaveIndicator";

describe("SaveIndicator", () => {
  it("renders nothing for idle", () => {
    const { container } = render(<SaveIndicator status="idle" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows 'Saving…' while saving", () => {
    render(<SaveIndicator status="saving" />);
    expect(screen.getByRole("status")).toHaveTextContent("Saving…");
  });

  it("shows 'Saved' once the save completes", () => {
    render(<SaveIndicator status="saved" />);
    expect(screen.getByRole("status")).toHaveTextContent("Saved");
  });

  it("shows a retry message on error", () => {
    render(<SaveIndicator status="error" />);
    expect(screen.getByRole("status")).toHaveTextContent("Save failed — retry");
  });

  it("shows the conflict message when the document changed elsewhere", () => {
    render(<SaveIndicator status="conflict" />);
    expect(screen.getByRole("status")).toHaveTextContent(
      "This document changed elsewhere — reload to continue."
    );
  });
});
