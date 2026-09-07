# DocEngine

A lightweight collaborative document editor — create, edit, import, and share rich-text documents. Built for the Ajaia LLC AI-Native Full Stack Developer take-home assignment (see `SUBMISSION.md` for the reviewer-facing manifest).

**Stack:** React 18 + TypeScript (Vite, TipTap) · Python 3.12 + FastAPI · PostgreSQL 16 · Docker.

For the full product spec — goals, non-goals, user stories, ERD, API surface — see [`docs/PRD.md`](docs/PRD.md). For the condensed engineering rationale, see [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Quick start (Docker)

```bash
git clone <this-repo>
cd DocEngine
cp .env.example .env
docker compose up --build
```

Open **http://localhost:5173**. The API container runs Alembic migrations and the seed script automatically on every start (idempotent — safe to restart), so the app is immediately usable with:

| Email | Password | Notes |
|---|---|---|
| `alice@ajaia.test` | `demo1234` | Owns two documents, one already shared with Bob (editor) |
| `bob@ajaia.test` | `demo1234` | Has editor access to Alice's "Welcome to DocEngine" doc |
| `carol@ajaia.test` | `demo1234` | No documents — good for testing an empty state |
| `dave@ajaia.test` | `demo1234` | No documents |

The login screen also shows these as clickable hints.

## Features

- **Rich-text editing** — bold, italic, underline, headings (H1–H3), bulleted and numbered lists. Autosaves 800ms after you stop typing, with a visible save indicator and a conflict warning if the document changed elsewhere.
- **File import** — upload a `.txt`, `.md`, or `.docx` file to create a new document. Headings, bold/italic/underline, and lists are preserved; **images, tables, and footnotes in `.docx` files are dropped** (stated in the import dialog and confirmed in a banner after import). Max file size: 5 MB.
- **Sharing** — the owner grants another seeded user `viewer` or `editor` access by email, and can revoke it. The home page splits documents into **My documents** / **Shared with me**.
- **Attachments** — any file can be attached to an existing document (separate from the import flow).

See [`docs/PRD.md`](docs/PRD.md) for the full feature list, including what was deliberately left out (real-time co-editing, version history UI, comments) and why.

## Local development (without Docker)

**Backend**

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp ../.env.example ../.env   # edit DATABASE_URL to point at your own Postgres
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Vite proxies `/api` to `http://localhost:8000` (see `frontend/vite.config.ts`), so both dev servers work together without CORS configuration.

## Testing

```bash
# Backend — runs both unit and integration tests; the integration test
# (tests/integration/test_share_flow.py) needs Docker and skips itself
# cleanly if it can't reach the Docker daemon.
cd backend && PYTHONPATH=. python -m pytest -q

# Frontend
cd frontend && npm test
```

The single most important backend test is `tests/test_permissions.py::test_require_role_matrix` — it exercises every (role × minimum-required-role) combination and asserts the exact 404-vs-403 split described in `docs/PRD.md` §5.3 (a stranger gets 404, an under-privileged viewer gets 403). `tests/integration/test_share_flow.py` then proves the same rule end-to-end over real HTTP against a real Postgres container.

## Pre-commit hooks

```bash
pip install pre-commit
pre-commit install
```

This runs on every commit: whitespace/EOF hygiene, `ruff` lint + format on `backend/`, the backend unit test suite (integration tests excluded — they need Docker), and a frontend typecheck. Run it manually with `pre-commit run --all-files`.

## Project layout

```
DocEngine/
├── docs/PRD.md              # Full product requirements + ERD
├── ARCHITECTURE.md          # Condensed engineering rationale
├── AI_WORKFLOW.md           # AI tool usage note (assignment requirement)
├── SUBMISSION.md            # Reviewer manifest
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── models/          # One file per ERD table
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── repositories/    # SQLAlchemy queries only
│   │   ├── services/        # Business rules + permission checks
│   │   ├── routers/         # HTTP only — thin
│   │   └── content/         # ProseMirror sanitizer + txt/md/docx importers
│   ├── alembic/versions/    # Hand-written initial migration
│   └── tests/               # Unit tests + tests/integration/ (Docker-backed)
└── frontend/
    └── src/
        ├── api/              # fetch wrappers, one per resource
        ├── hooks/            # useAuth, useDocuments, useAutosave, ...
        ├── components/       # editor/, documents/, sharing/, layout/, common/
        └── pages/            # LoginPage, DocumentsPage, DocumentEditorPage
```

Every file is kept under ~450 lines by design — one table per model file, one resource per router/service/repository, one importer per file format.

## Deployment

**Live: https://docengine.up.railway.app** (API at `https://docengine-api.up.railway.app`). Sign in with any seeded account below.

Both `backend/Dockerfile` and `frontend/Dockerfile` build standalone and are ready to deploy as-is. See **[`docs/RAILWAY_SETUP.md`](docs/RAILWAY_SETUP.md)** for the full step-by-step (Postgres add-on, environment variables, build-time `VITE_API_BASE_URL`, volumes, CORS). The same two Dockerfiles work equally well on Fly.io or any other container platform — the backend image already runs migrations and seeding on boot (`alembic upgrade head && python -m app.seed`), and reads `$PORT` if the platform assigns one dynamically.
