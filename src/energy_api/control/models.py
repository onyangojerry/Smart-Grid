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
