# Submission manifest

## Included in this repository

- Source code: `backend/` (FastAPI + SQLAlchemy + PostgreSQL) and `frontend/` (React + TypeScript + TipTap)
- `README.md` — setup and run instructions (Docker one-liner + manual local setup)
- `docs/PRD.md` — full product requirements, ERD, API surface, test plan
- `ARCHITECTURE.md` — condensed architecture note (stack rationale, key decisions, scope cuts)
- `AI_WORKFLOW.md` — AI tool usage note (append-only log)
- `.pre-commit-config.yaml` — lint/format/test hooks
- `docker-compose.yml` + `.env.example` — one-command local deployment
- Automated tests: 22 backend (unit + integration), 7 frontend

## Live deployment

**https://docengine.up.railway.app** — sign in with any account in the table below.

Deployed on Railway as two services (`api` from `backend/Dockerfile`, `web` from `frontend/Dockerfile`) plus managed Postgres and a 500 MB volume for uploads. The whole project is declared as code in `.railway/railway.ts`; see `docs/RAILWAY_SETUP.md` for the full walkthrough. The API is at `https://docengine-api.up.railway.app` and its health endpoint is public: `GET /api/health`.

Migrations and seeding run automatically on every container start, so the accounts below exist on first boot with no manual step.

## Not yet included (fill in before submitting)

- [ ] **Walkthrough video URL** — record the 3–5 minute walkthrough per the assignment brief (main flow, what works end-to-end, what was deprioritized, key decisions, AI workflow) and paste an unlisted Loom/YouTube link here.
- [ ] **Google Drive folder link** — if submitting via Drive rather than a repo link, upload this folder there and paste the link here.

## Reviewer credentials

Four seeded accounts, password `demo1234` for all:

| Email | Notes |
|---|---|
| `alice@ajaia.test` | Owns "Welcome to DocEngine" (shared with Bob as editor) and a private document |
| `bob@ajaia.test` | Has editor access to Alice's shared document — use this to test the sharing flow end-to-end |
| `carol@ajaia.test` | No documents (empty-state testing) |
| `dave@ajaia.test` | No documents |

Seeding runs automatically on every container start (`docker compose up`) — no manual setup step required.

## Status

### Working end-to-end

- Create, rename, edit, and reopen documents with formatting intact (bold, italic, underline, H1–H3, bulleted/numbered lists)
- Autosave with a visible save indicator and an honest conflict message on concurrent edits
- Import `.txt`, `.md`, and `.docx` files into new, editable documents, with dropped `.docx` features (images/tables/footnotes) reported to the user
- File attachments on an existing document
- Sharing: owner grants viewer/editor access by email, revokes it, and "My documents" / "Shared with me" are visibly distinct
- Permission enforcement at the API layer (not just hidden UI controls) — verified by the automated permission-matrix test
- Persistence across restarts (Postgres, not in-memory)

### Incomplete / explicitly out of scope

See `docs/PRD.md` §2 and `ARCHITECTURE.md` for the full list and reasoning. Highlights: no real-time co-editing or presence, no version-history UI (the data is captured, the screen isn't built), no SSO/password reset, no comments/suggestions.

### With another 2–4 hours

1. Real-time presence/co-editing via Yjs + `y-prosemirror` — the single biggest gap.
2. A read-only version-history panel (data already exists in `document_versions`).
3. Export to Markdown/PDF, and full-text search (the GIN index on `documents.content` is already in place, unused).
