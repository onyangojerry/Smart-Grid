# Device Profiles

This repository now uses a profile-driven device layer for edge integrations.

## Canonical Internal Model

All device telemetry is normalized into canonical keys:

- site_load_kw
- pv_generation_kw
- battery_soc
- battery_power_kw
- grid_import_kw
- grid_export_kw
- battery_voltage_v
- battery_current_a
- battery_temp_c
- inverter_mode
- alarm_code
- device_online
- device_fault

All control commands are normalized into canonical command names:

- idle
- charge_setpoint_kw
- discharge_setpoint_kw
- set_mode
- set_grid_limit_kw
- set_export_limit_kw

Vendor-native register names remain below the profile layer.

## Profile System

Profiles are defined in src/energy_api/edge/device_profiles.py using:

- DeviceProfile
- RegisterPoint (alias PointMapping)
- CommandPoint

Supported profile identifiers:

- simulated_home_bess
- victron_gx_home_bess
- sma_sunspec_home_bess
- sma_native_modbus_home_bess (scaffold)

## Victron GX

- Default Unit ID is 100 in this profile.
- Register points must be loaded from official Victron GX Modbus-TCP register list.
- v1 profile ships as read-only until explicit write mappings are supplied by deployment config.

## SMA SunSpec

- Register support is product-family specific.
- Modbus must be enabled on target hardware before operation.
- v1 profile is scaffolded and requires deployment-provided register maps.

## Adding a New Vendor Profile

1. Add or load RegisterPoint mappings.
2. Add CommandPoint entries only for verified writable paths.
3. Keep command capabilities explicit (unsupported by default).
4. Validate with validate_profile before enabling device control.
5. Run observation-only mode before write-enabled mode.
