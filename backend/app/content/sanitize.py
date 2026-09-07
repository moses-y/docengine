"""The server-side ProseMirror node/mark whitelist — the actual XSS boundary
for document content (PRD §4.2). Client-side editor restrictions are a UX
nicety; this function is what makes a malicious or buggy client harmless.

Anything not on the whitelist is dropped, not escaped — there is no notion
of "safe HTML" here because the stored content is never raw HTML.
"""

from __future__ import annotations

from typing import Any

_ALLOWED_NODES = {
    "doc",
    "paragraph",
    "heading",
    "bulletList",
    "orderedList",
    "listItem",
    "text",
    "hardBreak",
}
_ALLOWED_MARKS = {"bold", "italic", "underline"}
_ALLOWED_HEADING_LEVELS = {1, 2, 3}

_EMPTY_DOC: dict[str, Any] = {"type": "doc", "content": [{"type": "paragraph", "content": []}]}


def _sanitize_mark(mark: Any) -> dict | None:
    if not isinstance(mark, dict):
        return None
    mark_type = mark.get("type")
    if mark_type not in _ALLOWED_MARKS:
        return None
    return {"type": mark_type}


def _sanitize_node(node: Any) -> dict | None:
    if not isinstance(node, dict):
        return None
    node_type = node.get("type")
    if node_type not in _ALLOWED_NODES:
        return None

    result: dict[str, Any] = {"type": node_type}

    if node_type == "text":
        text = node.get("text")
        if not isinstance(text, str) or text == "":
            return None
        result["text"] = text
        marks = [m for m in (_sanitize_mark(m) for m in node.get("marks", []) or []) if m]
        if marks:
            result["marks"] = marks
        return result

    if node_type == "heading":
        level = (node.get("attrs") or {}).get("level")
        if level not in _ALLOWED_HEADING_LEVELS:
            level = 1
        result["attrs"] = {"level": level}

    children = node.get("content")
    if isinstance(children, list):
        sanitized_children = [c for c in (_sanitize_node(child) for child in children) if c]
        if sanitized_children:
            result["content"] = sanitized_children

    return result


def sanitize_document(raw: Any) -> dict[str, Any]:
    """Sanitize a full ProseMirror document. Falls back to an empty document
    if the input is not a well-formed `doc` node after filtering, rather than
    ever raising — malformed content should never be able to break a save."""
    if not isinstance(raw, dict) or raw.get("type") != "doc":
        return dict(_EMPTY_DOC)

    children = raw.get("content")
    sanitized_children = []
    if isinstance(children, list):
        sanitized_children = [c for c in (_sanitize_node(child) for child in children) if c]

    if not sanitized_children:
        return dict(_EMPTY_DOC)

    return {"type": "doc", "content": sanitized_children}
