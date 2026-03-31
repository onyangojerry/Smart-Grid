# Author: Jerry Onyango
# Contribution: Defines profile-driven device register/command models for simulated, Victron GX, and SMA integrations.
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .types import CanonicalCommand, CommandPoint, PointMapping


CANONICAL_TELEMETRY_KEYS: tuple[str, ...] = (
    "site_load_kw",
    "pv_generation_kw",
    "battery_soc",
    "battery_power_kw",
    "grid_import_kw",
    "grid_export_kw",
    "battery_voltage_v",
    "battery_current_a",
    "battery_temp_c",
    "inverter_mode",
    "alarm_code",
    "device_online",
    "device_fault",
)


LEGACY_KEY_ALIASES: dict[str, str] = {
    "pv_kw": "pv_generation_kw",
    "load_kw": "site_load_kw",
    "pv_generation": "pv_generation_kw",
}


@dataclass(frozen=True)
class DeviceProfile:
    name: str
    vendor: str
    model_family: str
    version: str
    description: str
    default_unit_id: int
    register_points: list[PointMapping]
    command_points: list[CommandPoint]
    supports_writes: bool
    source_of_truth: str

    def command_for(self, command: CanonicalCommand) -> CommandPoint | None:
        for point in self.command_points:
            if point.canonical_command == command:
                return point
        return None

    def supported_commands(self) -> set[str]:
        return {point.canonical_command for point in self.command_points}


def canonicalize_key(key: str) -> str:
    return LEGACY_KEY_ALIASES.get(key, key)


def _simulated_profile() -> DeviceProfile:
    points = [
        PointMapping(canonical_key="battery_soc", profile_name="simulated_home_bess", register_type="holding", address=0, count=1, data_type="uint16", scale_factor=0.1, unit="%", poll_group="medium", critical=True),
        PointMapping(canonical_key="battery_power_kw", profile_name="simulated_home_bess", register_type="holding", address=1, count=1, data_type="int16", scale_factor=0.1, signed=True, unit="kW", poll_group="fast", critical=True),
        PointMapping(canonical_key="pv_generation_kw", profile_name="simulated_home_bess", register_type="holding", address=2, count=2, data_type="float32", unit="kW", poll_group="fast", critical=True),
        PointMapping(canonical_key="site_load_kw", profile_name="simulated_home_bess", register_type="holding", address=4, count=2, data_type="float32", unit="kW", poll_group="fast", critical=True),
        PointMapping(canonical_key="grid_import_kw", profile_name="simulated_home_bess", register_type="holding", address=6, count=2, data_type="float32", unit="kW", poll_group="fast", critical=True),
        PointMapping(canonical_key="grid_export_kw", profile_name="simulated_home_bess", register_type="holding", address=8, count=2, data_type="float32", unit="kW", poll_group="fast", critical=True),
        PointMapping(canonical_key="battery_temp_c", profile_name="simulated_home_bess", register_type="holding", address=10, count=1, data_type="int16", signed=True, scale_factor=0.1, unit="C", poll_group="medium", critical=True),
        PointMapping(canonical_key="battery_voltage_v", profile_name="simulated_home_bess", register_type="holding", address=14, count=1, data_type="uint16", scale_factor=0.1, unit="V", poll_group="medium", critical=False),
        PointMapping(canonical_key="battery_current_a", profile_name="simulated_home_bess", register_type="holding", address=15, count=1, data_type="int16", signed=True, scale_factor=0.1, unit="A", poll_group="medium", critical=False),
        PointMapping(canonical_key="inverter_mode", profile_name="simulated_home_bess", register_type="holding", address=16, count=1, data_type="uint16", poll_group="fast", critical=True),
        PointMapping(canonical_key="alarm_code", profile_name="simulated_home_bess", register_type="holding", address=17, count=1, data_type="uint16", poll_group="fast", critical=True),
        PointMapping(canonical_key="device_fault", profile_name="simulated_home_bess", register_type="holding", address=18, count=1, data_type="uint16", poll_group="fast", critical=True),
        PointMapping(canonical_key="device_online", profile_name="simulated_home_bess", register_type="holding", address=19, count=1, data_type="uint16", poll_group="medium", critical=True),
    ]
    commands = [
        CommandPoint(canonical_command="charge_setpoint_kw", supported=True, write_address=20, write_type="holding", value_encoding="signed_scale", verify_address=1, verify_mode="observed_positive", tolerance=0.15, supports_readback=True),
        CommandPoint(canonical_command="discharge_setpoint_kw", supported=True, write_address=20, write_type="holding", value_encoding="signed_scale", verify_address=1, verify_mode="observed_negative", tolerance=0.15, supports_readback=True),
        CommandPoint(canonical_command="idle", supported=True, write_address=20, write_type="holding", value_encoding="signed_scale", verify_address=1, verify_mode="observed_near_zero", tolerance=0.15, supports_readback=True),
        CommandPoint(canonical_command="set_mode", supported=True, write_address=16, write_type="holding", value_encoding="enum", verify_address=16, verify_mode="mode_equals", tolerance=0.0, supports_readback=True),
        CommandPoint(canonical_command="set_grid_limit_kw", supported=True, write_address=21, write_type="holding", value_encoding="signed_scale", verify_address=21, verify_mode="readback_equals", tolerance=0.1, supports_readback=True),
        CommandPoint(canonical_command="set_export_limit_kw", supported=True, write_address=22, write_type="holding", value_encoding="signed_scale", verify_address=22, verify_mode="readback_equals", tolerance=0.1, supports_readback=True),
    ]
    return DeviceProfile(
        name="simulated_home_bess",
        vendor="Repository",
        model_family="Simulated Home BESS",
        version="v1.0.0",
        description="Repository simulation profile used for integration tests and local runtime validation.",
        default_unit_id=1,
        register_points=points,
        command_points=commands,
        supports_writes=True,
        source_of_truth="Repository simulated register map under src/energy_api/edge/simulation/.",
    )


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _default_profile_artifact(profile_name: str) -> Path:
    return _repo_root() / "profiles" / profile_name / "v1.0.0.json"


def _victron_profile() -> DeviceProfile:
    return merge_profile_overrides(_simulated_profile(), str(_default_profile_artifact("victron_gx_home_bess")), profile_name="victron_gx_home_bess")


def _sma_sunspec_profile() -> DeviceProfile:
    return merge_profile_overrides(_simulated_profile(), str(_default_profile_artifact("sma_sunspec_home_bess")), profile_name="sma_sunspec_home_bess")


def _sma_native_profile() -> DeviceProfile:
    return DeviceProfile(
        name="sma_native_modbus_home_bess",
        vendor="SMA",
        model_family="Native Modbus Scaffold",
        version="v1.0.0",
        description="Optional SMA native Modbus scaffold. Requires explicit device-family register list.",
        default_unit_id=3,
        register_points=[],
        command_points=[],
        supports_writes=False,
        source_of_truth="Official SMA Modbus profile documentation per product family.",
    )


def base_profiles() -> dict[str, DeviceProfile]:
    return {
        "simulated_home_bess": _simulated_profile(),
        "victron_gx_home_bess": _victron_profile(),
        "sma_sunspec_home_bess": _sma_sunspec_profile(),
        "sma_native_modbus_home_bess": _sma_native_profile(),
    }


def load_profile(profile_name: str, register_map_path: str | None = None) -> DeviceProfile:
    profiles = base_profiles()
    profile = profiles.get(profile_name)
    if profile is None:
        raise ValueError(f"unsupported profile_name={profile_name}")
    if not register_map_path:
        return profile
    return merge_profile_overrides(profile, register_map_path, profile_name=profile_name)


def merge_profile_overrides(profile: DeviceProfile, register_map_path: str, profile_name: str | None = None) -> DeviceProfile:
    path = Path(register_map_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    metadata = payload.get("metadata", {}) if isinstance(payload.get("metadata", {}), dict) else {}

    register_points: list[PointMapping] = []
    for item in payload.get("register_points", []):
        register_points.append(_register_point_from_payload(profile_name or profile.name, item))
    command_points: list[CommandPoint] = []
    for item in payload.get("command_points", []):
        command_points.append(_command_point_from_payload(item))

    supports_writes = bool(payload.get("supports_writes", bool(command_points)))
    return DeviceProfile(
        name=profile_name or profile.name,
        vendor=str(metadata.get("vendor", profile.vendor)),
        model_family=str(metadata.get("model_family", profile.model_family)),
        version=str(metadata.get("version", profile.version)),
        description=payload.get("description", profile.description),
        default_unit_id=int(payload.get("default_unit_id", profile.default_unit_id)),
        register_points=register_points or profile.register_points,
        command_points=command_points or profile.command_points,
        supports_writes=supports_writes,
        source_of_truth=payload.get("source_of_truth", profile.source_of_truth),
    )


def _register_point_from_payload(profile_name: str, item: dict[str, Any]) -> PointMapping:
    return PointMapping(
        profile_name=profile_name,
        canonical_key=canonicalize_key(str(item["canonical_key"])),
        register_type=str(item.get("register_type", "holding")),
        address=int(item["address"]),
        count=int(item.get("count", 1)),
        data_type=str(item.get("data_type", "float32")),
        scale_factor=float(item.get("scale_factor", 1.0)),
        byte_order=str(item.get("byte_order", "big")),
        word_order=str(item.get("word_order", "big")),
        access=str(item.get("access", "read")),
        poll_group=str(item.get("poll_group", "fast")),
        critical=bool(item.get("critical", False)),
        tolerance=float(item.get("tolerance", 0.05)),
        verify_address=int(item["verify_address"]) if item.get("verify_address") is not None else None,
        transform=item.get("transform"),
        unit=item.get("unit"),
        signed=bool(item.get("signed", False)),
    )


def _command_point_from_payload(item: dict[str, Any]) -> CommandPoint:
    return CommandPoint(
        canonical_command=str(item["canonical_command"]),
        supported=bool(item.get("supported", True)),
        write_address=int(item["write_address"]) if item.get("write_address") is not None else None,
        write_type=str(item.get("write_type", "holding")),
        value_encoding=str(item.get("value_encoding", "signed_scale")),
        verify_address=int(item["verify_address"]) if item.get("verify_address") is not None else None,
        verify_mode=str(item.get("verify_mode", "readback_equals")),
        tolerance=float(item.get("tolerance", 0.1)),
        supports_readback=bool(item.get("supports_readback", False)),
    )
