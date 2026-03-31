<!-- /Users/loan/Desktop/energyallocation/docs/EDGE_GATEWAY.md -->
# Edge Gateway

## Current state
- Edge runtime modules exist in `src/energy_api/edge/` (adapter, decoder, poller, staleness, replay, command execution, runtime orchestration, SQLite storage).
- Cloud-side control loop API exists in `src/energy_api/routers/control_loop.py`.
- Gateway and point-mapping API surface exists in `src/energy_api/routers/edge.py`.
- Canonical edge service entrypoint exists: `energy-edge` (`src/energy_api/edge/main.py`).
- Runtime supervision is handled by `EdgeRuntimeSupervisor` (`src/energy_api/edge/supervisor.py`).

## Device adapter configuration
- Device metadata persisted in `devices.metadata` JSONB.
- Core adapter behavior is implemented (`src/energy_api/edge/modbus_adapter.py`).
- Config/deployment profile hardening remains pending for production rollouts.

## Supported protocols (current)
- Protocol field exists in schema (`devices.protocol`, default `modbus_tcp`).
- Modbus transport implementation exists in edge runtime modules.
- MQTT client/runtime transport wiring remains pending.

## Modbus register map format (current data model)
`point_mappings` columns:
- `device_id`
- `source_key`
- `canonical_key`
- `value_type`
- `scale_factor`
- `byte_order`
- `word_order`

## Polling loop design
- Edge polling module is implemented in `src/energy_api/edge/poller.py`.
- Edge staleness tracking module is implemented in `src/energy_api/edge/staleness.py`.
- Cloud state engine still enforces safe-mode behavior when telemetry is stale/missing.

## Runtime orchestration and status
- `EdgeRuntimeSupervisor` is the single orchestrator for startup recovery, poll/replay cadence, command backlog processing, and shutdown sequencing.
- Runtime emits structured status logs (`edge_runtime_status`) and writes a status JSON snapshot (`EDGE_STATUS_FILE`).
- Status snapshot includes service start state, runtime mode, active device count, last poll/replay times, unresolved command count, queue depth, and fault/degraded indicators.

## Fail-safe mode behavior
- Implemented in `RuleEngine.evaluate`:
  - If telemetry/device not online -> `idle` decision.
  - If over-temperature -> `idle` decision.

## MQTT topics and QoS
Current code still uses simulated metadata for command request topic in cloud dispatch responses:
- `ems/{site_id}/command/request` (simulated QoS 1 metadata in response).

Other runtime topic handlers remain pending for production messaging:
- `ems/{site_id}/telemetry/{canonical_key}`
- `ems/{site_id}/state/current`
- `ems/{site_id}/policy/active`
- `ems/{site_id}/command/ack`
- `ems/{site_id}/alerts/device_fault`

## Local buffer schema and replay
- Local SQLite buffer and replay logic are implemented in `src/energy_api/edge/storage/sqlite.py` and `src/energy_api/edge/replay.py`.
- SQLite runtime state is persisted for service restarts and startup recovery.
- Compose/local ingest auth is wired via service keys (`EDGE_API_KEY` -> `X-API-Key`, validated against `EA_SERVICE_KEYS`).
- Remaining work is operational validation under prolonged outages.
