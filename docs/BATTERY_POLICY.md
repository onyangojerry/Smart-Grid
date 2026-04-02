# Battery Policy

Battery control is implemented as a layered policy under src/energy_api/control/battery_policy.py.

## Layer 1: Hard Safety

Always block control actions when:

- telemetry is stale or device is offline
- active alarm or active fault is present
- battery temperature is above safety max
- SOC is below hard reserve for discharge conditions
- unresolved critical command exists within reconciliation window

## Layer 2: Asset Protection

Implemented protections:

- SOC reserve and SOC max boundaries
- direction-change gap blocks reversals only; same-direction continuation is allowed
- minimum action window via policy timing fields keeps the current direction active until the window elapses
- temperature derating above derate threshold
- power cap enforcement

## Layer 3: Economic Control

Policy chooses among:

- charge_setpoint_kw on PV surplus
- discharge_setpoint_kw on peak/high-cost intervals
- off-peak charging up to target SOC
- idle under uncertainty or weak economics

## Required Thresholds

Configurable policy keys:

- soc_reserve_hard
- soc_reserve_normal
- soc_target_offpeak
- soc_max
- minimum_action_duration
- minimum_direction_change_gap
- verification_timeout
- battery_power_limit_kw

## Tariff Interaction

Tariff state includes:

- import_price
- export_price
- is_peak
- is_shoulder
- tariff_name

Supported v1 tariff models:

- flat
- time-of-use
- export credit
