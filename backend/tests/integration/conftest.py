"""Integration test fixtures: a real, ephemeral PostgreSQL via testcontainers
(PRD §8), migrated with Alembic, wired into the FastAPI app by overriding
`get_db` — the app's own cached engine (built from `DATABASE_URL` at import
time) is left untouched, so these tests never risk touching a real database.

Requires Docker. Skipped automatically (module-level) if the Docker socket
is unreachable, so `pytest` still runs cleanly in the unit-only sandbox
these were authored in.
"""

from __future__ import annotations

import subprocess

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

pytest.importorskip("testcontainers", reason="testcontainers is a dev-only integration dependency")
from testcontainers.postgres import PostgresContainer  # noqa: E402


def _docker_available() -> bool:
    try:
        subprocess.run(["docker", "info"], capture_output=True, timeout=5, check=True)
        return True
    except Exception:
        return False


@pytest.fixture(scope="module")
def postgres_url():
    if not _docker_available():
        pytest.skip("Docker is not available in this environment")
    with PostgresContainer("postgres:16-alpine") as pg:
        url = pg.get_connection_url().replace("postgresql://", "postgresql+asyncpg://", 1)
        yield url


@pytest.fixture(scope="module")
def migrated_db(postgres_url):
    """Runs the real Alembic migration chain against the container once per
    test module, so integration tests exercise the same schema production
    deploys use — not a `create_all()` shortcut."""

    from alembic.config import Config

    from alembic import command

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", postgres_url)
    command.upgrade(cfg, "head")
    return postgres_url


@pytest_asyncio.fixture
async def db_session(migrated_db):
    engine = create_async_engine(migrated_db, future=True)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def client(migrated_db):
    from app.database import get_db
    from app.main import app

    engine = create_async_engine(migrated_db, future=True)
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
    await engine.dispose()
