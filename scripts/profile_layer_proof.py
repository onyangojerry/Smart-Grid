# Author: Jerry Onyango
# Contribution: Emits deterministic proof artifacts for canonical model, register maps, battery policy outcomes, and command verification.
from __future__ import annotations

import json
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from energy_api.control.battery_policy import BatteryPolicyConfig, BatteryPolicyEngine
from energy_api.control.models import SiteState
from energy_api.control.tariff import TariffState
from energy_api.edge.commands import CommandExecutor
from energy_api.edge.device_profiles import load_profile


class FakeAdapter:
    def __init__(self) -> None:
        self.registers = {1: int(2.3 * 10) & 0xFFFF, 16: 1, 21: 50, 22: 30}

    def write_single_register(self, address: int, value: int, unit_id: int = 1) -> None:
        self.registers[address] = value & 0xFFFF

    def read_holding_registers(self, address: int, count: int, unit_id: int = 1) -> list[int]:
        return [self.registers.get(address + i, 0) for i in range(count)]


def _profile_payloads() -> tuple[dict, dict]:
    victron_payload = {
        "default_unit_id": 100,
        "register_points": [
            {"canonical_key": "site_load_kw", "register_type": "input", "address": 820, "count": 2, "data_type": "float32", "poll_group": "fast"},
            {"canonical_key": "pv_generation_kw", "register_type": "input", "address": 808, "count": 2, "data_type": "float32", "poll_group": "fast"},
            {"canonical_key": "battery_soc", "register_type": "input", "address": 843, "count": 1, "data_type": "uint16", "scale_factor": 0.1, "poll_group": "medium"},
            {"canonical_key": "battery_power_kw", "register_type": "input", "address": 842, "count": 2, "data_type": "float32", "poll_group": "fast"},
            {"canonical_key": "grid_import_kw", "register_type": "input", "address": 807, "count": 2, "data_type": "float32", "poll_group": "fast"},
            {"canonical_key": "grid_export_kw", "register_type": "input", "address": 807, "count": 2, "data_type": "float32", "poll_group": "fast"},
            {"canonical_key": "inverter_mode", "register_type": "input", "address": 870, "count": 1, "data_type": "uint16", "poll_group": "fast"},
            {"canonical_key": "alarm_code", "register_type": "input", "address": 875, "count": 1, "data_type": "uint16", "poll_group": "fast"},
            {"canonical_key": "device_fault", "register_type": "input", "address": 876, "count": 1, "data_type": "uint16", "poll_group": "fast"},
        ],
    }
    sma_payload = {
        "default_unit_id": 1,
        "register_points": [
            {"canonical_key": "site_load_kw", "register_type": "input", "address": 40183, "count": 2, "data_type": "float32", "poll_group": "fast"},
            {"canonical_key": "pv_generation_kw", "register_type": "input", "address": 30775, "count": 2, "data_type": "float32", "poll_group": "fast"},
            {"canonical_key": "battery_soc", "register_type": "input", "address": 30845, "count": 2, "data_type": "float32", "poll_group": "medium"},
            {"canonical_key": "battery_power_kw", "register_type": "input", "address": 30813, "count": 2, "data_type": "float32", "poll_group": "fast"},
            {"canonical_key": "grid_import_kw", "register_type": "input", "address": 30795, "count": 2, "data_type": "float32", "poll_group": "fast"},
            {"canonical_key": "grid_export_kw", "register_type": "input", "address": 30795, "count": 2, "data_type": "float32", "poll_group": "fast"},
            {"canonical_key": "inverter_mode", "register_type": "input", "address": 40151, "count": 1, "data_type": "uint16", "poll_group": "fast"},
            {"canonical_key": "alarm_code", "register_type": "input", "address": 40191, "count": 1, "data_type": "uint16", "poll_group": "fast"},
            {"canonical_key": "device_fault", "register_type": "input", "address": 40192, "count": 1, "data_type": "uint16", "poll_group": "fast"},
        ],
    }
    return victron_payload, sma_payload


def run() -> None:
    sim = load_profile("simulated_home_bess")
    victron_payload, sma_payload = _profile_payloads()

    with tempfile.TemporaryDirectory() as tmp:
        vpath = Path(tmp) / "victron.json"
        spath = Path(tmp) / "sma.json"
        vpath.write_text(json.dumps(victron_payload), encoding="utf-8")
        spath.write_text(json.dumps(sma_payload), encoding="utf-8")
        victron = load_profile("victron_gx_home_bess", str(vpath))
        sma = load_profile("sma_sunspec_home_bess", str(spath))

    print("CANONICAL_MODEL_PROOF")
    for profile in (sim, victron, sma):
        keys = sorted({point.canonical_key for point in profile.register_points})
        print(json.dumps({"profile": profile.name, "unit_id": profile.default_unit_id, "keys": keys[:8]}, separators=(",", ":")))

    print("REGISTER_MAP_PROOF")
    print(json.dumps({
        "profile": sim.name,
        "fast": [p.canonical_key for p in sim.register_points if p.poll_group == "fast"],
        "medium": [p.canonical_key for p in sim.register_points if p.poll_group == "medium"],
        "slow": [p.canonical_key for p in sim.register_points if p.poll_group == "slow"],
    }, separators=(",", ":")))

    print("BATTERY_POLICY_PROOF")
    base = SiteState(ts=datetime.now(UTC), pv_kw=6.0, load_kw=2.0, battery_soc=50.0, battery_power_kw=0.0, grid_import_kw=1.0, grid_export_kw=0.0, battery_temp_c=30.0, price_import=0.2, price_export=0.06, online=True)
    peak_state = SiteState(ts=datetime.now(UTC), pv_kw=0.3, load_kw=4.0, battery_soc=70.0, battery_power_kw=-1.5, grid_import_kw=3.0, grid_export_kw=0.0, battery_temp_c=32.0, price_import=0.34, price_export=0.06, online=True)
    low_soc = SiteState(ts=datetime.now(UTC), pv_kw=0.1, load_kw=5.0, battery_soc=10.0, battery_power_kw=0.0, grid_import_kw=4.9, grid_export_kw=0.0, battery_temp_c=28.0, price_import=0.35, price_export=0.06, online=True)
    print(json.dumps({"scenario": "pv_surplus", "action": BatteryPolicyEngine().decide(base, TariffState(0.2, 0.06, False, True, "shoulder"), BatteryPolicyConfig(), datetime.now(UTC)).action_type}, separators=(",", ":")))
    print(json.dumps({"scenario": "peak_tariff", "action": BatteryPolicyEngine().decide(peak_state, TariffState(0.34, 0.06, True, False, "peak"), BatteryPolicyConfig(), datetime.now(UTC)).action_type}, separators=(",", ":")))
    print(json.dumps({"scenario": "stale_telemetry", "action": BatteryPolicyEngine().decide(base, TariffState(0.34, 0.06, True, False, "peak"), BatteryPolicyConfig(stale_critical=True), datetime.now(UTC)).action_type}, separators=(",", ":")))
    print(json.dumps({"scenario": "soc_reserve", "action": BatteryPolicyEngine().decide(low_soc, TariffState(0.34, 0.06, True, False, "peak"), BatteryPolicyConfig(), datetime.now(UTC)).action_type}, separators=(",", ":")))

    print("COMMAND_VERIFICATION_PROOF")
    adapter = FakeAdapter()
    executor = CommandExecutor(adapter=adapter, profile=sim, allow_writes=True)
    print(json.dumps({"command": "charge_setpoint_kw", "result": executor.execute_and_reconcile({"command_type": "charge_setpoint_kw", "target_power_kw": 2.0, "setpoint_scale": 10})}, separators=(",", ":")))
    adapter.registers[1] = int(0.2 * 10) & 0xFFFF
    print(json.dumps({"command": "discharge_setpoint_kw_failure", "result": executor.execute_and_reconcile({"command_type": "discharge_setpoint_kw", "target_power_kw": 2.0, "setpoint_scale": 10})}, separators=(",", ":")))
    print(json.dumps({"command": "unsupported_victron_write", "result": CommandExecutor(adapter=adapter, profile=load_profile("victron_gx_home_bess"), allow_writes=True).execute_and_reconcile({"command_type": "set_grid_limit_kw", "target_power_kw": 1.0})}, separators=(",", ":")))

    print("DEPLOYMENT_PROOF")
    print(json.dumps({"mode": "simulated", "env": {"EDGE_DEVICE_PROFILE": "simulated_home_bess", "EDGE_DEVICE_ENABLED": "true", "EDGE_OBSERVATION_ONLY_MODE": "false", "EDGE_READ_ONLY_MODE": "false"}}, separators=(",", ":")))
    print(json.dumps({"mode": "real_read_only", "env": {"EDGE_DEVICE_PROFILE": "victron_gx_home_bess", "EDGE_PROFILE_REGISTER_MAP_PATH": "/secure/victron/register_map.json", "EDGE_DEVICE_ENABLED": "true", "EDGE_OBSERVATION_ONLY_MODE": "true", "EDGE_READ_ONLY_MODE": "true"}}, separators=(",", ":")))
    print(json.dumps({"mode": "real_write_enabled", "env": {"EDGE_DEVICE_PROFILE": "victron_gx_home_bess", "EDGE_PROFILE_REGISTER_MAP_PATH": "/secure/victron/register_map.json", "EDGE_DEVICE_ENABLED": "true", "EDGE_OBSERVATION_ONLY_MODE": "false", "EDGE_READ_ONLY_MODE": "false", "safety_note": "LAN/VPN only; never expose Modbus TCP on public internet."}}, separators=(",", ":")))


if __name__ == "__main__":
    run()
