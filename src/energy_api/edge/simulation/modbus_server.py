# Author: Jerry Onyango
# Contribution: Runs a configurable simulated Modbus server with injectable faults for timeout, bad data, disconnect, and frozen values.
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Iterable

from pymodbus.datastore import ModbusDeviceContext, ModbusSequentialDataBlock, ModbusServerContext
from pymodbus.server import StartTcpServer


class FaultInjectableDataBlock(ModbusSequentialDataBlock):
    def __init__(self, address: int, values: list[int]) -> None:
        super().__init__(address, values)
        self.disconnect_enabled = False
        self.timeout_enabled = False
        self.timeout_seconds = 0.0
        self.bad_data_enabled = False
        self.bad_data_value = 0xFFFF
        self.frozen_values_enabled = False

    def getValues(self, address: int, count: int = 1):
        if self.disconnect_enabled:
            raise ConnectionResetError("simulated disconnect")
        if self.timeout_enabled:
            time.sleep(self.timeout_seconds)
        values = list(super().getValues(address, count))
        if self.bad_data_enabled:
            return [self.bad_data_value for _ in values]
        return values

    def setValues(self, address: int, values):
        if self.frozen_values_enabled:
            return
        super().setValues(address, values)


@dataclass
class SimulatedModbusDevice:
    host: str = "127.0.0.1"
    port: int = 15020
    address: int = 1  # Add address parameter here
    timeout_injection_seconds: float = 1.5

    def __post_init__(self) -> None:
        # Adjust address to be 1-based for pymodbus datastore if it's 0
        self._address = self.address # Set _address from the dataclass field
        adjusted_address = max(1, self._address) 
        self._holding_block = FaultInjectableDataBlock(adjusted_address, [0] * 200)
        self._device_context = ModbusDeviceContext(hr=self._holding_block)
        self._context = ModbusServerContext(devices={1: self._device_context}, single=False)
        self._thread: threading.Thread | None = None

    # The server runs in a daemon thread, so it will automatically stop when the main program exits.
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        def _run_server() -> None:
            StartTcpServer(context=self._context, address=(self.host, self.port))

        self._thread = threading.Thread(target=_run_server, daemon=True)
        self._thread.start()
        time.sleep(0.2)

    def configure_register_map(self, register_map: dict[int, int | Iterable[int]]) -> None:
        for address, value in register_map.items():
            if isinstance(value, int):
                self.set_holding_register(address, value)
            else:
                self.set_holding_registers(address, list(value))

    def set_holding_register(self, address: int, value: int) -> None:
        self._holding_block.setValues(address + 1, [value & 0xFFFF])

    def set_holding_registers(self, address: int, values: list[int]) -> None:
        self._holding_block.setValues(address + 1, [int(v) & 0xFFFF for v in values])

    def inject_timeout(self, enabled: bool, timeout_seconds: float | None = None) -> None:
        self._holding_block.timeout_enabled = enabled
        self._holding_block.timeout_seconds = timeout_seconds if timeout_seconds is not None else self.timeout_injection_seconds

    def inject_bad_data(self, enabled: bool, bad_value: int = 0xFFFF) -> None:
        self._holding_block.bad_data_enabled = enabled
        self._holding_block.bad_data_value = bad_value & 0xFFFF

    def inject_disconnect(self, enabled: bool) -> None:
        self._holding_block.disconnect_enabled = enabled

    def freeze_values(self, enabled: bool) -> None:
        self._holding_block.frozen_values_enabled = enabled
