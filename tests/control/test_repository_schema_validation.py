# Author: Jerry Onyango
# Contribution: Verifies repository schema authority is validation-only and fails fast when tables are missing.
from __future__ import annotations

import unittest
from unittest.mock import patch

from energy_api.control.repository import ControlRepository


class TestRepositorySchemaValidation(unittest.TestCase):
    def test_missing_required_table_raises_runtime_error(self) -> None:
        def table_exists(table_name: str) -> bool:
            return table_name != "devices"

        with patch.object(ControlRepository, "_table_exists", side_effect=table_exists):
            with self.assertRaises(RuntimeError) as cm:
                ControlRepository(db_url="postgresql://example.invalid/test")

        self.assertIn("missing required control schema tables", str(cm.exception))
        self.assertIn("devices", str(cm.exception))

    def test_present_schema_does_not_attempt_runtime_ddl(self) -> None:
        with patch.object(ControlRepository, "_table_exists", return_value=True), patch.object(
            ControlRepository,
            "_connect",
            side_effect=AssertionError("runtime DDL should not open a connection"),
        ):
            repo = ControlRepository(db_url="postgresql://example.invalid/test")

        self.assertIsInstance(repo, ControlRepository)


if __name__ == "__main__":
    unittest.main()
