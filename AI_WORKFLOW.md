# AI workflow note

Append-only log of how AI tools were used to build DocEngine, per the assignment's requirement to disclose this. Written in first person as the actual session log; entries are added, not edited, as the project progresses.

## Tool used

**Claude** (Anthropic), used through Cowork mode — an agentic session with direct file read/write and a sandboxed shell, not just a chat window. Everything below happened in that session: I described the assignment and answered a couple of clarifying questions (backend language, output format for the PRD); the rest — the PRD, the ERD, the full backend and frontend, the tests, and this document — was written and then verified by running it, not just generated and trusted.

## 2026-09-07 — PRD and ERD

Asked Claude to turn the raw assignment brief into a PRD with an ERD, features list, and a Postgres/React/Python stack. It asked one clarifying question up front (FastAPI vs. Go vs. Rust for the backend — I picked FastAPI for import-library maturity, i.e. `mammoth` for `.docx`) rather than guessing, which I'd have had to redo later otherwise. It produced `docs/PRD.md` with a full ERD, API surface, and an explicit non-goals list (no CRDT co-editing, no version-history UI, no SSO) — I kept all of these cuts; they matched what I would have cut myself given the timebox, and having them written down up front is what let the build stay scoped.

## 2026-09-07 — Full-stack build

Asked it to build the PRD into a real repo: FastAPI + SQLAlchemy + Postgres backend, React + TipTap frontend, files kept under ~450 lines each, organized by layer (routers/services/repositories on the backend; api/hooks/components/pages on the frontend). This is where AI usage mattered most in terms of raw time saved — scaffolding ~90 files with consistent naming and layering by hand would have eaten most of the timebox on its own.

**What I verified, not just accepted:**

- **The permission matrix** (`tests/test_permissions.py`) — the one test I'd have written first myself, because it's the one place a sharing product can quietly get access control wrong. I read through the actual assertions (stranger → 404, under-privileged viewer → 403) rather than trusting a green checkmark, because that specific distinction (not conflating "no access" with "not enough access") is the detail that's easy to get backwards.
- **The `.docx` importer** — this was the one piece I wasn't confident would work out of the box, since it hand-parses `mammoth`'s HTML output into ProseMirror JSON with a small `HTMLParser` subclass rather than using an existing HTML→ProseMirror library. It was run against real generated `.docx` fixtures (built with `python-docx` in the test itself, including one with an embedded table) inside the session's sandbox, not just written and assumed correct — and it did need one real fix (see below).
- **All 22 backend tests and 7 frontend tests were actually executed** in the session (`pytest`, `vitest`), not just written. Ruff (lint + format) and `tsc --noEmit` were also run to completion and came back clean.

**What I changed or rejected:**

- The sanitizer's own test suite initially asserted the wrong output shape for an empty-content paragraph (expected `"content": []`, but ProseMirror's real serialization omits the key entirely for a childless node) — caught by actually running the test, not by inspecting the code, and fixed by correcting the test's expectation rather than changing the (correct) sanitizer behavior.
- Claude's first pass used `enum.StrEnum` for the share-role enum (a Python 3.11+ feature) — this broke on the Python 3.10 the verification sandbox happened to have installed, even though the target deployment is Python 3.12. Reverted to the more portable `str, Enum` pattern rather than assume the higher version would always be present.
- A handful of real lint findings from `ruff` were fixed, not suppressed: two unused imports in `app/seed.py`, and a couple of lines restructured for length/clarity. Two lint rules (`B008` for FastAPI's idiomatic `Depends(...)` default-arg pattern, and `EXE002` for a file-permission quirk of this sandbox's mounted filesystem) were deliberately ignored in `pyproject.toml` with a one-line reason each, rather than silently suppressed.
- Declined to port the project to SvelteKit/Supabase after finding a similar public submission built on that stack — the FastAPI/React/Postgres stack was already built, tested, and working, and switching stacks wouldn't have improved the product, only reset the clock.

## What's still owed

The frontend's own `node_modules` was verified in an isolated scratch copy (native Linux filesystem) rather than in the mounted project folder, because installing directly into the mounted `D:\DocEngine\frontend` folder was extremely slow over that mount and left a partially-corrupted `node_modules` behind. That folder is `.gitignore`d and irrelevant to the deliverable, but should be deleted (or just overwritten by `npm install`) before local development.

## 2026-09-07 — Deployment, and what only deploying found

Deployed to Railway in the same agentic session: two services built from their own Dockerfiles plus managed Postgres, declared as infrastructure-as-code in `.railway/railway.ts` (see `docs/RAILWAY_SETUP.md`).

This is the entry I'd point a reviewer at, because deploying found five real bugs that a green test suite had not — every one of them in application code, not in the deployment:

1. **The initial migration could not run on an empty database.** It created the `share_role` enum explicitly, then passed the same `ENUM` object to `create_table` as a column type, so SQLAlchemy emitted `CREATE TYPE` twice: `DuplicateObjectError` on any fresh Postgres. Deterministic, and it would have hit a reviewer running `docker compose up` just as hard.
2. **Every authorization check was issuing invalid SQL.** `role_for_user` built a `CASE` whose branches were the `share_role` enum and the varchar `'owner'`; Postgres refuses to match those types. `'owner'` is deliberately not an enum member — ownership is not a grant — so the fix casts the column to text.
3. **Login rejected its own seeded accounts.** `EmailStr` plus a newer `email-validator` (pinned only `>=2.2`) treats `.test` as a reserved TLD, so every documented `@ajaia.test` credential got a 422 before the password was checked. Login is a credential lookup, so format validation there could only ever make existing accounts unreachable; registration keeps `EmailStr`.
4. **The frontend image could not boot outside the compose network.** `nginx.conf` hardcoded `proxy_pass http://api:8000`, and nginx resolves proxy_pass hostnames at config load — it refuses to start when the name does not exist. The `/api/` block is now generated at container start from `$API_UPSTREAM`.
5. **Auth was cookie-only, which silently breaks across hostnames.** The client sent no `Authorization` header and relied on the `SameSite=Lax` cookie. That works locally, where nginx makes the API same-origin, but the deployed services sit on separate hosts under `up.railway.app` — a Public Suffix List entry, so the browser treats them as cross-site and withholds the cookie. Login appeared to succeed and every authenticated request then failed. The API already accepted `Bearer`, so the fix was to send the token the login response had always returned.

Bugs 1 and 2 were both inside the reach of `tests/integration/`, which spins up real Postgres via testcontainers and runs the migration — they survived because Docker was not running on the machine, so that suite had never been executed. The lesson I'd actually draw: the tests were written and the unit tests were run, but "tests exist" and "tests ran on this machine" are different claims, and only the second one is worth anything. Bugs 3, 4 and 5 are of a kind no unit test would catch, because each depends on a property of the deployed environment — installed dependency versions, DNS resolvability, and cross-site cookie rules.

Two platform-side traps are documented in `docs/RAILWAY_SETUP.md` rather than here, since they are Railway behavior rather than AI workflow: nginx needing an explicit IPv6 listener, and a generated domain that reports `ACTIVE` while never routing.

Also worth recording as a correction: the `node_modules` corruption noted under "What's still owed" above recurred when reinstalling in the mounted folder, and broke `vitest` with a missing nested `tinyspy`. The frontend typecheck (`tsc --noEmit`) was run clean before deploying, and the Docker build installs into a fresh tree, so the deployed bundle is sound — but the frontend test suite was **not** re-run after the auth change. That is the one verification gap I would close first.
