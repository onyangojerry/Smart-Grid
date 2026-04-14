# Author: Jerry Onyango
# Contribution: Validates production battery policy decisions for PV surplus, peak tariff, stale telemetry, and reserve protection.
from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

from energy_api.control.battery_policy import BatteryPolicyConfig, BatteryPolicyEngine
from energy_api.control.models import SiteState
from energy_api.control.tariff import TariffState


class TestBatteryPolicy(unittest.TestCase):
    def _state(self, **overrides: float | bool) -> SiteState:
        base = {
            "ts": datetime.now(UTC),
            "pv_kw": 5.0,
            "load_kw": 2.0,
            "battery_soc": 50.0,
            "battery_power_kw": 0.0,
            "grid_import_kw": 1.0,
            "grid_export_kw": 0.0,
            "battery_temp_c": 30.0,
            "price_import": 0.2,
            "price_export": 0.06,
            "online": True,
        }
        base.update(overrides)
        return SiteState(**base)

    def test_pv_surplus_charges(self) -> None:
        engine = BatteryPolicyEngine()
        state = self._state(pv_kw=6.0, load_kw=2.0, battery_soc=40.0)
        tariff = TariffState(import_price=0.22, export_price=0.07, is_peak=False, is_shoulder=True, tariff_name="shoulder")
        action = engine.decide(state, tariff, BatteryPolicyConfig(), datetime.now(UTC))
        self.assertEqual(action.action_type, "charge_setpoint_kw")

    def test_peak_tariff_discharges(self) -> None:
        engine = BatteryPolicyEngine()
        state = self._state(pv_kw=0.4, load_kw=4.2, battery_soc=70.0)
        tariff = TariffState(import_price=0.35, export_price=0.07, is_peak=True, is_shoulder=False, tariff_name="peak")
        action = engine.decide(state, tariff, BatteryPolicyConfig(), datetime.now(UTC))
        self.assertEqual(action.action_type, "discharge_setpoint_kw")

    def test_stale_telemetry_forces_idle(self) -> None:
        engine = BatteryPolicyEngine()
        state = self._state()
        tariff = TariffState(import_price=0.35, export_price=0.07, is_peak=True, is_shoulder=False, tariff_name="peak")
        cfg = BatteryPolicyConfig(stale_critical=True)
        action = engine.decide(state, tariff, cfg, datetime.now(UTC))
        self.assertEqual(action.action_type, "idle")

    def test_reserve_protection_forces_idle(self) -> None:
        engine = BatteryPolicyEngine()
        state = self._state(pv_kw=0.0, load_kw=5.0, battery_soc=10.0)
        tariff = TariffState(import_price=0.32, export_price=0.07, is_peak=True, is_shoulder=False, tariff_name="peak")
        cfg = BatteryPolicyConfig(soc_reserve_hard=15.0)
        action = engine.decide(state, tariff, cfg, datetime.now(UTC))
        self.assertEqual(action.action_type, "idle")

    def test_alarm_blocks_action(self) -> None:
        engine = BatteryPolicyEngine()
        state = self._state(pv_kw=8.0, load_kw=2.0, battery_soc=60.0)
        tariff = TariffState(import_price=0.20, export_price=0.06, is_peak=False, is_shoulder=True, tariff_name="shoulder")
        cfg = BatteryPolicyConfig(active_alarm=True)
        action = engine.decide(state, tariff, cfg, datetime.now(UTC))
        self.assertEqual(action.action_type, "idle")

    def test_unresolved_command_blocks_action(self) -> None:
        engine = BatteryPolicyEngine()
        state = self._state(pv_kw=8.0, load_kw=2.0, battery_soc=60.0)
        tariff = TariffState(import_price=0.20, export_price=0.06, is_peak=False, is_shoulder=True, tariff_name="shoulder")
        cfg = BatteryPolicyConfig(unresolved_critical_command=True)
        action = engine.decide(state, tariff, cfg, datetime.now(UTC))
        self.assertEqual(action.action_type, "idle")

    def test_minimum_action_duration_continues_same_direction(self) -> None:
        engine = BatteryPolicyEngine()
        cfg = BatteryPolicyConfig(minimum_action_duration=300, minimum_direction_change_gap=600)
        tariff = TariffState(import_price=0.22, export_price=0.07, is_peak=False, is_shoulder=True, tariff_name="shoulder")
        first_state = self._state(pv_kw=6.0, load_kw=2.0, battery_soc=40.0)
        first_now = datetime.now(UTC)
        first_action = engine.decide(first_state, tariff, cfg, first_now)

        second_state = self._state(pv_kw=1.0, load_kw=4.5, battery_soc=70.0)
        second_tariff = TariffState(import_price=0.35, export_price=0.07, is_peak=True, is_shoulder=False, tariff_name="peak")
        second_action = engine.decide(second_state, second_tariff, cfg, first_now + timedelta(seconds=60))

        self.assertEqual(first_action.action_type, "charge_setpoint_kw")
        self.assertEqual(second_action.action_type, "charge_setpoint_kw")
        self.assertEqual(second_action.reason, "minimum_action_duration")

    def test_direction_change_is_blocked_until_gap_elapses(self) -> None:
        engine = BatteryPolicyEngine()
        cfg = BatteryPolicyConfig(minimum_action_duration=300, minimum_direction_change_gap=600)
        charge_tariff = TariffState(import_price=0.22, export_price=0.07, is_peak=False, is_shoulder=True, tariff_name="shoulder")
        charge_state = self._state(pv_kw=6.0, load_kw=2.0, battery_soc=40.0)
        first_now = datetime.now(UTC)
        engine.decide(charge_state, charge_tariff, cfg, first_now)

        discharge_state = self._state(pv_kw=0.4, load_kw=4.2, battery_soc=70.0)
        discharge_tariff = TariffState(import_price=0.35, export_price=0.07, is_peak=True, is_shoulder=False, tariff_name="peak")
        blocked_action = engine.decide(discharge_state, discharge_tariff, cfg, first_now + timedelta(seconds=301))

        self.assertEqual(blocked_action.action_type, "idle")
        self.assertEqual(blocked_action.reason, "direction_change_gap")

    def test_same_direction_continuation_is_not_blocked(self) -> None:
        engine = BatteryPolicyEngine()
        cfg = BatteryPolicyConfig(minimum_action_duration=300, minimum_direction_change_gap=600)
        tariff = TariffState(import_price=0.22, export_price=0.07, is_peak=False, is_shoulder=True, tariff_name="shoulder")
        state = self._state(pv_kw=6.0, load_kw=2.0, battery_soc=40.0)
        first_now = datetime.now(UTC)
        engine.decide(state, tariff, cfg, first_now)

        continued_action = engine.decide(state, tariff, cfg, first_now + timedelta(seconds=301))

        self.assertEqual(continued_action.action_type, "charge_setpoint_kw")


if __name__ == "__main__":
    unittest.main()
