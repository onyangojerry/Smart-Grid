# Author: Jerry Onyango
# Contribution: Tests device profile loading, validation, and vendor defaults for simulated, Victron, and SMA paths.
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from energy_api.edge.device_profiles import load_profile
from energy_api.edge.profile_validation import validate_profile, validate_profile_file


class TestDeviceProfiles(unittest.TestCase):
    def test_simulated_profile_is_complete(self) -> None:
        profile = load_profile("simulated_home_bess")
        keys = {point.canonical_key for point in profile.register_points}
        self.assertIn("site_load_kw", keys)
        self.assertIn("pv_generation_kw", keys)
        self.assertTrue(profile.supports_writes)
        self.assertEqual(validate_profile(profile), [])

    def test_victron_defaults_and_unit_id(self) -> None:
        profile = load_profile("victron_gx_home_bess")
        self.assertEqual(profile.default_unit_id, 100)
        self.assertFalse(profile.supports_writes)
        self.assertEqual(profile.vendor, "Victron")
        self.assertEqual(profile.version, "v1.0.0")
        self.assertEqual(validate_profile(profile), [])

    def test_sma_defaults_and_versioned_metadata(self) -> None:
        profile = load_profile("sma_sunspec_home_bess")
        self.assertEqual(profile.vendor, "SMA")
        self.assertEqual(profile.version, "v1.0.0")
        self.assertEqual(validate_profile(profile), [])

    def test_incomplete_native_profile_fails_on_load(self) -> None:
        with self.assertRaises(ValueError) as cm:
            load_profile("sma_native_modbus_home_bess")

        self.assertIn("invalid profile_name=sma_native_modbus_home_bess", str(cm.exception))

    def test_profile_override_file(self) -> None:
        payload = {
            "description": "Victron profile for specific deployment",
            "default_unit_id": 100,
            "supports_writes": True,
            "register_points": [
                {
                    "canonical_key": "site_load_kw",
                    "register_type": "input",
                    "address": 820,
                    "count": 2,
                    "data_type": "float32",
                    "poll_group": "fast",
                },
                {
                    "canonical_key": "battery_soc",
                    "register_type": "input",
                    "address": 843,
                    "count": 1,
                    "data_type": "uint16",
                    "scale_factor": 0.1,
                    "poll_group": "medium",
                },
                {
                    "canonical_key": "pv_generation_kw",
                    "register_type": "input",
                    "address": 808,
                    "count": 2,
                    "data_type": "float32",
                    "poll_group": "fast",
                },
                {
                    "canonical_key": "battery_power_kw",
                    "register_type": "input",
                    "address": 842,
                    "count": 2,
                    "data_type": "float32",
                    "poll_group": "fast",
                },
                {
                    "canonical_key": "grid_import_kw",
                    "register_type": "input",
                    "address": 807,
                    "count": 2,
                    "data_type": "float32",
                    "poll_group": "fast",
                },
                {
                    "canonical_key": "grid_export_kw",
                    "register_type": "input",
                    "address": 807,
                    "count": 2,
                    "data_type": "float32",
                    "poll_group": "fast",
                },
                {
                    "canonical_key": "inverter_mode",
                    "register_type": "input",
                    "address": 870,
                    "count": 1,
                    "data_type": "uint16",
                },
                {
                    "canonical_key": "alarm_code",
                    "register_type": "input",
                    "address": 875,
                    "count": 1,
                    "data_type": "uint16",
                },
                {
                    "canonical_key": "device_fault",
                    "register_type": "input",
                    "address": 876,
                    "count": 1,
                    "data_type": "uint16",
                },
            ],
            "command_points": [
                {
                    "canonical_command": "charge_setpoint_kw",
                    "write_address": 2714,
                    "write_type": "holding",
                    "value_encoding": "signed_scale",
                    "verify_address": 2714,
                    "verify_mode": "observed_positive",
                    "supports_readback": True,
                },
                {
                    "canonical_command": "discharge_setpoint_kw",
                    "write_address": 2714,
                    "write_type": "holding",
                    "value_encoding": "signed_scale",
                    "verify_address": 2714,
                    "verify_mode": "observed_negative",
                    "supports_readback": True,
                },
                {
                    "canonical_command": "idle",
                    "write_address": 2714,
                    "write_type": "holding",
                    "value_encoding": "signed_scale",
                    "verify_address": 2714,
                    "verify_mode": "observed_near_zero",
                    "supports_readback": True,
                },
                {
                    "canonical_command": "set_mode",
                    "write_address": 2700,
                    "write_type": "holding",
                    "value_encoding": "enum",
                    "verify_address": 2700,
                    "verify_mode": "mode_equals",
                    "supports_readback": True,
                },
                {
                    "canonical_command": "set_grid_limit_kw",
                    "write_address": 2716,
                    "write_type": "holding",
                    "value_encoding": "signed_scale",
                    "verify_address": 2716,
                    "verify_mode": "readback_equals",
                    "supports_readback": True,
                },
                {
                    "canonical_command": "set_export_limit_kw",
                    "write_address": 2717,
                    "write_type": "holding",
                    "value_encoding": "signed_scale",
                    "verify_address": 2717,
                    "verify_mode": "readback_equals",
                    "supports_readback": True,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "victron.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            profile = load_profile("victron_gx_home_bess", str(path))

        self.assertEqual(profile.default_unit_id, 100)
        self.assertTrue(profile.supports_writes)
        self.assertEqual(len(profile.command_points), 6)

    def test_invalid_example_missing_version_fails(self) -> None:
        errors = validate_profile_file(Path("profiles/invalid_examples/missing_version.json"))
        self.assertTrue(any("metadata.version" in err for err in errors))

    def test_invalid_example_missing_verify_address_fails(self) -> None:
        errors = validate_profile_file(Path("profiles/invalid_examples/missing_verify_address.json"))
        self.assertTrue(any("requires integer verify_address" in err for err in errors))


if __name__ == "__main__":
    unittest.main()
