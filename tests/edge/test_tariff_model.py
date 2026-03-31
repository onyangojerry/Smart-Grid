# Author: Jerry Onyango
# Contribution: Tests flat and time-of-use tariff state modeling and export credit behavior.
from __future__ import annotations

import unittest
from datetime import UTC, datetime

from energy_api.control.tariff import build_tariff_state


class TestTariffModel(unittest.TestCase):
    def test_flat_tariff(self) -> None:
        ts = datetime(2026, 3, 29, 10, 0, tzinfo=UTC)
        state = build_tariff_state(
            ts=ts,
            policy={"tariff_model": "flat", "flat_import_price": 0.21, "export_credit_price": 0.07},
            default_import=0.2,
            default_export=0.05,
        )
        self.assertEqual(state.tariff_name, "flat")
        self.assertAlmostEqual(state.import_price, 0.21, places=4)
        self.assertAlmostEqual(state.export_price, 0.07, places=4)

    def test_tou_peak(self) -> None:
        ts = datetime(2026, 3, 29, 18, 0, tzinfo=UTC)
        state = build_tariff_state(
            ts=ts,
            policy={
                "tariff_model": "tou",
                "tou_windows": [
                    {"start_hour": 0, "end_hour": 7, "import_price": 0.10, "export_price": 0.06, "label": "offpeak"},
                    {"start_hour": 17, "end_hour": 21, "import_price": 0.34, "export_price": 0.08, "label": "peak"},
                ],
            },
            default_import=0.2,
            default_export=0.05,
        )
        self.assertTrue(state.is_peak)
        self.assertEqual(state.tariff_name, "peak")
        self.assertAlmostEqual(state.import_price, 0.34, places=4)


if __name__ == "__main__":
    unittest.main()
