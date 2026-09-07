# Architecture note

This is the condensed version of `docs/PRD.md` — what was prioritized, why, and what was deliberately cut, written for a reviewer skimming in a few minutes rather than reading the full spec.

## Stack and why

**React + TypeScript + TipTap** for the editor: TipTap wraps ProseMirror, which gives a real, whitelistable document model (see below) rather than a `contentEditable` div and a prayer.

**FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL**: `jsonb` gives us a real column type for the document content with a GIN index reserved for future search, without needing a document database. FastAPI's dependency injection made the permission gate (below) trivial to thread through every route uniformly.

**Docker Compose, two services**: `api` (FastAPI + nginx-free, serves JSON only) and `web` (static build served by nginx, which also proxies `/api/*` to `api`). This avoids any CORS configuration in both dev and prod, and matches how it deploys to Railway/Fly.io — one Postgres add-on, two containers.

## The one architectural decision that mattered most

**Content is stored as ProseMirror JSON, never HTML**, and a server-side whitelist (`app/content/sanitize.py`) is the only thing that decides what node types and marks are allowed to reach the database. This does two things at once: it's the actual XSS boundary (there is no "sanitize this HTML" problem to get subtly wrong, because HTML never enters the trust boundary at all), and it's what makes every import path — Markdown, `.docx`, or the editor itself — converge on one shape that the frontend can render identically regardless of where the content came from.

## Layering

```
routers/       HTTP + Pydantic only — no business logic
services/      permission checks, business rules, transactions
repositories/  SQLAlchemy queries — return ORM objects, know nothing of HTTP
```

The payoff: `tests/test_permissions.py` — the single most important test in the repo — tests the real `require_role()` function with a monkeypatched repository call, with no database, no ASGI app, and no HTTP client. It runs in under a second and exercises the exact rule that matters most for a sharing product: **a stranger with no access gets 404, a viewer attempting an editor-only action gets 403** — different failure modes, decided in one place, tested exhaustively (owner/editor/viewer/stranger × read/write/share/delete).

## Concurrency: optimism over merging

Every `PATCH /api/documents/{id}` with new content must include `base_version`. If the server's `documents.version` has already moved past it, the request is rejected with `409` and the client shows "This document changed elsewhere — reload to continue." This was a deliberate choice over building real-time merge (CRDT/OT): a two-person take-home in a few hours cannot responsibly ship conflict-free merging, and a visible, honest conflict beats a silent, wrong one. `document_versions` rows are still written on a cadence (every 10th autosave, plus every explicit flush), so a future version-history feature is a read-only addition, not a schema change.

## What was cut, and why

| Cut | Reason |
|---|---|
| Real-time co-editing (CRDT/OT, presence) | Highest-cost item available; optimistic concurrency (above) is the honest, shippable alternative |
| Comments, suggestion mode, version-history UI | `document_versions` already captures the data; only the UI is missing |
| SSO / password reset / email verification | Seeded accounts + JWT covers the reviewer's actual need: prove sharing works between two known users |
| Images, tables, footnotes in `.docx` import | No whitelisted ProseMirror node to hold them; dropped and reported to the user rather than silently discarded or half-rendered |
| Public link sharing, org-wide roles | Assignment asks for owner → grant-to-another-user; per-user grants are the minimum that demonstrates the model correctly |

## What would come next (given 2–4 more hours)

1. Yjs + `y-prosemirror` for real presence/co-editing — the biggest gap, and the reason optimistic concurrency was chosen as the interim answer rather than skipped entirely.
2. A read-only version-history panel — the data already exists in `document_versions`.
3. Export to Markdown/PDF and full-text search (the GIN index on `documents.content` is already in place, unused).

See `docs/PRD.md` for the full ERD, API surface, and test plan.
