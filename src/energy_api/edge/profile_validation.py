# Author: Jerry Onyango
# Contribution: Validates device profile register maps and command capabilities before runtime polling starts.
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .device_profiles import CANONICAL_TELEMETRY_KEYS, DeviceProfile


REQUIRED_METADATA_KEYS = {"vendor", "model_family", "version"}

REQUIRED_COMMANDS = {
    "idle",
    "charge_setpoint_kw",
    "discharge_setpoint_kw",
    "set_mode",
    "set_grid_limit_kw",
    "set_export_limit_kw",
}

VERIFY_REQUIRED_COMMANDS = {
    "idle",
    "charge_setpoint_kw",
    "discharge_setpoint_kw",
    "set_mode",
}


def validate_profile(profile: DeviceProfile) -> list[str]:
    errors: list[str] = []

    if not profile.vendor.strip():
        errors.append("missing_vendor")
    if not profile.model_family.strip():
        errors.append("missing_model_family")
    if not profile.version.strip():
        errors.append("missing_version")

    keys = {point.canonical_key for point in profile.register_points}

    required_minimum = {
        "site_load_kw",
        "pv_generation_kw",
        "battery_soc",
        "battery_power_kw",
        "grid_import_kw",
        "grid_export_kw",
        "inverter_mode",
        "alarm_code",
        "device_fault",
    }

    missing = sorted(required_minimum - keys)
    if missing:
        errors.append(f"missing_required_keys:{','.join(missing)}")

    unknown = sorted(k for k in keys if k not in CANONICAL_TELEMETRY_KEYS)
    if unknown:
        errors.append(f"unknown_canonical_keys:{','.join(unknown)}")

    for point in profile.register_points:
        if point.count <= 0:
            errors.append(f"invalid_count:{point.canonical_key}")
        if point.register_type not in {"holding", "input", "coil"}:
            errors.append(f"invalid_register_type:{point.canonical_key}")

    if profile.supports_writes and not profile.command_points:
        errors.append("write_enabled_without_command_points")

    commands_by_name = {point.canonical_command: point for point in profile.command_points}
    missing_commands = sorted(REQUIRED_COMMANDS - set(commands_by_name.keys()))
    if missing_commands:
        errors.append(f"missing_required_commands:{','.join(missing_commands)}")

    for command_name, point in commands_by_name.items():
        if point.supported and point.write_address is None:
            errors.append(f"supported_command_missing_write_address:{command_name}")
        if not point.supported and point.write_address is not None:
            errors.append(f"unsupported_command_must_not_set_write_address:{command_name}")
        if point.supported and command_name in VERIFY_REQUIRED_COMMANDS and point.verify_address is None:
            errors.append(f"supported_command_missing_verify_address:{command_name}")

    return errors


def validate_profile_payload(payload: dict[str, Any], profile_name: str = "unknown") -> list[str]:
    errors: list[str] = []

    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        errors.append(f"{profile_name}: metadata is required")
    else:
        for key in REQUIRED_METADATA_KEYS:
            value = metadata.get(key)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{profile_name}: metadata.{key} is required and must be a non-empty string")

    register_points = payload.get("register_points")
    if not isinstance(register_points, list) or not register_points:
        errors.append(f"{profile_name}: register_points must be a non-empty list")

    command_points = payload.get("command_points")
    if not isinstance(command_points, list) or not command_points:
        errors.append(f"{profile_name}: command_points must be a non-empty list")
        return errors

    seen: set[str] = set()
    command_names: set[str] = set()
    for idx, item in enumerate(command_points):
        if not isinstance(item, dict):
            errors.append(f"{profile_name}: command_points[{idx}] must be an object")
            continue

        command_name = item.get("canonical_command")
        if not isinstance(command_name, str) or not command_name.strip():
            errors.append(f"{profile_name}: command_points[{idx}].canonical_command must be a non-empty string")
            continue

        if command_name in seen:
            errors.append(f"{profile_name}: duplicate command mapping for '{command_name}'")
        seen.add(command_name)
        command_names.add(command_name)

        supported = item.get("supported", True)
        if not isinstance(supported, bool):
            errors.append(f"{profile_name}: command_points[{idx}].supported must be a boolean")
            continue

        write_address = item.get("write_address")
        if supported and not isinstance(write_address, int):
            errors.append(
                f"{profile_name}: command_points[{idx}] '{command_name}' must include integer write_address when supported=true"
            )
        if not supported and write_address is not None:
            errors.append(
                f"{profile_name}: command_points[{idx}] '{command_name}' must set write_address to null when supported=false"
            )

        verify_address = item.get("verify_address")
        if supported and command_name in VERIFY_REQUIRED_COMMANDS and not isinstance(verify_address, int):
            errors.append(
                f"{profile_name}: command_points[{idx}] '{command_name}' requires integer verify_address"
            )

    missing_commands = sorted(REQUIRED_COMMANDS - command_names)
    if missing_commands:
        errors.append(f"{profile_name}: missing_required_commands:{','.join(missing_commands)}")
    return errors


def validate_profile_file(path: str | Path) -> list[str]:
    profile_path = Path(path)
    payload = json.loads(profile_path.read_text(encoding="utf-8"))
    return validate_profile_payload(payload, profile_name=profile_path.name)
