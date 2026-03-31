# Author: Jerry Onyango
# Contribution: Verifies profile-aware command reconciliation success, failure, and read-only/unsupported safeguards.
from __future__ import annotations

import unittest

from energy_api.edge.commands import CommandExecutor
from energy_api.edge.device_profiles import load_profile


class FakeAdapter:
    def __init__(self) -> None:
        self.registers: dict[int, int] = {}

    def write_single_register(self, address: int, value: int, unit_id: int = 1) -> None:
        self.registers[address] = value & 0xFFFF

    def read_holding_registers(self, address: int, count: int, unit_id: int = 1) -> list[int]:
        return [self.registers.get(address + i, 0) for i in range(count)]


class TestProfileCommandReconciliation(unittest.TestCase):
    def test_charge_setpoint_reconciles(self) -> None:
        profile = load_profile("simulated_home_bess")
        adapter = FakeAdapter()
        adapter.registers[1] = int(2.2 * 10) & 0xFFFF
        executor = CommandExecutor(adapter=adapter, profile=profile, allow_writes=True)

        ok, detail = executor.execute_and_reconcile({"command_type": "charge_setpoint_kw", "target_power_kw": 2.0, "setpoint_scale": 10})
        self.assertTrue(ok)
        self.assertIn("reconciled", detail)

    def test_discharge_failure_case(self) -> None:
        profile = load_profile("simulated_home_bess")
        adapter = FakeAdapter()
        adapter.registers[1] = int(0.5 * 10) & 0xFFFF
        executor = CommandExecutor(adapter=adapter, profile=profile, allow_writes=True)

        ok, detail = executor.execute_and_reconcile({"command_type": "discharge_setpoint_kw", "target_power_kw": 2.0, "setpoint_scale": 10})
        self.assertFalse(ok)
        self.assertIn("observed_negative", detail)

    def test_unsupported_rejected(self) -> None:
        profile = load_profile("victron_gx_home_bess")
        adapter = FakeAdapter()
        executor = CommandExecutor(adapter=adapter, profile=profile, allow_writes=True)

        ok, detail = executor.execute_and_reconcile({"command_type": "set_grid_limit_kw", "target_power_kw": 1.0})
        self.assertFalse(ok)
        self.assertIn("unsupported_command_for_profile", detail)

    def test_read_only_blocks_write(self) -> None:
        profile = load_profile("simulated_home_bess")
        adapter = FakeAdapter()
        executor = CommandExecutor(adapter=adapter, profile=profile, allow_writes=False)

        ok, detail = executor.execute_and_reconcile({"command_type": "set_grid_limit_kw", "target_power_kw": 1.0})
        self.assertFalse(ok)
        self.assertEqual(detail, "writes_disabled_read_only_mode")


if __name__ == "__main__":
    unittest.main()
