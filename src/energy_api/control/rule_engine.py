# Author: Jerry Onyango
# Contribution: Evaluates control policies against site state to choose scored actions and human-readable explanations.

# /Users/loan/Desktop/energyallocation/src/energy_api/control/rule_engine.py
from __future__ import annotations

from datetime import UTC, datetime

from .battery_policy import BatteryPolicyConfig, BatteryPolicyEngine
from .models import ScoredAction, SiteState
from .tariff import build_tariff_state


class RuleEngine:
    def __init__(self) -> None:
        self.policy_engine = BatteryPolicyEngine()

    def evaluate(self, state: SiteState, policy: dict[str, object], forecast_peak: bool = False) -> ScoredAction:
        now = state.ts if state.ts.tzinfo else datetime.now(UTC)
        tariff = build_tariff_state(
            ts=now,
            policy=policy,
            default_import=state.price_import,
            default_export=state.price_export,
        )
        if forecast_peak and not tariff.is_peak:
            tariff = tariff.__class__(
                import_price=tariff.import_price,
                export_price=tariff.export_price,
                is_peak=True,
                is_shoulder=tariff.is_shoulder,
                tariff_name="forecast_peak",
            )

        config = BatteryPolicyConfig(
            soc_reserve_hard=float(policy.get("soc_reserve_hard", 15.0)),
            soc_reserve_normal=float(policy.get("soc_reserve_normal", policy.get("reserve_soc_min", 20.0))),
            soc_target_offpeak=float(policy.get("soc_target_offpeak", 85.0)),
            soc_max=float(policy.get("soc_max", 95.0)),
            minimum_action_duration=int(policy.get("minimum_action_duration", 300)),
            minimum_direction_change_gap=int(policy.get("minimum_direction_change_gap", 600)),
            verification_timeout=int(policy.get("verification_timeout", 30)),
            battery_power_limit_kw=float(policy.get("battery_power_limit_kw", policy.get("max_discharge_kw", 3.0))),
            battery_temp_max_c=float(policy.get("battery_temp_max_c", 45.0)),
            battery_temp_derate_start_c=float(policy.get("battery_temp_derate_start_c", 40.0)),
            stale_critical=bool(policy.get("stale_critical", False)),
            active_alarm=bool(policy.get("active_alarm", False)),
            active_fault=bool(policy.get("active_fault", False)),
            unresolved_critical_command=bool(policy.get("unresolved_critical_command", False)),
        )

        return self.policy_engine.decide(state=state, tariff=tariff, config=config, now=now)
