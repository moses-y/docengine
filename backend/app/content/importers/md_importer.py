"""Markdown import via `markdown-it-py`'s token stream, walked directly into
ProseMirror JSON (PRD §4.3) — no intermediate HTML, so there is nothing for
`app.content.sanitize` to do except double-check the result.

Preserves: headings (levels 1-3, clamped), bold, italic, bulleted and
numbered lists. Everything else markdown-it can produce (tables, code
fences, images, blockquotes, links) has no whitelisted target node and is
flattened to plain text, matching the "text formatting only" non-goal
(PRD §2).
"""

from __future__ import annotations

from typing import Any

from markdown_it import MarkdownIt
from markdown_it.token import Token

from app.content.sanitize import sanitize_document

_md = MarkdownIt("commonmark")


def _inline_to_text_nodes(children: list[Token]) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    mark_stack: list[str] = []

    for tok in children or []:
        if tok.type == "text":
            if tok.content:
                node: dict[str, Any] = {"type": "text", "text": tok.content}
                if mark_stack:
                    node["marks"] = [{"type": m} for m in dict.fromkeys(mark_stack)]
                nodes.append(node)
        elif tok.type in ("softbreak", "hardbreak"):
            nodes.append({"type": "hardBreak"})
        elif tok.type == "strong_open":
            mark_stack.append("bold")
        elif tok.type == "strong_close":
            if "bold" in mark_stack:
                mark_stack.remove("bold")
        elif tok.type == "em_open":
            mark_stack.append("italic")
        elif tok.type == "em_close":
            if "italic" in mark_stack:
                mark_stack.remove("italic")
        elif tok.type == "code_inline" and tok.content:
            nodes.append({"type": "text", "text": tok.content})
        # links, images, and anything else contribute no node of their own;
        # their inline text (if any) already came through as "text" tokens.

    return nodes


def _list_item_to_node(item_tokens: list[Token]) -> dict[str, Any]:
    """`item_tokens` spans one list_item_open .. list_item_close block."""
    content: list[dict[str, Any]] = []
    i = 0
    while i < len(item_tokens):
        tok = item_tokens[i]
        if tok.type == "paragraph_open":
            inline = item_tokens[i + 1]
            content.append({"type": "paragraph", "content": _inline_to_text_nodes(inline.children)})
            i += 3  # paragraph_open, inline, paragraph_close
            continue
        if tok.type in ("bullet_list_open", "ordered_list_open"):
            nested, consumed = _collect_list(item_tokens, i)
            content.append(nested)
            i += consumed
            continue
        i += 1
    if not content:
        content = [{"type": "paragraph", "content": []}]
    return {"type": "listItem", "content": content}


def _collect_list(tokens: list[Token], start: int) -> tuple[dict[str, Any], int]:
    """Consume a `bullet_list`/`ordered_list` block starting at `start`
    (inclusive of the `_open` token) and return (node, tokens_consumed)."""
    open_tok = tokens[start]
    is_bullet = open_tok.type == "bullet_list_open"
    node_type = "bulletList" if is_bullet else "orderedList"
    close_type = "bullet_list_close" if is_bullet else "ordered_list_close"

    depth = 1
    i = start + 1
    items: list[dict[str, Any]] = []
    item_start: int | None = None
    item_depth = 0

    while i < len(tokens) and depth > 0:
        tok = tokens[i]
        if tok.type == "list_item_open":
            if item_depth == 0:
                item_start = i + 1
            item_depth += 1
        elif tok.type == "list_item_close":
            item_depth -= 1
            if item_depth == 0 and item_start is not None:
                items.append(_list_item_to_node(tokens[item_start:i]))
                item_start = None
        elif tok.type in ("bullet_list_open", "ordered_list_open"):
            depth += 1
        elif tok.type in ("bullet_list_close", "ordered_list_close"):
            depth -= 1
            if depth == 0 and tok.type == close_type:
                i += 1
                break
        i += 1

    return {"type": node_type, "content": items}, i - start


def to_prosemirror(data: bytes) -> dict[str, Any]:
    text = data.decode("utf-8", errors="replace")
    tokens = _md.parse(text)

    content: list[dict[str, Any]] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok.type == "heading_open":
            level = int(tok.tag[1]) if tok.tag[1:].isdigit() else 1
            level = min(max(level, 1), 3)
            inline = tokens[i + 1]
            content.append(
                {
                    "type": "heading",
                    "attrs": {"level": level},
                    "content": _inline_to_text_nodes(inline.children),
                }
            )
            i += 3  # heading_open, inline, heading_close
        elif tok.type == "paragraph_open":
            inline = tokens[i + 1]
            content.append({"type": "paragraph", "content": _inline_to_text_nodes(inline.children)})
            i += 3
        elif tok.type in ("bullet_list_open", "ordered_list_open"):
            node, consumed = _collect_list(tokens, i)
            content.append(node)
            i += consumed
        else:
            i += 1

    if not content:
        content = [{"type": "paragraph", "content": []}]

    return sanitize_document({"type": "doc", "content": content})
