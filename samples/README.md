# Sample files

Files for exercising the import and attachment flows — used in the walkthrough
video, and useful to a reviewer who wants to try import without hunting for a
`.docx`.

| File | Exercises |
|---|---|
| `quarterly-report.docx` | Headings (H1–H3), bold, italic, bulleted and numbered lists — **plus a table and an embedded image**, which the importer deliberately drops and reports |
| `meeting-notes.md` | Markdown headings, bold/italic, bulleted and numbered lists |
| `release-checklist.txt` | Plain text, one paragraph per blank-line-separated block |

Import from the document list ("Import file"), or over the API:

```bash
TOKEN=$(curl -s -X POST "$API/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"alice@ajaia.test","password":"demo1234"}' | jq -r .access_token)

curl -s -X POST "$API/api/documents/import" \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@samples/quarterly-report.docx"
```

## Verified behavior

Imported against the deployed API, these are the actual results — not what the
docs claim:

| File | Result |
|---|---|
| `quarterly-report.docx` | 4 headings (levels 1, 2, 3), 5 paragraphs, 1 bulleted list, 1 numbered list, `bold` + `italic` marks; `dropped_features: ["images", "tables"]` |
| `meeting-notes.md` | 4 headings (levels 1, 2), 2 bulleted lists, 1 numbered list, `bold` + `italic`; nothing dropped |
| `release-checklist.txt` | 4 paragraphs; nothing dropped |

The `.docx` table and image are the point of that file: `dropped_features`
comes back naming exactly what was lost, so the UI can tell the user rather
than silently mangling the document. The parser also recovers after the
dropped subtrees — the paragraph following the table survives, which is what
makes the trailing-paragraph line in that file worth keeping.

`quarterly-report.docx` is generated rather than hand-made, by
`make_quarterly_report.py` (needs `python-docx`; not part of the app's
dependencies). The 4×4 PNG it embeds is built inline, so no binary image blob
is committed. Regenerate with:

```bash
pip install python-docx
python samples/make_quarterly_report.py
```

## Attachments

Any of these also work as an attachment on an existing document (`.txt` is the
easiest to eyeball). The cap is `MAX_UPLOAD_BYTES`, 5 MB by default.
