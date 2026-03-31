# Modbus Register Maps

## RegisterPoint Schema

Each telemetry mapping is represented by RegisterPoint:

- profile_name
- register_type: holding | input | coil
- address
- count
- data_type: uint16 | int16 | uint32 | int32 | float32
- scale_factor
- byte_order
- word_order
- access: read | write | read_write
- canonical_key
- poll_group: fast | medium | slow | verify
- critical
- tolerance
- verify_address (optional)
- transform (optional)

## CommandPoint Schema

Each write path is represented by CommandPoint:

- canonical_command
- write_address
- write_type
- value_encoding: signed_scale | uint16 | enum
- verify_address
- verify_mode: readback_equals | observed_positive | observed_negative | observed_near_zero | mode_equals
- tolerance
- supports_readback

## Poll Groups

- fast (2-5s): battery power, site load, grid import/export, pv generation, inverter mode, alarm/fault
- medium (10-30s): battery SOC, battery voltage/current, battery temperature
- slow (1-5m): daily/cumulative counters and diagnostics
- verify (on demand): post-write verification reads

The poller consumes profile config only. Vendor addresses are not hardcoded in poller logic.

## Decoding Rules

- data_type drives integer/float unpacking
- byte_order and word_order are applied before decoding
- scale_factor is applied after decoding
- quality and staleness are emitted per point

## Verification Rules

- charge_setpoint_kw: readback or observed positive battery power
- discharge_setpoint_kw: readback or observed negative battery power
- idle: readback neutral mode or near-zero battery power
- set_mode: mode register readback
- set_grid_limit_kw: grid limit register readback
