<!-- /Users/loan/Desktop/energyallocation/docs/EDGE_GATEWAY.md -->
# Edge Gateway

## Current state
- Dedicated edge gateway process in repository: NOT IMPLEMENTED.
- Cloud-side control loop API exists in `src/energy_api/routers/control_loop.py`.

## Device adapter configuration
- Device metadata persisted in `devices.metadata` JSONB.
- No standalone edge adapter config loader module yet.

## Supported protocols (current)
- Protocol field exists in schema (`devices.protocol`, default `modbus_tcp`).
- Actual Modbus transport implementation: NOT IMPLEMENTED.
- Actual MQTT client implementation: NOT IMPLEMENTED.

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
- Edge polling loop service: NOT IMPLEMENTED.
- Staleness handling currently occurs in cloud state engine using timestamp age check.

## Fail-safe mode behavior
- Implemented in `RuleEngine.evaluate`:
  - If telemetry/device not online -> `idle` decision.
  - If over-temperature -> `idle` decision.

## MQTT topics and QoS
Current code publishes only simulated metadata for command request topic:
- `ems/{site_id}/command/request` (simulated QoS 1 metadata in response).

Other topic handlers are NOT IMPLEMENTED:
- `ems/{site_id}/telemetry/{canonical_key}`
- `ems/{site_id}/state/current`
- `ems/{site_id}/policy/active`
- `ems/{site_id}/command/ack`
- `ems/{site_id}/alerts/device_fault`

## Local buffer schema and replay
- Local SQLite buffer and replay logic: NOT IMPLEMENTED.
