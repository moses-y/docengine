FROM python:3.12-slim

# libmagic1 is required by python-magic for server-side MIME sniffing.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /data/storage
ENV STORAGE_DIR=/data/storage
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Migrate + seed + serve, all in one CMD, so the image behaves identically
# under `docker compose` and under a platform like Railway that runs the
# image directly with no compose-level command override. `${PORT:-8000}`
# lets a host that assigns its own port (Railway sets $PORT) still work
# without a build-time change.
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
