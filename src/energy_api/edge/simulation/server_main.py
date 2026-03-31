# Author: Jerry Onyango
# Contribution: Starts a runnable simulated Modbus server process with default register seed values for local integration.

from __future__ import annotations

import logging
import os
import struct
import time

from energy_api.core import configure_logging

from .modbus_server import SimulatedModbusDevice


def _float32_to_regs(value: float) -> list[int]:
    payload = struct.pack(">f", float(value))
    return [int.from_bytes(payload[0:2], "big"), int.from_bytes(payload[2:4], "big")]


def run() -> None:
    configure_logging(level=logging.INFO)
    logger = logging.getLogger("energy_api.edge.simulation.server")

    host = os.getenv("EDGE_SIM_MODBUS_HOST", "0.0.0.0")
    port = int(os.getenv("EDGE_SIM_MODBUS_PORT", "15020"))

    device = SimulatedModbusDevice(host=host, port=port)
    device.start()

    device.set_holding_register(0, 650)
    device.set_holding_register(1, 0)
    device.set_holding_registers(2, _float32_to_regs(12.5))
    device.set_holding_registers(4, _float32_to_regs(18.2))
    device.set_holding_registers(6, _float32_to_regs(5.7))
    device.set_holding_registers(8, _float32_to_regs(0.0))
    device.set_holding_register(10, 255)
    device.set_holding_register(14, 525)
    device.set_holding_register(15, 105)
    device.set_holding_register(16, 1)
    device.set_holding_register(17, 0)
    device.set_holding_register(18, 0)
    device.set_holding_register(19, 1)
    device.set_holding_register(20, 0)
    device.set_holding_register(21, 50)
    device.set_holding_register(22, 30)

    logger.info("simulated_modbus_server_started host=%s port=%s", host, port)

    while True:
        time.sleep(60)


if __name__ == "__main__":
    run()
