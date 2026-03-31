# Author: Jerry Onyango
# Contribution: Validates poll-group behavior and profile-driven register type reads in EdgePoller.
from __future__ import annotations

import unittest

from energy_api.edge.poller import EdgePoller
from energy_api.edge.types import PointMapping


class FakeAdapter:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int, int, int]] = []

    def read_holding_registers(self, address: int, count: int, unit_id: int = 1) -> list[int]:
        self.calls.append(("holding", address, count, unit_id))
        return [650] if count == 1 else [0x4148, 0x0000]

    def read_input_registers(self, address: int, count: int, unit_id: int = 1) -> list[int]:
        self.calls.append(("input", address, count, unit_id))
        return [650] if count == 1 else [0x4148, 0x0000]


class TestProfilePollerGroups(unittest.TestCase):
    def test_only_selected_group_polled(self) -> None:
        adapter = FakeAdapter()
        mappings = [
            PointMapping(canonical_key="battery_soc", register_type="holding", register_address=0, register_count=1, value_type="uint16", poll_group="fast", scale_factor=0.1),
            PointMapping(canonical_key="battery_temp_c", register_type="input", register_address=10, register_count=1, value_type="uint16", poll_group="medium", scale_factor=0.1),
        ]
        poller = EdgePoller(adapter=adapter, mappings=mappings, polling_interval_seconds=2)

        records = poller.poll_once(groups={"fast"})
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].canonical_key, "battery_soc")
        self.assertEqual(adapter.calls[0][0], "holding")

    def test_input_register_path(self) -> None:
        adapter = FakeAdapter()
        mappings = [
            PointMapping(canonical_key="site_load_kw", register_type="input", register_address=4, register_count=2, value_type="float32", poll_group="fast"),
        ]
        poller = EdgePoller(adapter=adapter, mappings=mappings, polling_interval_seconds=2)
        records = poller.poll_once(groups={"fast"})
        self.assertEqual(len(records), 1)
        self.assertEqual(adapter.calls[0][0], "input")


if __name__ == "__main__":
    unittest.main()
