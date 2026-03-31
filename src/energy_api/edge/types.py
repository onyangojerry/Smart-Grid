# Author: Jerry Onyango
# Contribution: Defines shared edge runtime types for mappings, timestamps, decoded values, and telemetry records.
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


ValueType = Literal["uint16", "int16", "uint32", "int32", "float32"]
ByteOrder = Literal["big", "little"]
WordOrder = Literal["big", "little"]
RegisterType = Literal["holding", "input", "coil"]
AccessMode = Literal["read", "write", "read_write"]
PollGroup = Literal["fast", "medium", "slow", "verify"]
Quality = Literal["good", "bad", "suspect"]
CanonicalCommand = Literal[
    "idle",
    "charge_setpoint_kw",
    "discharge_setpoint_kw",
    "set_mode",
    "set_grid_limit_kw",
    "set_export_limit_kw",
]
VerifyMode = Literal["readback_equals", "observed_positive", "observed_negative", "observed_near_zero", "mode_equals"]


@dataclass(frozen=True)
class TimestampBundle:
    ts: datetime
    device_ts: datetime
    gateway_received_at: datetime
    processed_at: datetime


@dataclass(frozen=True)
class RegisterPoint:
    canonical_key: str
    profile_name: str = "simulated_home_bess"
    register_type: RegisterType = "holding"
    address: int = 0
    count: int = 1
    data_type: ValueType = "float32"
    scale_factor: float = 1.0
    byte_order: ByteOrder = "big"
    word_order: WordOrder = "big"
    access: AccessMode = "read"
    poll_group: PollGroup = "fast"
    signed: bool = False
    tolerance: float = 0.05
    verify_address: int | None = None
    transform: str | None = None
    unit: str | None = None
    critical: bool = False

    # Backward-compatible fields used by legacy tests/config payloads.
    register_address: int | None = None
    register_count: int | None = None
    value_type: ValueType | None = None

    def __post_init__(self) -> None:
        if self.register_address is not None:
            object.__setattr__(self, "address", int(self.register_address))
        else:
            object.__setattr__(self, "register_address", int(self.address))
        if self.register_count is not None:
            object.__setattr__(self, "count", int(self.register_count))
        else:
            object.__setattr__(self, "register_count", int(self.count))
        if self.value_type is not None:
            object.__setattr__(self, "data_type", self.value_type)
        else:
            object.__setattr__(self, "value_type", self.data_type)

    @property
    def normalized_data_type(self) -> ValueType:
        return self.data_type


# Preserve the existing public name so current code and tests remain valid.
PointMapping = RegisterPoint


@dataclass(frozen=True)
class CommandPoint:
    canonical_command: CanonicalCommand
    supported: bool
    write_address: int | None
    write_type: RegisterType
    value_encoding: Literal["signed_scale", "uint16", "enum"]
    verify_address: int | None
    verify_mode: VerifyMode
    tolerance: float
    supports_readback: bool


@dataclass(frozen=True)
class TelemetryRecord:
    canonical_key: str
    value: float | None
    unit: str | None
    quality: Quality
    ts: datetime
    device_ts: datetime
    gateway_received_at: datetime
    processed_at: datetime
    stale: bool
    stale_reason: str | None = None
    error: str | None = None


@dataclass(frozen=True)
class DecodedPoint:
    canonical_key: str
    value: float
    unit: str | None
