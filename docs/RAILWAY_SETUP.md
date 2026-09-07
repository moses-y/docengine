# Deploying to Railway

Railway does **not** read `docker-compose.yml` — it builds each service from its own Dockerfile and wires them together with environment variables and Railway's private networking. This repo has two deployable services (`backend/`, `frontend/`) plus a managed Postgres, so you'll create three things in one Railway project.

## 1. Push the repo to GitHub

Railway deploys from a GitHub repo (or `railway up` from your local folder — see step 7 for that alternative). If you haven't already:

```bash
gh repo create <your-username>/docengine --private --source=. --push
```

or create the repo on github.com and:

```bash
git remote add origin https://github.com/<your-username>/docengine.git
git push -u origin master
```

## 2. Create the Railway project and Postgres database

1. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo** → select your repo.
2. Railway will try to auto-detect a service from the repo root — delete that first auto-created service (you'll add two scoped ones in step 3).
3. In the same project, click **+ New** → **Database** → **Add PostgreSQL**. Railway provisions it and exposes its connection details as variables on that Postgres service (`PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE`, and a combined `DATABASE_URL` in the plain `postgresql://` form).

## 3. Add the backend service

1. **+ New** → **GitHub Repo** → same repo again.
2. Once created, open its **Settings**:
   - **Root Directory**: `backend`
   - Railway will detect `backend/Dockerfile` automatically and build from it.
3. Open **Variables** and add:

   | Variable | Value |
   |---|---|
   | `DATABASE_URL` | `postgresql+asyncpg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}` |
   | `JWT_SECRET` | a real random value — e.g. output of `openssl rand -hex 32` |
   | `JWT_ALGORITHM` | `HS256` |
   | `JWT_EXPIRE_MINUTES` | `1440` |
   | `MAX_UPLOAD_BYTES` | `5242880` |
   | `STORAGE_DIR` | `/data/storage` |
   | `CORS_ORIGINS` | the frontend's public URL (fill in after step 4 — Railway lets you edit variables anytime and redeploy) |

   The `${{Postgres.PGUSER}}`-style syntax is Railway's variable reference — it lets one service read another's variables so you never hardcode the database password. Note the `postgresql+asyncpg://` scheme: Railway's own `DATABASE_URL` uses plain `postgresql://`, which SQLAlchemy's async engine can't use directly, hence building it manually here rather than referencing `Postgres.DATABASE_URL` verbatim.

4. **Add a volume** (Settings → Volumes → **+ New Volume**) mounted at `/data/storage`, so uploaded/imported files survive redeploys. Without this, attachments and imports still work but vanish on the next deploy.
5. Deploy. Railway assigns a dynamic `$PORT`; the backend's `Dockerfile` CMD already binds to `${PORT:-8000}` and runs `alembic upgrade head` + `python -m app.seed` before starting the server, so migrations and the four seeded demo accounts are ready on first boot — no manual step.
6. Under **Settings → Networking**, click **Generate Domain** to get a public URL like `docengine-api-production.up.railway.app`. Copy it — you'll need it for the frontend's build variable next.

## 4. Add the frontend service

1. **+ New** → **GitHub Repo** → same repo again.
2. **Settings**:
   - **Root Directory**: `frontend`
   - Railway detects `frontend/Dockerfile` (the nginx-based build).
3. **Variables** — this one is a **build-time** variable, since Vite bakes it into the static bundle:

   | Variable | Value |
   |---|---|
   | `VITE_API_BASE_URL` | `https://<your-backend-domain>/api` (the domain from step 3.6) |

4. **Settings → Networking**: since this container's nginx listens on a fixed port `80` rather than reading `$PORT`, set the **Target Port** to `80` explicitly (Railway's Docker deployments let you pin this instead of requiring the app to read `$PORT`).
5. Deploy, then **Generate Domain** here too — this is the URL you'll actually visit and share.
6. Go back to the **backend** service's `CORS_ORIGINS` variable (step 3) and set it to this frontend domain (e.g. `https://docengine-web-production.up.railway.app`), then redeploy the backend so it accepts requests from the real frontend origin.

## 5. Verify

Visit the frontend's public URL. You should land on the login screen with the seeded-account hint chips (`alice@ajaia.test` / `demo1234`, etc. — see `README.md`). Sign in as Alice, confirm her two documents and the share with Bob are visible, then sign in as Bob in a private window to confirm the shared document shows up under "Shared with me".

If login fails with a network error, it's almost always one of: `CORS_ORIGINS` not matching the frontend's exact origin (including `https://`, no trailing slash), or `VITE_API_BASE_URL` pointing at the wrong backend domain (remember it's baked in at build time — changing it requires a redeploy of the frontend, not just a variable edit).

## 6. Ongoing deploys

Every `git push` to the branch Railway is watching redeploys both services automatically. Migrations run again on every backend boot (`alembic upgrade head` is idempotent), and the seed script only creates the demo accounts/documents if they don't already exist.

## 7. Alternative: deploy without GitHub

If you'd rather not push to GitHub first, install the [Railway CLI](https://docs.railway.app/guides/cli) and run `railway login` then `railway up` from the repo root — it uploads the local folder directly. You'll still need to do steps 2–4 above (add Postgres, configure two services with their root directories and variables) either via the CLI (`railway variables set KEY=value`) or the dashboard.
