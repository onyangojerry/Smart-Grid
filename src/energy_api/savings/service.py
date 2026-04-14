# Author: Jerry Onyango
# Contribution: Computes savings summaries from command activity and persists savings snapshots for reporting.

# /Users/loan/Desktop/energyallocation/src/energy_api/savings/service.py

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from energy_api.control.repository import ControlRepository


class SavingsService:
    def __init__(self, repository: ControlRepository | None = None) -> None:
        self.repository = repository or ControlRepository()

    def compute_summary(self, site_id: str, start: datetime | None = None, end: datetime | None = None) -> dict[str, Any]:
        end = end or datetime.now(UTC)
        start = start or (end - timedelta(days=30))

        commands = self.repository.list_commands(site_id=site_id, start=start, end=end)
        avg_import_price = self.repository.average_import_price(site_id)

        optimized_cost = 0.0
        baseline_cost = 0.0
        battery_cycles = 0.0
        peak_reduction = 0.0
        taxonomy_counts = {
            "charge": 0,
            "discharge": 0,
            "idle": 0,
            "mode": 0,
            "grid_limit": 0,
            "other": 0,
        }

        for command in commands:
            command_type = command.get("command_type")
            target_power_kw = float(command.get("target_power_kw") or 0.0)
            slot_hours = 5.0 / 60.0
            normalized = self._normalize_command_type(command_type)
            taxonomy_counts[normalized] += 1

            if normalized == "discharge":
                optimized_cost += max(0.0, 2.0 - target_power_kw) * avg_import_price * slot_hours
                baseline_cost += 2.0 * avg_import_price * slot_hours
                battery_cycles += target_power_kw * slot_hours / 10.0
                peak_reduction = max(peak_reduction, target_power_kw)
            elif normalized == "charge":
                optimized_cost += (2.0 + target_power_kw) * avg_import_price * slot_hours
                baseline_cost += 2.0 * avg_import_price * slot_hours
                battery_cycles += target_power_kw * slot_hours / 10.0
            else:
                # Non-energy-shifting commands remain baseline-neutral in this summary model.
                optimized_cost += 2.0 * avg_import_price * slot_hours
                baseline_cost += 2.0 * avg_import_price * slot_hours

        if baseline_cost <= 0:
            baseline_cost = 1.0
            optimized_cost = 1.0

        savings_percent = max(0.0, ((baseline_cost - optimized_cost) / baseline_cost) * 100.0)
        self_consumption_percent = min(100.0, 65.0 + savings_percent * 0.2)

        snapshot_id = self.repository.upsert_savings_snapshot(
            site_id=site_id,
            start=start,
            end=end,
            baseline_cost=round(baseline_cost, 4),
            optimized_cost=round(optimized_cost, 4),
            savings_percent=round(savings_percent, 4),
            battery_cycles=round(battery_cycles, 4),
            self_consumption_percent=round(self_consumption_percent, 4),
            peak_demand_reduction=round(peak_reduction, 4),
        )

        return {
            "snapshot_id": snapshot_id,
            "site_id": site_id,
            "window_start": start.isoformat(),
            "window_end": end.isoformat(),
            "baseline_cost": round(baseline_cost, 4),
            "optimized_cost": round(optimized_cost, 4),
            "savings_percent": round(savings_percent, 4),
            "battery_cycles": round(battery_cycles, 4),
            "self_consumption_percent": round(self_consumption_percent, 4),
            "peak_demand_reduction": round(peak_reduction, 4),
            "command_taxonomy": taxonomy_counts,
        }

    @staticmethod
    def _normalize_command_type(command_type: Any) -> str:
        command = str(command_type or "").strip().lower()
        if command in {"charge", "charge_setpoint_kw"}:
            return "charge"
        if command in {"discharge", "discharge_setpoint_kw"}:
            return "discharge"
        if command == "idle":
            return "idle"
        if command == "set_mode":
            return "mode"
        if command in {"set_limit", "set_grid_limit_kw", "set_export_limit_kw"}:
            return "grid_limit"
        return "other"
