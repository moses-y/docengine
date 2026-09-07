import "@testing-library/jest-dom/vitest";

/** jsdom doesn't implement layout, so Range/Element rect APIs are missing —
 * ProseMirror (which TipTap sits on) calls them on every selection change to
 * scroll the cursor into view. These no-op polyfills are the standard
 * workaround for testing ProseMirror-based editors under jsdom. */
if (typeof document !== "undefined") {
  const rectStub = () => ({
    top: 0,
    left: 0,
    bottom: 0,
    right: 0,
    width: 0,
    height: 0,
    x: 0,
    y: 0,
    toJSON() {
      return this;
    },
  });

  Range.prototype.getClientRects = () => [] as unknown as DOMRectList;
  Range.prototype.getBoundingClientRect = rectStub as unknown as () => DOMRect;
  Element.prototype.getBoundingClientRect = rectStub;
}
