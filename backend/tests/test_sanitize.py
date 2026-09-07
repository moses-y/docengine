"""Unit tests for the ProseMirror whitelist sanitizer — the XSS boundary
described in PRD §4.2. These are pure functions: no DB, no event loop.
"""

from __future__ import annotations

from app.content.sanitize import sanitize_document


def test_allows_whitelisted_marks_and_headings():
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 2},
                "content": [{"type": "text", "text": "Hello", "marks": [{"type": "bold"}]}],
            },
            {
                "type": "bulletList",
                "content": [
                    {
                        "type": "listItem",
                        "content": [
                            {"type": "paragraph", "content": [{"type": "text", "text": "item"}]}
                        ],
                    }
                ],
            },
        ],
    }
    result = sanitize_document(doc)
    assert result["type"] == "doc"
    heading = result["content"][0]
    assert heading["type"] == "heading"
    assert heading["attrs"]["level"] == 2
    assert heading["content"][0]["marks"] == [{"type": "bold"}]


def test_strips_script_node_entirely():
    """A malicious/buggy client sending a fabricated 'script' node type must
    have it dropped — there is no whitelisted node it could map to."""
    doc = {
        "type": "doc",
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "safe"}]},
            {"type": "script", "content": [{"type": "text", "text": "alert(1)"}]},
        ],
    }
    result = sanitize_document(doc)
    node_types = [n["type"] for n in result["content"]]
    assert "script" not in node_types
    assert node_types == ["paragraph"]


def test_strips_disallowed_mark_and_unknown_attrs():
    """An 'onclick' attribute or a 'strike' mark has no whitelisted target
    and must not survive sanitization."""
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "click me",
                        "marks": [{"type": "strike"}, {"type": "bold"}],
                        "onclick": "steal()",
                    }
                ],
            }
        ],
    }
    result = sanitize_document(doc)
    text_node = result["content"][0]["content"][0]
    assert "onclick" not in text_node
    assert text_node["marks"] == [{"type": "bold"}]


def test_clamps_heading_level_outside_1_to_3():
    doc = {
        "type": "doc",
        "content": [
            {
                "type": "heading",
                "attrs": {"level": 6},
                "content": [{"type": "text", "text": "Too deep"}],
            }
        ],
    }
    result = sanitize_document(doc)
    assert result["content"][0]["attrs"]["level"] == 1


def test_malformed_input_falls_back_to_empty_document():
    assert sanitize_document({"type": "not-a-doc"}) == {
        "type": "doc",
        "content": [{"type": "paragraph", "content": []}],
    }
    assert sanitize_document("not even a dict") == {
        "type": "doc",
        "content": [{"type": "paragraph", "content": []}],
    }


def test_drops_empty_text_nodes():
    """An empty text node contributes nothing. The surrounding paragraph
    still survives, but — matching how ProseMirror itself serializes an
    empty-content node — with no `content` key at all rather than `[]`."""
    doc = {
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": ""}]}],
    }
    result = sanitize_document(doc)
    assert result == {"type": "doc", "content": [{"type": "paragraph"}]}
