# Data Model and Migrations (Current)

## Source of truth
- Base schema and policy migrations:
  - `db/migrations/0001_init_schema.sql`
  - `db/migrations/0002_rls_policies.sql`
  - `db/migrations/0003_app_state_store.sql`
- Control-loop schema migration:
  - `db/migrations/0004_control_loop_schema.sql`

## Active runtime entities
Current control-loop runtime persists:
- `sites`, `assets`, `devices`
- `telemetry_streams`, `telemetry_points`, `point_mappings`
- `control_policies`, `tariffs`
- `optimization_runs`, `commands`, `savings_snapshots`

## Data integrity posture
- Primary and foreign keys across site/device/run data.
- Dedupe protection for telemetry points on `(stream_id, ts)`.
- Command idempotency support via `(site_id, idempotency_key)` uniqueness.
- Time-series index for telemetry query efficiency.
- The control repository no longer creates tables at runtime; schema presence is validated against the migration-managed database before use.

## Migration strategy
- Keep migrations append-only.
- Add new migrations for schema evolution.
- Run migrations in CI/staging before production rollout.

## Legacy note
Legacy domain tables referenced by prior platform versions are historical and documented in `docs/HISTORICAL_APPENDIX.md`.
