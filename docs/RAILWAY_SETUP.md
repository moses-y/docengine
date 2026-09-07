# Deploying to Railway

Railway does **not** read `docker-compose.yml` — it builds each service from its own Dockerfile and wires them together with environment variables and Railway's private networking. This repo has two deployable services (`backend/`, `frontend/`) plus a managed Postgres.

The whole project is declared as code in **[`.railway/railway.ts`](../.railway/railway.ts)**, so the setup below is mostly `railway config apply` rather than clicking through the dashboard. Section 6 covers the dashboard equivalent if you prefer that.

## What the deployment looks like

| Resource | Source | Notes |
|---|---|---|
| `Postgres` | Railway managed image | Exposes `PGUSER` / `PGPASSWORD` / `PGHOST` / `PGPORT` / `PGDATABASE` |
| `api` | `backend/Dockerfile` | Public domain, healthcheck `/api/health`, volume at `/data/storage` |
| `web` | `frontend/Dockerfile` | Public domain pinned to target port 80 (nginx) |
| `api-storage` | volume, 500 MB | Uploaded and imported files; without it they vanish on redeploy |

The browser talks to `web` for the app shell and **directly to `api`'s public domain** for API calls, so CORS matters in this topology (unlike local compose, where nginx proxies `/api` and same-origin applies). Two details make that work:

- `VITE_API_BASE_URL` is a **build arg**, not a runtime variable. Vite inlines `VITE_*` into the static bundle at build time, so changing it requires rebuilding `web`, not just editing a variable.
- nginx must listen on **IPv6** as well as IPv4. Railway's edge reaches containers over IPv6, so `listen 80` alone leaves a healthy, ACTIVE-domain deployment answering every request with `Application not found`. The nginx image normally adds this itself via `10-listen-on-ipv6-by-default.sh`, but that script patches `default.conf` only while it still matches the packaged checksum — replacing the file makes it skip silently.
- `frontend/nginx.conf` generates its `/api/` proxy block at container start from `$API_UPSTREAM` (see `frontend/docker-entrypoint.d/40-api-proxy.sh`). Compose sets that variable; Railway leaves it unset, so the block is empty. This is not cosmetic — nginx resolves `proxy_pass` hostnames at config *load* and refuses to start when the name does not exist, so a hardcoded `proxy_pass http://api:8000` makes the image unbootable anywhere outside the compose network.

## 1. Push the repo to GitHub and authorize Railway

```bash
gh repo create <your-username>/docengine --private --source=. --push
```

If the repo is **private**, Railway's GitHub App needs access to it before it can build: in the Railway project, open a service → **Settings → Source → Connect Repo** and grant the Railway app access to the repo when GitHub prompts. Without this, `railway service source connect` fails with `User does not have access to the repo` and no deployment is ever triggered.

## 2. Install the CLI and create the project

```bash
npm install -g @railway/cli
railway login
railway init --name docengine
```

`railway init` links the current directory to the new project's `production` environment.

> **Windows note:** invoke the binary directly (`.../npm/node_modules/@railway/cli/bin/railway.exe`) for the `railway config` commands. The IaC SDK's version gate shells out to `$_` to check the CLI version; under Git Bash that points at the npm shell shim rather than the binary, and every `config plan` / `config apply` fails with a misleading `requires Railway CLI 5.42.1 or newer`.

## 3. Apply the infrastructure

The authoring file needs the SDK present at the repo root (this is why the root `package.json` exists — it is not an application package):

```bash
npm install
railway config plan     # preview; changes nothing
railway config apply    # add --yes to skip the confirmation
```

`plan` prints an add/change/destroy summary; `plan --out plan.json` gives the full change set including every resolved variable, which is worth reading once before the first apply. Read the `volumeAttachments` block of the api service while you are in there — **`volumeMounts` must be keyed by mount path**, with the volume as the value:

```ts
volumeMounts: { "/data/storage": storage }   // correct
volumeMounts: { "api-storage": { mountPath: "/data/storage" } }   // silently does nothing
```

The second form type-checks, applies without complaint, and attaches nothing: the volume is created detached at a default `/tmp` with a null `serviceId`, so uploads go to the container filesystem and disappear on the next redeploy. The tell is `volumeAttachments: {}` in the plan JSON, and `detached` in `railway status`. Confirm it landed:

```bash
railway api 'query { project(id: "<project-id>") { volumes { edges { node { name volumeInstances { edges { node { mountPath serviceId state } } } } } } } }'
```

Note that **apply is atomic** — one bad value fails the entire change set, and the diagnostic is only visible with `--json`. The volume size is the easy one to trip over: Railway's current plan caps volumes at 500 MB, and asking for more fails all ten changes with `Max size of 500 MB on current plan`.

## 4. Generate the domains — before the first `web` build

```bash
railway domain --service api            # api reads $PORT, so no --port needed
railway domain --service web --port 80  # nginx listens on a fixed 80
railway domain list --service api
```

Order matters. `VITE_API_BASE_URL` is `https://${{api.RAILWAY_PUBLIC_DOMAIN}}/api`, and build args are resolved when the image is built — so if `api` has no public domain yet, `web` bakes a broken API URL into its bundle and needs a rebuild to recover. `CORS_ORIGINS` is the mirror image (`https://${{web.RAILWAY_PUBLIC_DOMAIN}}`) but resolves at deploy time, so it is not order-sensitive.

Both use Railway's `${{service.VAR}}` reference syntax rather than literal hostnames, so nothing needs editing when a domain changes. `CORS_ORIGINS` does need the api **redeployed** to pick up a new value, though — the reference resolves when the container starts, not continuously.

A domain generated *before* the service has ever deployed can end up registered but unroutable: `railway domain status` reports `ACTIVE`, the container logs show nginx serving happily, and the edge still returns `Application not found` with an `x-railway-fallback: true` header. Updating the target port does not repair it. Delete and regenerate the domain, which fixes it at the cost of a new host label:

```bash
railway domain delete <domain-id> --service web
railway domain --service web --port 80
```

## 5. Set the secret

`JWT_SECRET` is declared as `preserve()` in the authoring file — Railway keeps whatever value is already set and the real secret never enters git. Set it out of band, reading from stdin so it stays out of your shell history and the process list:

```bash
openssl rand -hex 32 | railway variables --service api --set-from-stdin JWT_SECRET
```

Then confirm the wiring resolved as expected:

```bash
railway variables --service api          # table view, values truncated
railway variables --service api --json   # full raw values
```

`DATABASE_URL` should read `postgresql+asyncpg://postgres:***@postgres.railway.internal:5432/railway`. The `postgresql+asyncpg://` scheme is why the URL is assembled from the individual `PG*` variables instead of referencing `Postgres.DATABASE_URL` — Railway's own value uses the plain `postgresql://` scheme, which SQLAlchemy's async engine rejects.

The backend needs no further setup: its `Dockerfile` CMD runs `alembic upgrade head` and `python -m app.seed` before starting uvicorn on `${PORT:-8000}`, so migrations and the four seeded demo accounts are ready on first boot.

## 6. Dashboard equivalent

If you would rather not use the CLI, the same result via railway.app: **New Project → Deploy from GitHub repo**, delete the auto-created root service, then **+ New → Database → PostgreSQL**, then add two services from the same repo with **Root Directory** set to `backend` and `frontend`. Copy the variables out of `.railway/railway.ts`, add a volume mounted at `/data/storage` on the backend, and set the frontend's **Target Port** to 80 under Settings → Networking.

## 7. Verify

Visit `web`'s public URL. You should land on the login screen with the seeded-account hint chips (`alice@ajaia.test` / `demo1234`, etc. — see `README.md`). Sign in as Alice, confirm her two documents and the share with Bob are visible, then sign in as Bob in a private window to confirm the shared document shows up under "Shared with me".

Useful when it does not work:

```bash
railway status                        # every resource and its state
railway logs --service api            # deploy + runtime logs
railway deployment list --service web
```

If login fails with a network error it is almost always one of:

- `CORS_ORIGINS` not matching the frontend's exact origin (scheme included, no trailing slash)
- `VITE_API_BASE_URL` baked in wrong — remember it is build-time, so fix the variable *and* redeploy `web`
- `web` deployed before `api` had a domain (the same problem, from section 4)
- `CORS_ORIGINS` resolved to a stale domain because the api has not been redeployed since the frontend's domain changed

`Application not found` (rather than a CORS or connection error) is an edge-routing problem, not an application one — check for `x-railway-fallback: true` in the response headers and see the domain note in section 4.

## 8. Ongoing deploys

Once the GitHub source is connected, every push to `master` redeploys both services. Migrations run again on each backend boot (`alembic upgrade head` is idempotent) and the seed script only creates the demo data if it is missing.

Infrastructure changes go through the authoring file: edit `.railway/railway.ts`, `railway config plan`, then `railway config apply`. Be aware that the file is authoritative — **removing a variable from it deletes that variable** on the next apply. For CI, pin the reviewed plan and apply that exact file:

```bash
railway config plan --out railway-plan.json
railway config apply --plan railway-plan.json --yes --confirm-destructive
```

## 9. Alternative: deploy without GitHub

`railway up` uploads the current directory directly, which is handy for a one-off or when the GitHub App cannot be authorized:

```bash
cd backend  && railway up --service api
cd frontend && railway up --service web
```

The trade-off is that this switches the service's source from GitHub to local upload, so you lose deploy-on-push and the next `railway config apply` will want to set the GitHub source back.
