"""Plain-text import: blank-line-separated blocks become paragraphs
(PRD §4.3). No formatting is inferred — a `.txt` file has none to preserve.
"""

from __future__ import annotations

from typing import Any

from app.content.sanitize import sanitize_document


def to_prosemirror(data: bytes) -> dict[str, Any]:
    text = data.decode("utf-8", errors="replace")
    blocks = [b.strip() for b in text.replace("\r\n", "\n").split("\n\n")]
    blocks = [b for b in blocks if b]

    if not blocks:
        content = [{"type": "paragraph", "content": []}]
    else:
        content = [
            {
                "type": "paragraph",
                "content": [{"type": "text", "text": " ".join(block.split("\n"))}],
            }
            for block in blocks
        ]

    return sanitize_document({"type": "doc", "content": content})
