# Hardware Integration

## Safety Baseline

- Modbus TCP must remain on LAN/VPN/protected network.
- Do not expose Modbus TCP directly to the public internet.
- Use EDGE_DEVICE_ENABLED, EDGE_READ_ONLY_MODE, and EDGE_OBSERVATION_ONLY_MODE for staged rollout.

## Victron GX Strategy

Profile: victron_gx_home_bess

- Prefer Unit ID 100 unless deployment requires override.
- Use GX as integration hub for system-level and connected-device values.
- Register maps must be sourced from official Victron GX Modbus-TCP register list.
- Start in observation-only mode, then enable writes only when command paths are validated.

## SMA SunSpec Strategy

Profile: sma_sunspec_home_bess

- Require explicit product-family register map.
- Modbus on SMA devices is often disabled by default and must be enabled during commissioning.
- Prefer SunSpec where supported.
- Keep write capabilities disabled unless product-family docs confirm support and tests pass.

## Runtime Controls

Environment variables:

- EDGE_DEVICE_PROFILE
- EDGE_PROFILE_REGISTER_MAP_PATH
- EDGE_DEVICE_ENABLED
- EDGE_READ_ONLY_MODE
- EDGE_OBSERVATION_ONLY_MODE
- EDGE_MODBUS_UNIT_ID (optional explicit value, guarded)
- EDGE_ALLOW_PROFILE_UNIT_ID_OVERRIDE

## Config Precedence

Unit ID resolution:

1. Profile default unit ID (single source of truth).
2. EDGE_MODBUS_UNIT_ID if provided and equal to profile default.
3. EDGE_MODBUS_UNIT_ID different from profile default only when EDGE_ALLOW_PROFILE_UNIT_ID_OVERRIDE=true.
4. Otherwise startup fails fast with a mismatch error.

## Startup Mismatch Protection

- Profiles are validated on load. Invalid profiles, including incomplete scaffolds, fail before runtime control starts.
- Runtime fails fast if profile validation fails for non-simulated profiles.
- Runtime fails fast on Unit ID mismatch unless explicit override gate is enabled.
- Runtime fails fast when both read-only and observation-only are enabled simultaneously.
- Runtime fails fast when write-enabled mode is requested for a profile that does not support writes.

## Onboarding Path

1. Start with simulated_home_bess profile.
2. Move real profile to observation-only mode.
3. Verify telemetry quality, staleness, and alarms.
4. Enable read-only mode with command verification checks.
5. Enable write mode only after reconciliation tests are green.
