# Author: Jerry Onyango
# Contribution: Verifies savings summary taxonomy normalization across legacy and modern command names.
from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta
from typing import Any

from energy_api.savings.service import SavingsService


class FakeSavingsRepository:
    def __init__(self, commands: list[dict[str, Any]], avg_import_price: float = 0.2) -> None:
        self._commands = commands
        self._avg_import_price = avg_import_price
        self.snapshot_calls: list[dict[str, Any]] = []

    def list_commands(self, site_id: str, start: datetime, end: datetime) -> list[dict[str, Any]]:
        return list(self._commands)

    def average_import_price(self, site_id: str) -> float:
        return self._avg_import_price

    def upsert_savings_snapshot(self, **kwargs: Any) -> str:
        self.snapshot_calls.append(kwargs)
        return "sav_test"


class TestSavingsServiceTaxonomy(unittest.TestCase):
    def test_modern_taxonomy_is_accounted_for(self) -> None:
        repo = FakeSavingsRepository(
            commands=[
                {"command_type": "charge_setpoint_kw", "target_power_kw": 3.0},
                {"command_type": "discharge_setpoint_kw", "target_power_kw": 2.0},
                {"command_type": "idle", "target_power_kw": 0.0},
                {"command_type": "set_mode", "target_power_kw": 0.0},
                {"command_type": "set_grid_limit_kw", "target_power_kw": 0.0},
            ]
        )
        service = SavingsService(repository=repo)

        now = datetime.now(UTC)
        summary = service.compute_summary(site_id="site_001", start=now - timedelta(days=1), end=now)

        self.assertEqual(summary["snapshot_id"], "sav_test")
        self.assertEqual(summary["command_taxonomy"]["charge"], 1)
        self.assertEqual(summary["command_taxonomy"]["discharge"], 1)
        self.assertEqual(summary["command_taxonomy"]["idle"], 1)
        self.assertEqual(summary["command_taxonomy"]["mode"], 1)
        self.assertEqual(summary["command_taxonomy"]["grid_limit"], 1)
        self.assertEqual(summary["command_taxonomy"]["other"], 0)
        self.assertAlmostEqual(summary["peak_demand_reduction"], 2.0, places=4)
        self.assertAlmostEqual(summary["battery_cycles"], 0.0417, places=4)

    def test_legacy_aliases_are_still_supported(self) -> None:
        repo = FakeSavingsRepository(
            commands=[
                {"command_type": "charge", "target_power_kw": 1.5},
                {"command_type": "discharge", "target_power_kw": 1.0},
                {"command_type": "set_limit", "target_power_kw": 0.0},
            ]
        )
        service = SavingsService(repository=repo)

        now = datetime.now(UTC)
        summary = service.compute_summary(site_id="site_001", start=now - timedelta(days=1), end=now)

        self.assertEqual(summary["command_taxonomy"]["charge"], 1)
        self.assertEqual(summary["command_taxonomy"]["discharge"], 1)
        self.assertEqual(summary["command_taxonomy"]["grid_limit"], 1)
        self.assertEqual(summary["command_taxonomy"]["other"], 0)
        self.assertGreaterEqual(summary["baseline_cost"], 0.0)
        self.assertGreaterEqual(summary["optimized_cost"], 0.0)


if __name__ == "__main__":
    unittest.main()
