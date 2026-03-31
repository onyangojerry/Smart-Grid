# Author: Jerry Onyango
# Contribution: Provides production battery policy with layered safety, asset protection, and tariff-aware economic decisions.
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from .models import ScoreBreakdown, ScoredAction, SiteState
from .tariff import TariffState


@dataclass
class BatteryPolicyConfig:
    soc_reserve_hard: float = 15.0
    soc_reserve_normal: float = 20.0
    soc_target_offpeak: float = 85.0
    soc_max: float = 95.0
    minimum_action_duration: int = 300
    minimum_direction_change_gap: int = 600
    verification_timeout: int = 30
    battery_power_limit_kw: float = 3.0
    battery_temp_max_c: float = 45.0
    battery_temp_derate_start_c: float = 40.0
    stale_critical: bool = False
    active_alarm: bool = False
    active_fault: bool = False
    unresolved_critical_command: bool = False


class BatteryPolicyEngine:
    def __init__(self) -> None:
        self._last_action: str = "idle"
        self._last_action_ts: datetime | None = None

    def decide(
        self,
        state: SiteState,
        tariff: TariffState,
        config: BatteryPolicyConfig,
        now: datetime,
    ) -> ScoredAction:
        if self._fails_hard_safety(state, config):
            return self._result("idle", 0.0, "hard_safety_block", state, tariff)

        if config.unresolved_critical_command:
            return self._result("idle", 0.0, "unresolved_command_block", state, tariff)

        direction_locked = self._direction_lock_active(now, config.minimum_direction_change_gap)
        if direction_locked:
            return self._result("idle", 0.0, "direction_change_gap", state, tariff)

        if state.pv_kw > state.load_kw and state.battery_soc < config.soc_max:
            pv_surplus = max(0.0, state.pv_kw - state.load_kw)
            target = min(self._derated_limit(state, config), pv_surplus)
            if target > 0.0:
                return self._result("charge_setpoint_kw", target, "pv_surplus_charge", state, tariff)

        if tariff.is_peak and state.battery_soc > config.soc_reserve_normal:
            target = min(self._derated_limit(state, config), max(0.0, state.load_kw))
            if target > 0.0:
                return self._result("discharge_setpoint_kw", target, "peak_discharge", state, tariff)

        if (not tariff.is_peak) and (tariff.import_price <= 0.12) and state.battery_soc < config.soc_target_offpeak:
            target = min(self._derated_limit(state, config), max(0.0, config.soc_target_offpeak - state.battery_soc) / 10.0)
            if target > 0.0:
                return self._result("charge_setpoint_kw", target, "offpeak_charge", state, tariff)

        if state.battery_soc <= config.soc_reserve_hard:
            return self._result("idle", 0.0, "soc_reserve_protection", state, tariff)

        return self._result("idle", 0.0, "economic_idle", state, tariff)

    def _fails_hard_safety(self, state: SiteState, config: BatteryPolicyConfig) -> bool:
        if not state.online:
            return True
        if config.stale_critical:
            return True
        if config.active_alarm or config.active_fault:
            return True
        if state.battery_temp_c >= config.battery_temp_max_c:
            return True
        if state.battery_soc >= config.soc_max and state.pv_kw > state.load_kw:
            return True
        if state.battery_soc <= config.soc_reserve_hard and state.load_kw >= state.pv_kw:
            return True
        return False

    def _direction_lock_active(self, now: datetime, min_gap_seconds: int) -> bool:
        if self._last_action_ts is None:
            return False
        return now < self._last_action_ts + timedelta(seconds=max(0, min_gap_seconds))

    @staticmethod
    def _derated_limit(state: SiteState, config: BatteryPolicyConfig) -> float:
        if state.battery_temp_c <= config.battery_temp_derate_start_c:
            return config.battery_power_limit_kw
        temp_span = max(1.0, config.battery_temp_max_c - config.battery_temp_derate_start_c)
        reduction = min(1.0, (state.battery_temp_c - config.battery_temp_derate_start_c) / temp_span)
        return max(0.3, config.battery_power_limit_kw * (1.0 - reduction))

    def _result(self, action_type: str, target_power_kw: float, reason: str, state: SiteState, tariff: TariffState) -> ScoredAction:
        self._last_action = action_type
        self._last_action_ts = datetime.now(UTC)
        score = ScoreBreakdown(
            energy_cost=round(max(0.0, state.load_kw - state.pv_kw) * max(0.0, tariff.import_price), 6),
            battery_degradation_penalty=round(abs(target_power_kw) * 0.02, 6),
            reserve_violation_penalty=0.0,
            command_churn_penalty=0.0 if action_type == "idle" else 0.03,
            device_safety_penalty=0.0,
        )
        explanation = {
            "decision": action_type,
            "target_power_kw": round(target_power_kw, 4),
            "tariff": {
                "import_price": tariff.import_price,
                "export_price": tariff.export_price,
                "is_peak": tariff.is_peak,
                "is_shoulder": tariff.is_shoulder,
                "tariff_name": tariff.tariff_name,
            },
            "summary": reason,
        }
        return ScoredAction(
            action_type=action_type,
            target_power_kw=target_power_kw,
            score=score,
            explanation=explanation,
            reason=reason,
            economic_class=ScoredAction.classify_economic_intent(action_type),  # v2 Reporting extension point
        )
