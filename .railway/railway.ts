import {
  defineRailway,
  github,
  postgres,
  preserve,
  project,
  service,
  volume,
} from "railway/iac";

const REPO = "moses-y/docengine";
const BRANCH = "master";

export default defineRailway(() => {
  const db = postgres("Postgres");

  // Uploaded and imported files live here; without a volume they vanish on
  // every redeploy. 500 MB is the cap on Railway's current plan for this
  // workspace -- ample next to MAX_UPLOAD_BYTES of 5 MB per file.
  const storage = volume("api-storage", { sizeMB: 500 });

  const api = service("api", {
    source: github(REPO, { rootDirectory: "backend", branch: BRANCH }),
    build: { builder: "DOCKERFILE" },
    healthcheck: "/api/health",
    env: {
      // Built by hand rather than referencing Postgres.DATABASE_URL because
      // Railway hands out the plain `postgresql://` scheme, which SQLAlchemy's
      // async engine rejects -- it needs `postgresql+asyncpg://`.
      DATABASE_URL:
        "postgresql+asyncpg://${{Postgres.PGUSER}}:${{Postgres.PGPASSWORD}}@${{Postgres.PGHOST}}:${{Postgres.PGPORT}}/${{Postgres.PGDATABASE}}",
      // Set out of band (`railway variables --set JWT_SECRET=...`) so the real
      // secret never lands in git; preserve() keeps whatever is already there.
      JWT_SECRET: preserve(),
      JWT_ALGORITHM: "HS256",
      JWT_EXPIRE_MINUTES: "1440",
      MAX_UPLOAD_BYTES: "5242880",
      STORAGE_DIR: "/data/storage",
      // Resolved by Railway at deploy time, so it tracks the web service's
      // generated domain without hardcoding it here.
      CORS_ORIGINS: "https://${{web.RAILWAY_PUBLIC_DOMAIN}}",
    },
    volumeMounts: {
      "api-storage": { mountPath: "/data/storage" },
    },
  });

  const web = service("web", {
    source: github(REPO, { rootDirectory: "frontend", branch: BRANCH }),
    build: { builder: "DOCKERFILE" },
    env: {
      // Vite bakes this into the bundle, so it is consumed at *build* time as
      // a Docker build arg -- the api service must already have a public
      // domain when the web service builds.
      VITE_API_BASE_URL: "https://${{api.RAILWAY_PUBLIC_DOMAIN}}/api",
    },
  });

  return project("docengine", {
    resources: [db, storage, api, web],
  });
});
