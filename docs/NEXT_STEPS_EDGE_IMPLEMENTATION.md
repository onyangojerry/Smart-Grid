# Next Steps: Edge Runtime Implementation Plan

## Objective
Implement a production-ready edge execution path that complements the current cloud control loop by adding:
- Modbus adapter
- Point-mapping decoder
- Polling loop
- Stale telemetry handling
- Reconnect/backoff
- Command reconciliation
- MQTT or direct edge messaging
- Local buffer/replay

This plan is designed to move from the current simulated transport to reliable field operation with deterministic failure behavior.

## Current baseline (already in repo)
- Cloud API and control loop exist under `/api/v1`.
- `point_mappings` table and core telemetry/control tables already exist.
- Rule safe mode is implemented when telemetry is stale/missing.
- Real edge process, Modbus transport, MQTT runtime wiring, and local buffering are not implemented yet.

## Target architecture

### New edge process
Add a standalone edge service package (recommended path):
- `src/energy_api/edge/`
  - `runner.py` (main loop coordinator)
  - `config.py` (edge config loading and validation)
  - `modbus_adapter.py` (transport + reconnect)
  - `decoder.py` (register-to-canonical point decoding)
  - `poller.py` (scheduling and collection)
  - `staleness.py` (freshness tracking and stale events)
  - `command_sync.py` (command fetch/ack reconciliation)
  - `messaging.py` (MQTT/direct API abstraction)
  - `buffer.py` (SQLite queue and replay)

### Runtime topology
1. Edge poller reads device data through Modbus adapter.
2. Decoder converts raw register values to canonical telemetry points.
3. Telemetry is sent via messaging layer (MQTT preferred, HTTP fallback).
4. On network outage, telemetry is persisted to local buffer.
5. Replay worker drains buffered telemetry when connectivity returns.
6. Command sync pulls command intents, applies locally, publishes acknowledgements.

## Phased implementation

## Phase 1: Modbus adapter
### Scope
Implement robust Modbus TCP client wrapper for read operations and command write operations.

### Deliverables
- Connection lifecycle (`connect`, `disconnect`, `is_connected`).
- Read APIs:
  - `read_holding_registers(address, count, unit_id)`
  - `read_input_registers(address, count, unit_id)`
  - optional coil/discrete read support.
- Write APIs for command execution:
  - `write_single_register`
  - `write_multiple_registers`
- Structured error model (timeout, connection error, CRC/protocol error).

### Acceptance criteria
- Adapter reconnects successfully after cable pull / endpoint restart.
- Read timeout and retry behavior is deterministic and bounded.
- All failures include machine-parseable error codes.

## Phase 2: Point-mapping decoder
### Scope
Decode raw register blocks using mappings in `point_mappings` into canonical telemetry keys.

### Mapping contract (extend current data model)
Current columns exist; consider adding:
- `register_address` (int)
- `register_count` (int)
- `function_code` (enum: input/holding/coil/discrete)
- `signed` (bool)
- `bit_offset` / `bit_length` (optional)
- `endianness_profile` (optional normalized enum)

### Decoder behavior
- Supports int16/int32/uint16/uint32/float32 first.
- Applies `scale_factor` after numeric conversion.
- Applies byte order + word order exactly as mapping specifies.
- Produces normalized point:
  - `canonical_key`
  - `value`
  - `unit`
  - `quality`
  - `ts`

### Acceptance criteria
- Golden tests for each numeric type and endianness combination pass.
- Invalid mappings fail fast with actionable diagnostics.
- Decoder never crashes process on malformed single point; marks point `quality=suspect`.

## Phase 3: Polling loop
### Scope
Implement deterministic per-device polling scheduler.

### Design
- Device-level schedule from `devices.polling_interval_seconds`.
- Jitter (small random offset) to avoid synchronized bursts.
- Single-flight guard per device (no overlapping poll cycle).
- Batching by device and function code to minimize round-trips.

### Output behavior
- Emits telemetry batches in canonical format.
- Emits internal health metrics:
  - poll duration
  - points read
  - decode errors
  - timeout count

### Acceptance criteria
- Poll loop keeps target cadence within tolerance (e.g., ±10%).
- Slow device does not block other devices.
- Poll loop shutdown is graceful and lossless for in-flight data.

## Phase 4: Stale telemetry handling
### Scope
Add explicit freshness state at edge before cloud ingestion checks.

### Behavior
- Track last successful point timestamp per canonical key.
- Mark key stale when age > `2 * polling_interval` (or policy override).
- Emit stale event telemetry/alerts channel.
- For critical keys, propagate `online=false` signal to cloud path.

### Acceptance criteria
- Staleness transition is edge-triggered (no noisy repeated alerts).
- Recovery transition is emitted when fresh data resumes.
- Critical stale keys lead to cloud safe mode via existing rule path.

## Phase 5: Reconnect/backoff
### Scope
Implement robust retry policy across Modbus and upstream messaging.

### Strategy
- Exponential backoff with jitter.
- Separate policies for:
  - device transport retries
  - cloud publish retries
- Circuit-breaker style cooldown after repeated hard failures.

### Suggested defaults
- base delay: 0.5s
- multiplier: 2.0
- max delay: 30s
- max attempts before cooldown: 8
- cooldown: 60s

### Acceptance criteria
- No tight retry loops under prolonged outages.
- Recovery latency after outage remains acceptable.
- Backoff state is observable via logs/metrics.

## Phase 6: Command reconciliation
### Scope
Guarantee command lifecycle correctness between cloud intent and edge execution.

### Reconciliation model
- Cloud command states: `queued -> sent -> acked|failed`.
- Edge command state machine:
  - fetched
  - validated
  - applied
  - ack_published / fail_published
- Idempotency by `command_id` + optional `idempotency_key`.
- Local command journal to prevent duplicate application after restart.

### Edge responsibilities
- Pull/subscribe for new commands.
- Verify device readiness and command constraints.
- Apply command once.
- Publish ack/failure with reason and timestamp.

### Acceptance criteria
- Duplicate command delivery does not duplicate device writes.
- Every fetched command converges to ack or fail state.
- Failure reasons are standardized and actionable.

## Phase 7: Messaging mode (MQTT or direct)
### Scope
Implement pluggable transport for edge-cloud communication.

### Interface
Define `EdgeMessagingClient` abstraction:
- `publish_telemetry(batch)`
- `publish_command_ack(ack)`
- `fetch_commands()` or `subscribe_commands(handler)`
- `health()`

### Mode A: MQTT (preferred for field)
Topics:
- `ems/{site_id}/telemetry/{canonical_key}`
- `ems/{site_id}/state/current`
- `ems/{site_id}/command/ack`
- `ems/{site_id}/alerts/device_fault`

QoS recommendations:
- Telemetry: QoS 1
- Command ack/fail: QoS 1 (or QoS 2 if required)

### Mode B: Direct API fallback
- Use existing `/api/v1/telemetry/ingest` for telemetry.
- Add/extend command endpoints for edge pull/ack if needed.

### Acceptance criteria
- Same internal edge flow works with either messaging mode.
- Mode can be switched by config without code changes.

## Phase 8: Local buffer and replay
### Scope
Implement durable local queue for offline operation.

### SQLite schema (minimum)
- `telemetry_buffer`
  - `id`
  - `site_id`
  - `payload_json`
  - `created_at`
  - `attempt_count`
  - `next_attempt_at`
- `command_journal`
  - `command_id`
  - `status`
  - `applied_at`
  - `ack_sent_at`

### Replay policy
- FIFO by `created_at`.
- Backpressure limit (`max_rows`, disk cap).
- Retry with backoff on publish failure.
- Poison-message policy after N failures (quarantine table/log).

### Acceptance criteria
- No telemetry loss across process restart during outage window.
- Replay preserves ordering per site/device.
- Buffer drains automatically after connectivity restoration.

## Cross-cutting requirements

## Observability
Add structured metrics/logging for:
- device connectivity
- poll latency and success rate
- decode error rate
- stale key counts
- buffered row count and replay lag
- command ack latency

## Security
- Store edge credentials outside code (env/secret file).
- TLS for MQTT/HTTP where applicable.
- Optional message signing for command channels.
- Audit command execution outcomes.

## Configuration
Introduce edge config profile with:
- site/device identity
- transport mode (`mqtt|http`)
- retry/backoff settings
- buffer limits
- polling interval overrides

## Testing strategy

## Unit tests
- decoder numeric and endianness matrix
- backoff scheduler behavior
- stale detector transitions
- command idempotency logic

## Integration tests
- simulated Modbus server read/write flows
- network outage + reconnect + replay
- duplicate command delivery
- MQTT and direct mode parity

## Field validation checklist
- cold start with empty cache
- gateway restart under outage
- intermittent Wi-Fi behavior
- device reboot mid-command

## Rollout plan
1. Implement edge service with direct HTTP publish first (simpler debug path).
2. Add SQLite buffering and replay.
3. Add command reconciliation end-to-end.
4. Add MQTT mode behind config flag.
5. Run pilot on one site with aggressive observability.
6. Gradually expand to additional sites.

## Definition of done
- Edge process runs continuously with no manual intervention in a 7-day soak test.
- Telemetry delivery success > 99.9% with replay enabled.
- No duplicate command application in fault-injection tests.
- Documented runbook for outage recovery and troubleshooting.

## Suggested immediate tasks (next sprint)
- Create `src/energy_api/edge/` package scaffold.
- Implement `modbus_adapter.py` + `decoder.py` with unit tests.
- Implement `poller.py` and send batches to `/api/v1/telemetry/ingest`.
- Add `buffer.py` SQLite persistence and replay worker.
- Add basic command fetch/apply/ack path with idempotency journal.
