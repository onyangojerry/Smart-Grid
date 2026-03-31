# Smart-Grid Control-Loop Backend

Reference implementation for a deterministic distributed energy control loop exposed under `/api/v1`.

## Service Scope
Smart-Grid ingests telemetry, builds current site state, applies rule-based optimization, dispatches commands, and computes savings snapshots.
The repository now treats the control-loop backend as canonical and retires the previous legacy platform backend.

## Documentation
- `docs/ARCHITECTURE.md`
- `docs/CONTROL_LOGIC.md`
- `docs/EDGE_GATEWAY.md`
- `docs/DEVICE_PROFILES.md`
- `docs/MODBUS_REGISTER_MAPS.md`
- `docs/BATTERY_POLICY.md`
- `docs/HARDWARE_INTEGRATION.md`
- `docs/SIMULATION.md`
- `docs/API.md`
- `docs/AUTH.md`
- `docs/data-engineering.md`
- `docs/MIGRATION_NOTES.md`

## Key Assets
- Migrations: `db/migrations/`
- Backend source: `src/energy_api/`
- Control modules: `src/energy_api/control/`
- Simulation engine: `src/energy_api/simulation/`
- Frontend source: `ui/`

## Prerequisites
- Python `>=3.11`
- Node.js `>=20`
- Docker + Docker Compose (for full stack)

## Environment setup
1. Copy or edit `.env.example`.
2. Ensure `EA_DATABASE_URL` points to a running Postgres.

## Run with docker-compose
```bash
docker compose up --build
```

Services:
- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- UI: `http://localhost:5173`
- Edge runtime service: `edge-runtime` (writes status JSON to `/app/data/edge/status.json` in container)
- Simulated Modbus device: `modbus-sim` on `localhost:15020`

## Run API locally (without Docker)
```bash
python -m pip install -e .
energy-api
```

## Run edge runtime locally (canonical service entrypoint)
```bash
python -m pip install -e .
energy-edge
```

Common local environment variables for edge runtime:
- `EDGE_SITE_ID` (default `site_001`)
- `EDGE_GATEWAY_ID` (default `gw_edge_01`)
- `EDGE_DEVICE_PROFILE` (`simulated_home_bess`, `victron_gx_home_bess`, `sma_sunspec_home_bess`)
- `EDGE_PROFILE_REGISTER_MAP_PATH` (JSON register map file for vendor profiles)
- `EDGE_DEVICE_ENABLED` / `EDGE_READ_ONLY_MODE` / `EDGE_OBSERVATION_ONLY_MODE`
- `EDGE_MODBUS_HOST` / `EDGE_MODBUS_PORT` (default `127.0.0.1:15020`)
- `EDGE_MODBUS_UNIT_ID` (optional explicit value; strict mismatch checks apply)
- `EDGE_ALLOW_PROFILE_UNIT_ID_OVERRIDE` (default `false`; required when overriding profile default unit ID)
- `EA_API_BASE_URL` (default `http://localhost:8000`)
- `EDGE_API_BEARER_TOKEN` (optional bearer token for authenticated ingest)
- `EDGE_SQLITE_PATH` (default `./data/edge/edge_runtime.db`)
- `EDGE_STATUS_FILE` (default `./data/edge/status.json`)

Run simulated Modbus locally:
```bash
energy-edge-sim
```

Suggested startup order for local service validation:
1. `energy-api`
2. `energy-edge-sim`
3. `energy-edge`

Health/status visibility:
- Runtime status snapshots are emitted in logs as `edge_runtime_status`.
- Runtime status file is written to `EDGE_STATUS_FILE`.
- Status includes service start, mode, active devices, last poll/replay times, command backlog, queue depth, and fault/degraded state.

Hardware profile onboarding:
1. Simulated: `EDGE_DEVICE_PROFILE=simulated_home_bess`
2. Victron GX: `EDGE_DEVICE_PROFILE=victron_gx_home_bess` + `EDGE_PROFILE_REGISTER_MAP_PATH=/path/to/victron_registers.json`
3. SMA SunSpec: `EDGE_DEVICE_PROFILE=sma_sunspec_home_bess` + `EDGE_PROFILE_REGISTER_MAP_PATH=/path/to/sma_sunspec_registers.json`
4. Start with `EDGE_OBSERVATION_ONLY_MODE=true`, then disable after validation.

Vendor notes:
- Victron GX integrations should prefer Unit ID 100 unless commissioning requires override.
- SMA register support is product-family specific; Modbus must be enabled on the target device.
- Modbus TCP is a local/protected network interface and must not be exposed directly to the public internet.

Configuration precedence and startup safety:
1. Load selected profile from `EDGE_DEVICE_PROFILE` (+ optional `EDGE_PROFILE_REGISTER_MAP_PATH`).
2. Resolve Unit ID from profile default.
3. If `EDGE_MODBUS_UNIT_ID` is set:
	- allowed when equal to profile default
	- allowed when different only if `EDGE_ALLOW_PROFILE_UNIT_ID_OVERRIDE=true`
	- otherwise startup fails fast with a clear mismatch error.
4. Startup also fails fast on dangerous mode combinations (for example `EDGE_READ_ONLY_MODE=true` with `EDGE_OBSERVATION_ONLY_MODE=true`) and when write mode is requested for a read-only profile.

## Run UI locally
```bash
cd ui
npm install
npm run dev
```

## Run a local simulation (no hardware)
Use either:
- HTTP: `POST /api/v1/sites/{site_id}/simulation/run`
- Python import: `from energy_api.simulation import run_simulation, SimulatedSite`

## Connect a real device
Current repository state:
- Implemented in code: Modbus TCP adapter, point decoder, poller, staleness tracking, replay/backoff, command execution/reconciliation, and SQLite-backed edge storage under `src/energy_api/edge/`.
- Implemented in API/data model: gateway and point-mapping endpoints plus edge metadata tables.
- Remaining blockers for field deployment: production messaging transport strategy (MQTT or hardened HTTP path), token provisioning strategy for authenticated ingest, and long-duration operational hardening/runbooks.

## Edge runtime status (March 2026)
- Edge modules are present and tested (unit/integration style tests in `tests/edge/`).
- Demo flow exists for simulated Modbus polling (`scripts/edge_poll_demo.py`).
- Canonical edge service startup entrypoint is `energy-edge` (`energy_api.edge.main:run`).
- Runtime supervisor (`EdgeRuntimeSupervisor`) owns startup recovery, poll cycle, replay/sync, command backlog processing, status emission, and graceful shutdown.
- API process remains separate from edge runtime process by design.

## API quick checks
Health and authentication:
- `GET /health`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/dev-token`

Site, devices, and telemetry:
- `POST /api/v1/sites`
- `GET /api/v1/sites`
- `POST /api/v1/telemetry/ingest`
- `GET /api/v1/sites/{site_id}/telemetry/latest`

Optimization and commands:
- `POST /api/v1/sites/{site_id}/optimize/run`
- `GET /api/v1/sites/{site_id}/optimize/runs`
- `POST /api/v1/sites/{site_id}/commands`
- `GET /api/v1/sites/{site_id}/savings/summary`

Alerts:
- `POST /api/v1/sites/{site_id}/alerts`
- `GET /api/v1/sites/{site_id}/alerts`
- `PATCH /api/v1/alerts/{alert_id}/acknowledge`

Edge (gateways and point mappings):
- `POST /api/v1/sites/{site_id}/gateways`
- `GET /api/v1/sites/{site_id}/edge/health`

ROI calculator:
- `POST /api/v1/sites/{site_id}/roi/calculate`
- `POST /api/v1/sites/{site_id}/roi/scenarios`

Users and management:
- `GET /api/v1/users`
- `POST /api/v1/users/invite`

## Migration status
Legacy domain modules from the prior platform were retired from runtime.
See `docs/MIGRATION_NOTES.md` for the endpoint and module migration map.
