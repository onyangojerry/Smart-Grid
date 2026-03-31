<!-- /Users/loan/Desktop/energyallocation/docs/CONTROL_LOGIC.md -->
# Control Logic

## Rule cases (implemented pseudocode)
```text
if online == false or battery_temp_c > battery_temp_max_c:
  action = idle  # safe mode

elif pv_kw > load_kw and battery_soc < 100:
  action = charge(min(max_charge_kw, pv_kw - load_kw))

elif price_import >= high_price_threshold and battery_soc > reserve_soc_min:
  action = discharge(min(max_discharge_kw, load_kw))

elif price_import <= low_price_threshold and forecast_peak == true and battery_soc < 95:
  action = charge(min(max_charge_kw, 2.0))

else:
  action = idle
```

## Scoring function (implemented)
For each candidate action, score terms are computed in `RuleEngine._score`:
- `energy_cost`
- `battery_degradation_penalty`
- `reserve_violation_penalty`
- `command_churn_penalty`
- `device_safety_penalty`

Total score is sum of all terms via `ScoreBreakdown.total`.

## Action set
- Implemented canonical command types: `charge_setpoint_kw`, `discharge_setpoint_kw`, `idle`, `set_mode`, `set_grid_limit_kw`, `set_export_limit_kw`.
- Legacy aliases still accepted in execution paths for compatibility: `charge`, `discharge`, `set_limit`.
- Direct power targets are accepted by `/api/v1/sites/{site_id}/commands`.
- Savings/reporting v1 mapping: charge/discharge groups are economically modeled; `idle`, `set_mode`, and grid/export limit groups are baseline-neutral but counted in taxonomy reporting.

## Hard constraints before dispatch
- Safe mode when `online=False`.
- Safe mode when `battery_temp_c > battery_temp_max_c`.
- Block command when unacknowledged command exists inside ack block window.

## Explanation payload schema (implemented)
```json
{
  "decision": "discharge",
  "target_power_kw": 2.0,
  "top_factors": [
    {"factor": "import_price", "value": 0.34, "effect": "high"},
    {"factor": "battery_soc", "value": 64.0, "effect": "enough_reserve"}
  ],
  "summary": "Discharging battery to reduce expensive grid imports while protecting reserve."
}
```
Explanation is produced inside `RuleEngine.evaluate` before dispatcher call.
