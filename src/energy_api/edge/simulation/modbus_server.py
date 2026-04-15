# Author: Jerry Onyango
# Contribution: Runs a configurable simulated Modbus server with injectable faults for timeout, bad data, disconnect, and frozen values.
from __future__ import annotations

import asyncio
import threading
import time
from typing import Any, Iterable

from pymodbus.server import StartAsyncTcpServer
from pymodbus.simulator import SimData, SimDevice, DataType


class SimulatedModbusDevice:
    host: str = "127.0.0.1"
    port: int = 15020
    address: int = 1
    timeout_injection_seconds: float = 1.5

    def __init__(self, host: str = "127.0.0.1", port: int = 15020, address: int = 1) -> None:
        self.host = host
        self.port = port
        self._address = address
        self._values: dict[int, int] = {}
        self.disconnect_enabled = False
        self.timeout_enabled = False
        self.timeout_seconds = 0.0
        self.bad_data_enabled = False
        self.bad_data_value = 0xFFFF
        self.frozen_values_enabled = False

        self._simdata = SimData(address=0, values=[0] * 200, datatype=DataType.REGISTERS, count=1)
        self._device = SimDevice(id=self._address, simdata=[self._simdata], action=self._action)
        self._devices = [self._device]
        self._thread: threading.Thread | None = None

    async def _action(
        self,
        function_code: int,
        start_address: int,
        address: int,
        count: int,
        current_registers: list[int],
        set_values: list[int] | list[bool] | None,
    ) -> Any:
        if self.disconnect_enabled:
            # Simulate a hard disconnect by raising an error that pymodbus will catch or let propagate to the transport
            raise ConnectionResetError("simulated disconnect")
        
        if self.timeout_enabled:
            # Simulate a timeout by delaying the response
            await asyncio.sleep(self.timeout_seconds)

        if set_values is not None:
            # This is a WRITE operation
            if not self.frozen_values_enabled:
                for i, val in enumerate(set_values):
                    v = int(val) & 0xFFFF
                    self._values[address + i] = v
                    if address + i < len(self._simdata.values):
                        self._simdata.values[address + i] = v
            return None

        # This is a READ operation
        if self.bad_data_enabled:
            # Return garbage data but with a SUCCESSFUL Modbus response
            # We modify the registers slice in-place if possible, but also return a list to be sure
            garbage = [self.bad_data_value] * count
            for i in range(count):
                current_registers[i] = garbage[i]
            return garbage

        if self.frozen_values_enabled:
            # Return the frozen values from self._values, not whatever garbage may be in simdata.values
            frozen = []
            for i in range(count):
                reg_addr = address + i
                frozen.append(self._values.get(reg_addr, 0))
            return frozen

        # Normal read: Sync datastore with our internal values before returning
        for i in range(count):
            reg_addr = address + i
            if reg_addr in self._values:
                val = self._values[reg_addr]
                current_registers[i] = val
                if reg_addr < len(self._simdata.values):
                    self._simdata.values[reg_addr] = val
        
        return None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        def _run_server() -> None:
            asyncio.run(StartAsyncTcpServer(context=self._devices, address=(self.host, self.port)))

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
        if self.frozen_values_enabled:
            return
        val = value & 0xFFFF
        self._values[address] = val
        if address < len(self._simdata.values):
            self._simdata.values[address] = val

    def set_holding_registers(self, address: int, values: list[int]) -> None:
        if self.frozen_values_enabled:
            return
        for i, v in enumerate(values):
            val = int(v) & 0xFFFF
            self._values[address + i] = val
            if address + i < len(self._simdata.values):
                self._simdata.values[address + i] = val

    def inject_timeout(self, enabled: bool, timeout_seconds: float | None = None) -> None:
        self.timeout_enabled = enabled
        self.timeout_seconds = timeout_seconds if timeout_seconds is not None else self.timeout_injection_seconds

    def inject_bad_data(self, enabled: bool, bad_value: int = 0xFFFF) -> None:
        self.bad_data_enabled = enabled
        self.bad_data_value = bad_value & 0xFFFF

    def inject_disconnect(self, enabled: bool) -> None:
        self.disconnect_enabled = enabled

    def freeze_values(self, enabled: bool) -> None:
        self.frozen_values_enabled = enabled
