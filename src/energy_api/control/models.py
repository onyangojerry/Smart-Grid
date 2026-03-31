# Author: Jerry Onyango
# Contribution: Defines state, scoring, and action data structures used by the control-loop engines.

# /Users/loan/Desktop/energyallocation/src/energy_api/control/models.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


ActionType = Literal[
    "charge",
    "discharge",
    "idle",
    "set_limit",
    "set_mode",
    "charge_setpoint_kw",
    "discharge_setpoint_kw",
    "set_grid_limit_kw",
    "set_export_limit_kw",
]


@dataclass(frozen=True)
class SiteState:
    ts: datetime
    pv_kw: float
    load_kw: float
    battery_soc: float
    battery_power_kw: float
    grid_import_kw: float
    grid_export_kw: float
    battery_temp_c: float
    price_import: float
    price_export: float
    online: bool


@dataclass(frozen=True)
class ScoreBreakdown:
    energy_cost: float
    battery_degradation_penalty: float
    reserve_violation_penalty: float
    command_churn_penalty: float
    device_safety_penalty: float

    @property
    def total(self) -> float:
        return (
            self.energy_cost
            + self.battery_degradation_penalty
            + self.reserve_violation_penalty
            + self.command_churn_penalty
            + self.device_safety_penalty
        )


@dataclass(frozen=True)
class ScoredAction:
    action_type: ActionType
    target_power_kw: float
    score: ScoreBreakdown
    explanation: dict[str, object]
    reason: str
    economic_class: str = "modeled"  # v2 Extension point: "modeled", "atomic", "neutral", "constrained_control"

    @classmethod
    def classify_economic_intent(cls, action_type: ActionType) -> str:
        """
        Classify the economic intent of an action for v2 reporting.
        v1 Semantics:
        - "modeled": charge/discharge directly affect optimized_cost and baseline_cost (economic shifting)
        - "neutral": idle/set_mode/set_limit do not affect cost in v1 but may in v2
        v2 Extension Points:
        - "constrained_control": Future mode for constrained charging/discharging (e.g., during demand response)
        - "atomic": Atomic operations that should not be broken down (future)
        """
        if action_type in {"charge", "charge_setpoint_kw", "discharge", "discharge_setpoint_kw"}:
            return "modeled"  # Primary economic shifters: affect cost model
        if action_type in {"idle", "set_mode", "set_limit", "set_grid_limit_kw", "set_export_limit_kw"}:
            return "neutral"  # v1 baseline-neutral; tracked for observability
        return "unknown"
