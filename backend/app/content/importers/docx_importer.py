"""DOCX import: `mammoth` converts the document to HTML using its default
style map, then `_HtmlToProseMirror` below walks that HTML into ProseMirror
JSON (PRD §4.3). Images, tables, and footnotes have no whitelisted target
node — they are dropped and named in the returned `dropped` list so the
upload dialog and the document banner can tell the user exactly what did
not survive (PRD §2, §4.3).
"""

from __future__ import annotations

import io
from html.parser import HTMLParser
from typing import Any

import mammoth

from app.content.sanitize import sanitize_document

_HEADING_TAGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 3, "h5": 3, "h6": 3}
_MARK_TAGS = {"strong": "bold", "b": "bold", "em": "italic", "i": "italic", "u": "underline"}
_DROPPABLE_TAGS = {
    "img": "images",
    "table": "tables",
    "figure": "images",
    "footnote": "footnotes",
}


class _HtmlToProseMirror(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.doc: list[dict[str, Any]] = []
        self.dropped: set[str] = set()

        self._block_stack: list[dict[str, Any]] = []
        self._mark_stack: list[str] = []
        self._list_stack: list[dict[str, Any]] = []
        self._skip_depth = 0  # inside a dropped subtree (e.g. <table>)

    # -- helpers -----------------------------------------------------
    def _current_content_target(self) -> list:
        if self._block_stack:
            return self._block_stack[-1]["content"]
        if self._list_stack:
            return self._list_stack[-1]["content"]
        return self.doc

    def _open_block(self, node_type: str, attrs: dict | None = None) -> None:
        node: dict[str, Any] = {"type": node_type, "content": []}
        if attrs:
            node["attrs"] = attrs
        self._current_content_target().append(node)
        self._block_stack.append(node)

    def _close_block(self) -> None:
        if self._block_stack:
            self._block_stack.pop()

    # -- HTMLParser interface ----------------------------------------
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if self._skip_depth > 0:
            self._skip_depth += 1
            return
        if tag in _DROPPABLE_TAGS:
            self.dropped.add(_DROPPABLE_TAGS[tag])
            self._skip_depth = 1
            return

        if tag in _HEADING_TAGS:
            self._open_block("heading", {"level": _HEADING_TAGS[tag]})
        elif tag == "p":
            self._open_block("paragraph")
        elif tag in ("ul", "ol"):
            node = {"type": "bulletList" if tag == "ul" else "orderedList", "content": []}
            self._current_content_target().append(node)
            self._list_stack.append(node)
        elif tag == "li":
            self._open_block_in_list()
        elif tag in _MARK_TAGS:
            self._mark_stack.append(_MARK_TAGS[tag])
        elif tag == "br":
            self._current_content_target().append({"type": "hardBreak"})

    def _open_block_in_list(self) -> None:
        li_node: dict[str, Any] = {"type": "listItem", "content": []}
        parent = self._list_stack[-1]["content"] if self._list_stack else self.doc
        parent.append(li_node)
        # A listItem's content target should be its own paragraph; mammoth
        # emits <li>text</li> without an inner <p>, so open one implicitly.
        para = {"type": "paragraph", "content": []}
        li_node["content"].append(para)
        self._block_stack.append(li_node)
        self._block_stack.append(para)

    def handle_endtag(self, tag: str) -> None:
        if self._skip_depth > 0:
            self._skip_depth -= 1
            return
        if tag in _HEADING_TAGS or tag == "p":
            self._close_block()
        elif tag in ("ul", "ol"):
            if self._list_stack:
                self._list_stack.pop()
        elif tag == "li":
            self._close_block()  # paragraph
            self._close_block()  # listItem
        elif tag in _MARK_TAGS:
            mark = _MARK_TAGS[tag]
            if mark in self._mark_stack:
                self._mark_stack.remove(mark)

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        text = data.replace("\n", " ")
        if not text.strip(" ") and text != " ":
            return
        if not text:
            return
        node: dict[str, Any] = {"type": "text", "text": text}
        if self._mark_stack:
            node["marks"] = [{"type": m} for m in dict.fromkeys(self._mark_stack)]
        self._current_content_target().append(node)


def to_prosemirror(data: bytes) -> tuple[dict[str, Any], list[str]]:
    result = mammoth.convert_to_html(io.BytesIO(data))
    html = result.value

    parser = _HtmlToProseMirror()
    parser.feed(html)
    parser.close()

    content = parser.doc or [{"type": "paragraph", "content": []}]
    doc = sanitize_document({"type": "doc", "content": content})
    dropped = sorted(parser.dropped)
    return doc, dropped
