# Author: Jerry Onyango
# Contribution: Tests the circuit breaker for writes in CommandExecutor.
from __future__ import annotations

import unittest
import time
import sys
from unittest.mock import MagicMock

# Mock dependencies before importing anything from energy_api
mock_modbus = MagicMock()
class ModbusAdapterError(Exception):
    pass
mock_modbus.ModbusAdapterError = ModbusAdapterError
sys.modules["energy_api.edge.modbus_adapter"] = mock_modbus

sys.modules["httpx"] = MagicMock()
sys.modules["psycopg"] = MagicMock()
sys.modules["jwt"] = MagicMock()
sys.modules["pymodbus"] = MagicMock()
sys.modules["pymodbus.client"] = MagicMock()
sys.modules["pymodbus.datastore"] = MagicMock()
sys.modules["pymodbus.server"] = MagicMock()
sys.modules["pymodbus.transaction"] = MagicMock()

from energy_api.edge.commands import CommandExecutor

class FakeAdapter:
    def __init__(self) -> None:
        self.write_count = 0
        self.registers: dict[int, int] = {}

    def write_single_register(self, address: int, value: int, unit_id: int = 1) -> None:
        self.write_count += 1
        self.registers[address] = value & 0xFFFF

    def read_holding_registers(self, address: int, count: int, unit_id: int = 1) -> list[int]:
        return [self.registers.get(address + i, 0) for i in range(count)]

class TestWriteCircuitBreaker(unittest.TestCase):
    def test_circuit_breaker_limits_writes(self) -> None:
        adapter = FakeAdapter()
        # Set a very low limit for testing
        executor = CommandExecutor(adapter=adapter, max_writes_per_minute=2)

        payload = {
            "command_type": "set_limit",
            "limit_register": 30,
            "target_limit": 75,
        }

        # First write: OK
        ok, msg = executor.execute_and_reconcile(payload)
        self.assertTrue(ok)
        self.assertEqual(adapter.write_count, 1)

        # Second write: OK
        ok, msg = executor.execute_and_reconcile(payload)
        self.assertTrue(ok)
        self.assertEqual(adapter.write_count, 2)

        # Third write: Circuit breaker should trigger
        ok, msg = executor.execute_and_reconcile(payload)
        self.assertFalse(ok)
        self.assertIn("circuit_breaker_active", msg)
        self.assertEqual(adapter.write_count, 2) # No new write

    def test_circuit_breaker_resets_after_window(self) -> None:
        adapter = FakeAdapter()
        executor = CommandExecutor(adapter=adapter, max_writes_per_minute=1)

        payload = {
            "command_type": "set_limit",
            "limit_register": 30,
            "target_limit": 75,
        }

        # First write: OK
        ok, _ = executor.execute_and_reconcile(payload)
        self.assertTrue(ok)

        # Manually manipulate history to simulate time passing (61 seconds ago)
        executor._write_history = [time.time() - 61]

        # Second write: OK now
        ok, _ = executor.execute_and_reconcile(payload)
        self.assertTrue(ok)
        self.assertEqual(adapter.write_count, 2)

if __name__ == "__main__":
    unittest.main()
