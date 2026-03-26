# Smart-Grid Control-Loop Backend

Reference implementation for a deterministic distributed energy control loop exposed under `/api/v1`.

## Service Scope
Smart-Grid ingests telemetry, builds current site state, applies rule-based optimization, dispatches commands, and computes savings snapshots.
The repository now treats the control-loop backend as canonical and retires the previous legacy platform backend.

## Documentation
- `docs/ARCHITECTURE.md`
- `docs/CONTROL_LOGIC.md`
- `docs/EDGE_GATEWAY.md`
- `docs/SIMULATION.md`
- `docs/API.md`
- `docs/AUTH.md`
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

## Run API locally (without Docker)
```bash
python -m pip install -e .
energy-api
```

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
- Device protocol metadata and point mapping schema are implemented in DB tables.
- Real Modbus transport, edge polling daemon, and MQTT broker client are not yet implemented in runtime code.

## API quick checks
- `GET /health`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/dev-token`
- `POST /api/v1/sites`
- `POST /api/v1/telemetry/ingest`
- `POST /api/v1/sites/{site_id}/optimize/run`

## Migration status
Legacy domain modules from the prior platform were retired from runtime.
See `docs/MIGRATION_NOTES.md` for the endpoint and module migration map.
