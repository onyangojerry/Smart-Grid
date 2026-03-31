# Author: Jerry Onyango
# Contribution: Runs one polling cycle to read device registers, decode telemetry, assign timestamps, and apply staleness logic.
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import time

from .device_profiles import canonicalize_key
from .decoder import DecodeError, Decoder
from .modbus_adapter import ModbusAdapter, ModbusAdapterError
from .staleness import StalenessTracker
from .types import PointMapping, TelemetryRecord

# The EdgePoller class is responsible for performing a single polling cycle of 
# the edge runtime. It reads data from devices using the ModbusAdapter, 
# decodes the raw register values into meaningful telemetry using 
# the Decoder, and applies staleness logic to determine the freshness 
# of the data. The poll_once method returns a list of TelemetryRecord 
# objects that encapsulate the results of the polling cycle, 
# including any errors or quality issues encountered during reading or decoding.
@dataclass
class EdgePoller:
    adapter: ModbusAdapter
    mappings: list[PointMapping]
    polling_interval_seconds: int = 5
    unit_id: int = 1
    group_intervals: dict[str, int] | None = None

    def __post_init__(self) -> None:
        self.decoder = Decoder()
        self.staleness = StalenessTracker(stale_after_seconds=self.polling_interval_seconds * 2)
        self.group_intervals = self.group_intervals or {
            "fast": max(2, self.polling_interval_seconds),
            "medium": max(10, self.polling_interval_seconds * 3),
            "slow": max(60, self.polling_interval_seconds * 12),
            "verify": 1,
        }
        now = time.monotonic()
        self._next_group_due: dict[str, float] = {
            group: now for group in self.group_intervals
        }

    def due_groups(self) -> set[str]:
        now = time.monotonic()
        due: set[str] = set()
        for group, next_due in self._next_group_due.items():
            if now >= next_due:
                due.add(group)
                self._next_group_due[group] = now + float(self.group_intervals.get(group, self.polling_interval_seconds))
        return due or {"fast"}

    def poll_once(self, groups: set[str] | None = None) -> list[TelemetryRecord]:
        gateway_received_at = datetime.now(UTC)
        records: list[TelemetryRecord] = []
        selected_groups = groups or self.due_groups()

        for mapping in self.mappings:
            if mapping.poll_group not in selected_groups:
                continue

            read_failed = False
            decode_failed = False
            decoded_value: float | None = None
            error: str | None = None

            try:
                if mapping.register_type == "holding":
                    registers = self.adapter.read_holding_registers(
                        address=int(mapping.register_address or 0),
                        count=int(mapping.register_count or 1),
                        unit_id=self.unit_id,
                    )
                elif mapping.register_type == "input":
                    registers = self.adapter.read_input_registers(
                        address=int(mapping.register_address or 0),
                        count=int(mapping.register_count or 1),
                        unit_id=self.unit_id,
                    )
                else:
                    raise ModbusAdapterError("unsupported_register_type", f"Unsupported register_type={mapping.register_type}")
            except ModbusAdapterError as exc:
                read_failed = True
                registers = []
                error = f"{exc.code}:{exc}"

            if not read_failed:
                try:
                    decoded = self.decoder.decode(mapping, registers)
                    decoded_value = decoded.value
                except DecodeError as exc:
                    decode_failed = True
                    error = str(exc)

            processed_at = datetime.now(UTC)
            device_ts = processed_at if decoded_value is not None else gateway_received_at
            stale, stale_reason = self.staleness.evaluate(
                key=mapping.canonical_key,
                now=processed_at,
                value=decoded_value,
                missing_read=read_failed,
                decode_failed=decode_failed,
            )

            quality = "good"
            if decode_failed:
                quality = "bad"
            elif read_failed:
                quality = "suspect"

            ts = device_ts
            records.append(
                TelemetryRecord(
                    canonical_key=canonicalize_key(mapping.canonical_key),
                    value=decoded_value,
                    unit=mapping.unit,
                    quality=quality,
                    ts=ts,
                    device_ts=device_ts,
                    gateway_received_at=gateway_received_at,
                    processed_at=processed_at,
                    stale=stale,
                    stale_reason=stale_reason,
                    error=error,
                )
            )

        return records
