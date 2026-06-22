# Docker — digitization viewer (development)

Runs the FastAPI backend and the Next.js frontend in containers, wired for
**development** (source bind-mounted, hot reload). The backend connects to the
**existing external Postgres** defined by `VIEWER_DB_URL` — no database
container is started.

## URLs

| Service  | URL                              | Host port → container |
|----------|----------------------------------|-----------------------|
| Frontend | http://192.168.15.27:8082       | 8082 → 3000           |
| Backend  | http://192.168.15.27:8000       | 8000 → 8000           |

## Run

```bash
cd docker
docker compose up --build
```

Stop with `Ctrl+C`, or `docker compose down` to remove the containers.

After the first build you can usually skip `--build`:

```bash
docker compose up
```

Rebuild when dependencies change:
- backend → `docker/requirements.txt`
- frontend → `package.json` / `package-lock.json`

```bash
docker compose build backend   # or: frontend
```

## What's wired up

- **Hot reload** — `../dashboard` is mounted into the backend and the frontend
  source into the frontend container, so edits take effect live (uvicorn
  `--reload`, `next dev`).
- **Imports** — backend runs from `/app/dashboard_backend` with `PYTHONPATH=/app`
  so both `dashboard_backend`'s top-level modules and the sibling `LLMBatcher`
  package resolve.
- **Database** — `VIEWER_DB_URL` is read from `../dashboard/.env`. The container
  reaches the external Postgres (`192.168.15.47:5432`) through normal host LAN
  routing; make sure the Docker host can reach it.
- **API URL** — the browser calls the backend directly via
  `NEXT_PUBLIC_API_URL=http://192.168.15.27:8000/documents` (set in
  `docker-compose.yml`, overrides `.env.local`).
- **CORS** — `http://192.168.15.27:8082` is allowed in
  `dashboard_backend/dashboard_app_be.py`.

## Changing the server IP

If the Docker host's LAN IP is not `192.168.15.27`, update it in three places:
1. `docker-compose.yml` → `NEXT_PUBLIC_API_URL`
2. `dashboard_backend/dashboard_app_be.py` → CORS `origins`
3. The URLs in this README

## Notes

- Dependencies are pinned in `requirements.txt`, generated from the project's
  `.venv`. `psycopg2` is swapped for `psycopg2-binary` (same module, no build
  toolchain needed). Your local `.venv` is untouched.
- The frontend's `node_modules` lives in an anonymous volume so the host's copy
  doesn't shadow what the image installed. If you change dependencies and they
  don't seem to take effect, recreate it:
  `docker compose down && docker compose up --build`.
