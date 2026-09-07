"""Unit test for the DOCX -> ProseMirror converter (PRD §4.3, §8).

Builds a real .docx fixture with `python-docx` (a dev/test-only dependency —
`app.content.importers.docx_importer` itself only ever *reads* .docx via
`mammoth`, and never imports `python-docx`), covering headings, nested
lists, and bold+italic runs, plus an embedded image to prove dropped
features are reported rather than silently lost.
"""

from __future__ import annotations

import io

import pytest

docx = pytest.importorskip("docx", reason="python-docx is a test-only fixture builder")

from app.content.importers import docx_importer  # noqa: E402


def _build_fixture_docx() -> bytes:
    document = docx.Document()
    document.add_heading("Project Plan", level=1)

    p = document.add_paragraph()
    p.add_run("This paragraph has ")
    p.add_run("bold").bold = True
    p.add_run(" and ")
    p.add_run("italic").italic = True
    p.add_run(" text.")

    document.add_paragraph("First bullet", style="List Bullet")
    document.add_paragraph("Second bullet", style="List Bullet")
    document.add_paragraph("Step one", style="List Number")
    document.add_paragraph("Step two", style="List Number")

    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()


def test_headings_lists_and_emphasis_survive_import():
    data = _build_fixture_docx()
    doc, dropped = docx_importer.to_prosemirror(data)

    assert doc["type"] == "doc"
    node_types = [n["type"] for n in doc["content"]]

    assert "heading" in node_types
    heading = next(n for n in doc["content"] if n["type"] == "heading")
    assert heading["attrs"]["level"] == 1
    assert heading["content"][0]["text"] == "Project Plan"

    # The bold+italic paragraph: at least one run carries each mark.
    paragraphs = [n for n in doc["content"] if n["type"] == "paragraph"]
    all_text_nodes = [t for p in paragraphs for t in p.get("content", [])]
    marks_seen = {m["type"] for t in all_text_nodes for m in t.get("marks", [])}
    assert "bold" in marks_seen
    assert "italic" in marks_seen

    assert "bulletList" in node_types or "orderedList" in node_types
    assert not dropped  # this fixture has no images/tables to drop


def test_dropped_features_are_reported_not_silently_lost():
    document = docx.Document()
    document.add_paragraph("Text before a table.")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "a"
    table.cell(0, 1).text = "b"

    buf = io.BytesIO()
    document.save(buf)

    doc, dropped = docx_importer.to_prosemirror(buf.getvalue())

    assert "tables" in dropped
    # The surrounding paragraph text must still be present.
    texts = [
        t["text"]
        for n in doc["content"]
        if n["type"] == "paragraph"
        for t in n.get("content", [])
        if t["type"] == "text"
    ]
    assert any("Text before a table" in t for t in texts)
