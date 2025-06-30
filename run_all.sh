#!/usr/bin/env bash
# Build images, start database, apply migrations, launch bot & web server
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

# Load env variables so we can use them locally (optional)
if [[ -f .env ]]; then
  # shellcheck disable=SC2046
  export $(grep -v '^#' .env | xargs) || true
fi

# 1. Build all Docker images
printf "\n[INFO] Building Docker images...\n"
docker compose build

# 2. Start database container first
printf "\n[INFO] Starting PostgreSQL container...\n"
docker compose up -d db

# 3. Wait until the database is ready to accept connections
printf "[INFO] Waiting for database to be ready...\n"
until docker compose exec -T db pg_isready -U "${DB_USER:-postgres}" -d "${DB_NAME:-postgres}" >/dev/null 2>&1; do
  printf "."; sleep 2
done
printf "\n[INFO] Database is ready!\n"

# 4. Run Alembic migrations (idempotent)
printf "[INFO] Running Alembic migrations...\n"
docker compose run --rm bot alembic upgrade head
printf "[INFO] Migrations applied.\n"

# 5. Launch bot and web server containers
printf "[INFO] Starting Telegram bot and Flask web server...\n"
docker compose up -d bot web

# 6. Tail logs (optional)
printf "[INFO] All services are up and running. Streaming logs (Ctrl+C to stop)...\n\n"
docker compose logs -f 