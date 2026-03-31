# Author: Jerry Onyango
# Contribution: Validates edge config precedence and startup safety checks for profile unit-id and mode/capability mismatches.
from __future__ import annotations

import unittest
from unittest.mock import patch

from energy_api.edge.config import EdgeServiceSettings


class TestConfigPrecedence(unittest.TestCase):
    def _base_env(self) -> dict[str, str]:
        return {
            "EDGE_DEVICE_PROFILE": "victron_gx_home_bess",
            "EDGE_PROFILE_REGISTER_MAP_PATH": "",
            "EDGE_RUNTIME_MODE": "service",
            "EDGE_SITE_ID": "site_001",
            "EDGE_GATEWAY_ID": "gw_edge_01",
            "EDGE_SQLITE_PATH": "./data/edge/edge_runtime.db",
            "EDGE_STATUS_FILE": "./data/edge/status.json",
            "EA_API_BASE_URL": "http://localhost:8000",
            "EDGE_MODBUS_HOST": "127.0.0.1",
            "EDGE_MODBUS_PORT": "15020",
            "EDGE_MODBUS_TIMEOUT_SECONDS": "3.0",
            "EDGE_DEVICE_ENABLED": "true",
            "EDGE_READ_ONLY_MODE": "true",
            "EDGE_OBSERVATION_ONLY_MODE": "false",
            "EDGE_POLL_INTERVAL_SECONDS": "5",
            "EDGE_COMMAND_INTERVAL_SECONDS": "5",
            "EDGE_STATUS_INTERVAL_SECONDS": "10",
            "EDGE_REPLAY_LIMIT": "500",
            "EDGE_REPLAY_BASE_BACKOFF_SECONDS": "2",
            "EDGE_REPLAY_MAX_BACKOFF_SECONDS": "60",
            "EDGE_SHUTDOWN_GRACE_SECONDS": "10",
            "EDGE_CONTINUE_ON_POLL_ERROR": "true",
            "EDGE_ALLOW_PROFILE_UNIT_ID_OVERRIDE": "false",
        }

    def test_profile_default_unit_id_used_when_env_unset(self) -> None:
        env = self._base_env()
        with patch.dict("os.environ", env, clear=True):
            settings = EdgeServiceSettings.from_env()
        self.assertEqual(settings.modbus_unit_id, 100)
        self.assertEqual(settings.modbus_unit_id_source, "profile_default")

    def test_matching_env_unit_id_allowed_without_override(self) -> None:
        env = self._base_env()
        env["EDGE_MODBUS_UNIT_ID"] = "100"
        with patch.dict("os.environ", env, clear=True):
            settings = EdgeServiceSettings.from_env()
        self.assertEqual(settings.modbus_unit_id, 100)
        self.assertEqual(settings.modbus_unit_id_source, "env_matches_profile")

    def test_mismatched_env_unit_id_fails_without_override_flag(self) -> None:
        env = self._base_env()
        env["EDGE_MODBUS_UNIT_ID"] = "1"
        with patch.dict("os.environ", env, clear=True):
            with self.assertRaises(ValueError) as ctx:
                EdgeServiceSettings.from_env()
        self.assertIn("EDGE_MODBUS_UNIT_ID mismatch", str(ctx.exception))

    def test_mismatched_env_unit_id_allowed_with_override_flag(self) -> None:
        env = self._base_env()
        env["EDGE_MODBUS_UNIT_ID"] = "1"
        env["EDGE_ALLOW_PROFILE_UNIT_ID_OVERRIDE"] = "true"
        with patch.dict("os.environ", env, clear=True):
            settings = EdgeServiceSettings.from_env()
        self.assertEqual(settings.modbus_unit_id, 1)
        self.assertEqual(settings.modbus_unit_id_source, "env_override")

    def test_invalid_write_mode_for_read_only_profile_fails_validation(self) -> None:
        env = self._base_env()
        env["EDGE_DEVICE_ENABLED"] = "true"
        env["EDGE_READ_ONLY_MODE"] = "false"
        env["EDGE_OBSERVATION_ONLY_MODE"] = "false"
        with patch.dict("os.environ", env, clear=True):
            settings = EdgeServiceSettings.from_env()
        errors = settings.startup_validation_errors()
        self.assertTrue(any("write_mode_requested_for_read_only_profile" in err for err in errors))


if __name__ == "__main__":
    unittest.main()
