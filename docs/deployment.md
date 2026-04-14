# Deployment Guide

## Local production-like stack
Use Docker Compose:

```bash
docker compose up --build
```

Services:
- `postgres` on `localhost:5432`
- `api` on `localhost:8000`
- `ui` on `localhost:5173`
- `modbus-sim` on `localhost:15020` (optional simulation target)
- `edge-runtime` (edge service process)

## Environment configuration
Copy and customize:
- `.env.example`

Critical variables:
- `EA_JWT_SECRET`
- `EA_SERVICE_KEYS`
- `EA_DATABASE_URL`
- `EA_COMMAND_MAX_RETRIES`
- `EA_PENDING_ACK_BLOCK_SECONDS`
- `VITE_API_URL` or `VITE_API_BASE_URL` (frontend-to-backend base URL, defaults to `http://localhost:8000`)
- `EDGE_SITE_ID`
- `EDGE_GATEWAY_ID`
- `EDGE_MODBUS_HOST`
- `EDGE_MODBUS_PORT`
- `EA_API_BASE_URL`
- `EDGE_API_KEY` (preferred edge ingest service key; sent as `X-API-Key`)
- `EDGE_API_BEARER_TOKEN` (optional bearer token for authenticated ingest)
- `EDGE_SQLITE_PATH`
- `EDGE_STATUS_FILE`

## Compose edge ingest auth model
- API telemetry ingest endpoint remains protected by role authorization.
- Edge runtime authenticates to API using `X-API-Key` when `EDGE_API_KEY` is set.
- Compose default aligns `EDGE_API_KEY=ops-key` with the default `EA_SERVICE_KEYS` entry (`ops-key:svc_ops:ops_admin:`).
- Deterministic precedence in edge runtime: API key is primary; bearer is fallback only when `EDGE_API_KEY` is absent.
- `EDGE_API_BEARER_TOKEN` remains supported for JWT-based auth fallback when desired.

## Edge runtime startup
Canonical entrypoint:

```bash
energy-edge
```

Runtime supervisor behavior:
- runs startup recovery before polling
- executes poll + replay cycle continuously
- executes command backlog reconciliation cycle
- emits structured status logs (`edge_runtime_status`)
- writes status file JSON (`EDGE_STATUS_FILE`)
- handles SIGINT/SIGTERM for graceful shutdown

## Docker services for edge runtime
`docker-compose.yml` includes:
- `modbus-sim`: simulated Modbus TCP server (`energy-edge-sim`)
- `edge-runtime`: edge service (`energy-edge`)

Persistent local state:
- volume `edge_data` mounted to `/app/data/edge`
- SQLite file and status snapshot are stored in this mount

Quick validation:

```bash
docker compose up -d modbus-sim edge-runtime
docker compose ps modbus-sim edge-runtime
docker compose logs --tail 50 edge-runtime
docker compose down
```

## Database initialization
- `db/migrations/0001_init_schema.sql` initializes schema.
- `db/migrations/0002_rls_policies.sql` configures RLS baseline.
- `db/migrations/0004_control_loop_schema.sql` initializes control-loop runtime tables.

## Preflight checks
- `.venv/bin/python scripts/check_file_headers.py`
- `cd ui && npm run build`

## Production checklist
- move secrets to vault/KMS
- run migrations via controlled release process
- enable HTTPS and OAuth2 provider integration
- centralize logs and metrics (request_id, tenant_id, actor_id, latency)
- add backups and recovery policy for Postgres
