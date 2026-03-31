# Author: Jerry Onyango
# Contribution: Loads edge runtime service configuration from environment variables and mapping overrides.

from __future__ import annotations

import os
from dataclasses import dataclass

from .device_profiles import DeviceProfile, load_profile
from .types import PointMapping


@dataclass(frozen=True)
class EdgeServiceSettings:
    runtime_mode: str
    log_level: str
    site_id: str
    gateway_id: str
    sqlite_path: str
    status_file_path: str
    api_base_url: str
    api_timeout_seconds: float
    api_bearer_token: str | None
    api_key: str | None
    modbus_host: str
    modbus_port: int
    modbus_timeout_seconds: float
    modbus_unit_id: int
    modbus_unit_id_source: str
    configured_modbus_unit_id: int | None
    profile_default_unit_id: int
    allow_profile_unit_id_override: bool
    profile_name: str
    profile_register_map_path: str | None
    profile: DeviceProfile
    device_enabled: bool
    read_only_mode: bool
    observation_only_mode: bool
    poll_interval_seconds: int
    command_interval_seconds: int
    status_interval_seconds: int
    replay_limit: int
    replay_base_backoff_seconds: int
    replay_max_backoff_seconds: int
    shutdown_grace_seconds: int
    continue_on_poll_error: bool
    point_mappings: list[PointMapping]

    @staticmethod
    def from_env() -> "EdgeServiceSettings":
        profile_name = os.getenv("EDGE_DEVICE_PROFILE", "simulated_home_bess")
        profile_register_map_path = os.getenv("EDGE_PROFILE_REGISTER_MAP_PATH")
        profile = load_profile(profile_name=profile_name, register_map_path=profile_register_map_path)
        configured_unit_id_raw = str(os.getenv("EDGE_MODBUS_UNIT_ID", "")).strip()
        configured_unit_id = int(configured_unit_id_raw) if configured_unit_id_raw else None
        allow_profile_unit_id_override = _as_bool(os.getenv("EDGE_ALLOW_PROFILE_UNIT_ID_OVERRIDE", "false"))
        profile_default_unit_id = int(profile.default_unit_id)
        modbus_unit_id_source = "profile_default"

        if configured_unit_id is None:
            modbus_unit_id = profile_default_unit_id
        elif configured_unit_id == profile_default_unit_id:
            modbus_unit_id = configured_unit_id
            modbus_unit_id_source = "env_matches_profile"
        elif allow_profile_unit_id_override:
            modbus_unit_id = configured_unit_id
            modbus_unit_id_source = "env_override"
        else:
            raise ValueError(
                "EDGE_MODBUS_UNIT_ID mismatch with profile default "
                f"(profile={profile.name}, profile_default_unit_id={profile_default_unit_id}, configured={configured_unit_id}). "
                "Set EDGE_ALLOW_PROFILE_UNIT_ID_OVERRIDE=true to allow explicit override."
            )

        return EdgeServiceSettings(
            runtime_mode=os.getenv("EDGE_RUNTIME_MODE", "service"),
            log_level=os.getenv("EDGE_LOG_LEVEL", "INFO"),
            site_id=os.getenv("EDGE_SITE_ID", "site_001"),
            gateway_id=os.getenv("EDGE_GATEWAY_ID", "gw_edge_01"),
            sqlite_path=os.getenv("EDGE_SQLITE_PATH", "./data/edge/edge_runtime.db"),
            status_file_path=os.getenv("EDGE_STATUS_FILE", "./data/edge/status.json"),
            api_base_url=os.getenv("EA_API_BASE_URL", "http://localhost:8000"),
            api_timeout_seconds=float(os.getenv("EDGE_API_TIMEOUT_SECONDS", "10.0")),
            api_bearer_token=os.getenv("EDGE_API_BEARER_TOKEN"),
            api_key=os.getenv("EDGE_API_KEY"),
            modbus_host=os.getenv("EDGE_MODBUS_HOST", "127.0.0.1"),
            modbus_port=int(os.getenv("EDGE_MODBUS_PORT", "15020")),
            modbus_timeout_seconds=float(os.getenv("EDGE_MODBUS_TIMEOUT_SECONDS", "3.0")),
            modbus_unit_id=modbus_unit_id,
            modbus_unit_id_source=modbus_unit_id_source,
            configured_modbus_unit_id=configured_unit_id,
            profile_default_unit_id=profile_default_unit_id,
            allow_profile_unit_id_override=allow_profile_unit_id_override,
            profile_name=profile.name,
            profile_register_map_path=profile_register_map_path,
            profile=profile,
            device_enabled=_as_bool(os.getenv("EDGE_DEVICE_ENABLED", "true")),
            read_only_mode=_as_bool(os.getenv("EDGE_READ_ONLY_MODE", "false")),
            observation_only_mode=_as_bool(os.getenv("EDGE_OBSERVATION_ONLY_MODE", "false")),
            poll_interval_seconds=max(1, int(os.getenv("EDGE_POLL_INTERVAL_SECONDS", "5"))),
            command_interval_seconds=max(1, int(os.getenv("EDGE_COMMAND_INTERVAL_SECONDS", "5"))),
            status_interval_seconds=max(1, int(os.getenv("EDGE_STATUS_INTERVAL_SECONDS", "10"))),
            replay_limit=max(1, int(os.getenv("EDGE_REPLAY_LIMIT", "500"))),
            replay_base_backoff_seconds=max(1, int(os.getenv("EDGE_REPLAY_BASE_BACKOFF_SECONDS", "2"))),
            replay_max_backoff_seconds=max(1, int(os.getenv("EDGE_REPLAY_MAX_BACKOFF_SECONDS", "60"))),
            shutdown_grace_seconds=max(1, int(os.getenv("EDGE_SHUTDOWN_GRACE_SECONDS", "10"))),
            continue_on_poll_error=_as_bool(os.getenv("EDGE_CONTINUE_ON_POLL_ERROR", "true")),
            point_mappings=profile.register_points,
        )

    def startup_validation_errors(self) -> list[str]:
        errors: list[str] = []
        writes_requested = self.device_enabled and (not self.read_only_mode) and (not self.observation_only_mode)

        if self.read_only_mode and self.observation_only_mode:
            errors.append("invalid_mode_combination:read_only_and_observation_only")

        if writes_requested and (not self.profile.supports_writes):
            errors.append(
                f"write_mode_requested_for_read_only_profile:profile={self.profile_name}"
            )

        if self.modbus_unit_id_source == "env_override" and (not self.allow_profile_unit_id_override):
            errors.append("unit_id_override_source_conflict")

        return errors


def _as_bool(raw: str | None) -> bool:
    return str(raw or "").strip().lower() in {"1", "true", "yes", "on"}
