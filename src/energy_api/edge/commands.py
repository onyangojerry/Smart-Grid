# Author: Jerry Onyango
# Contribution: Executes supported edge commands and applies explicit per-command reconciliation rules against device readback.
from __future__ import annotations

from dataclasses import dataclass, field
import time
from typing import Any, Literal

from .device_profiles import DeviceProfile
from .modbus_adapter import ModbusAdapter, ModbusAdapterError
from .types import CanonicalCommand, CommandPoint


CommandType = Literal[
    "charge",
    "discharge",
    "idle",
    "set_limit",
    "set_mode",
    "charge_setpoint_kw",
    "discharge_setpoint_kw",
    "set_grid_limit_kw",
    "set_export_limit_kw",
]


@dataclass
class CommandExecutor:
    adapter: ModbusAdapter
    unit_id: int = 1
    profile: DeviceProfile | None = None
    allow_writes: bool = True
    max_writes_per_minute: int = 60
    _write_history: list[float] = field(default_factory=list)

    def execute_and_reconcile(self, payload: dict[str, Any]) -> tuple[bool, str]:
        command_type = self._command_type(payload)
        canonical = self._canonical_command(command_type)

        if not self._check_circuit_breaker():
            return False, "circuit_breaker_active:too_many_writes"

        if self.profile is not None:
            point = self.profile.command_for(canonical)
            if point is None:
                return False, f"unsupported_command_for_profile:{canonical}"
            if not point.supported:
                return False, f"unsupported_command_for_profile:{canonical}"
            if not self.allow_writes:
                return False, "writes_disabled_read_only_mode"
            
            self._record_write()
            self._apply_profile_command(point, payload)
            return self._reconcile_profile_command(point, payload), f"reconciled_{point.verify_mode}"

        if command_type in {"charge", "discharge"}:
            self._record_write()
            self._apply_charge_discharge(command_type, payload)
            ok = self._reconcile_charge_discharge(command_type, payload)
            return ok, "reconciled_power_or_setpoint"

        if command_type == "idle":
            self._record_write()
            self._apply_idle(payload)
            ok = self._reconcile_idle(payload)
            return ok, "reconciled_near_zero_power"

        if command_type == "set_limit":
            self._record_write()
            self._apply_set_limit(payload)
            ok = self._reconcile_set_limit(payload)
            return ok, "reconciled_limit_readback"

        if command_type == "set_mode":
            self._record_write()
            self._apply_set_mode(payload)
            ok = self._reconcile_set_mode(payload)
            return ok, "reconciled_mode_readback"

        return False, "unsupported_command"

    def _check_circuit_breaker(self) -> bool:
        now = time.time()
        # Keep only writes from the last 60 seconds
        self._write_history = [t for t in self._write_history if now - t < 60]
        return len(self._write_history) < self.max_writes_per_minute

    def _record_write(self) -> None:
        self._write_history.append(time.time())

    def reconcile_only(self, payload: dict[str, Any]) -> tuple[bool, str]:
        command_type = self._command_type(payload)
        canonical = self._canonical_command(command_type)
        if self.profile is not None:
            point = self.profile.command_for(canonical)
            if point is None:
                return False, f"unsupported_command_for_profile:{canonical}"
            if not point.supported:
                return False, f"unsupported_command_for_profile:{canonical}"
            return self._reconcile_profile_command(point, payload), f"reconcile_only_{point.verify_mode}"

        if command_type in {"charge", "discharge"}:
            return self._reconcile_charge_discharge(command_type, payload), "reconcile_only_power_or_setpoint"
        if command_type == "idle":
            return self._reconcile_idle(payload), "reconcile_only_near_zero_power"
        if command_type == "set_limit":
            return self._reconcile_set_limit(payload), "reconcile_only_limit_readback"
        if command_type == "set_mode":
            return self._reconcile_set_mode(payload), "reconcile_only_mode_readback"
        return False, "unsupported_command"

    def _apply_profile_command(self, point: CommandPoint, payload: dict[str, Any]) -> None:
        if point.write_address is None:
            raise ModbusAdapterError("invalid_profile_command", f"missing_write_address:{point.canonical_command}")
        value = self._command_value(point, payload)
        encoded = self._encode_value(point, value, payload)
        self.adapter.write_single_register(point.write_address, encoded, unit_id=self.unit_id)

    def _reconcile_profile_command(self, point: CommandPoint, payload: dict[str, Any]) -> bool:
        verify_address = point.verify_address if point.verify_address is not None else point.write_address
        if verify_address is None:
            return False

        if point.verify_mode == "readback_equals":
            if not point.supports_readback:
                return False
            expected = self._encode_value(point, self._command_value(point, payload), payload) & 0xFFFF
            actual = self.adapter.read_holding_registers(verify_address, 1, unit_id=self.unit_id)[0] & 0xFFFF
            return actual == expected

        if point.verify_mode == "mode_equals":
            target_mode = int(payload.get("target_mode", payload.get("target_value", 0))) & 0xFFFF
            actual = self.adapter.read_holding_registers(verify_address, 1, unit_id=self.unit_id)[0] & 0xFFFF
            return actual == target_mode

        scale = float(payload.get("setpoint_scale", 10.0))
        power_raw = self.adapter.read_holding_registers(verify_address, 1, unit_id=self.unit_id)[0]
        power_kw = self._decode_int16(power_raw) / scale

        if point.verify_mode == "observed_positive":
            return power_kw >= max(0.0, point.tolerance)
        if point.verify_mode == "observed_negative":
            return power_kw <= -max(0.0, point.tolerance)
        if point.verify_mode == "observed_near_zero":
            return abs(power_kw) <= max(0.0, point.tolerance)

        return False

    @staticmethod
    def _command_value(point: CommandPoint, payload: dict[str, Any]) -> float:
        if point.canonical_command == "idle":
            return 0.0
        if point.canonical_command in {"charge_setpoint_kw", "discharge_setpoint_kw", "set_grid_limit_kw", "set_export_limit_kw"}:
            return float(payload.get("target_power_kw", payload.get("target_limit", payload.get("target_kw", 0.0))))
        if point.canonical_command == "set_mode":
            return float(payload.get("target_mode", payload.get("target_value", 0)))
        return 0.0

    @staticmethod
    def _encode_value(point: CommandPoint, value: float, payload: dict[str, Any]) -> int:
        if point.value_encoding == "enum":
            return int(round(value)) & 0xFFFF
        if point.value_encoding == "uint16":
            return max(0, int(round(value))) & 0xFFFF
        scale = float(payload.get("setpoint_scale", 10.0))
        signed_value = int(round(value * scale))
        if point.canonical_command == "discharge_setpoint_kw":
            signed_value = -abs(signed_value)
        if point.canonical_command == "charge_setpoint_kw":
            signed_value = abs(signed_value)
        return signed_value & 0xFFFF

    def _apply_charge_discharge(self, command_type: CommandType, payload: dict[str, Any]) -> None:
        register_address = int(payload["setpoint_register"])
        target_power_kw = float(payload.get("target_power_kw", 0.0))
        scale = float(payload.get("setpoint_scale", 10.0))

        signed_value = int(round(target_power_kw * scale))
        if command_type == "discharge":
            signed_value = -abs(signed_value)
        else:
            signed_value = abs(signed_value)

        encoded = signed_value & 0xFFFF
        self.adapter.write_single_register(register_address, encoded, unit_id=self.unit_id)

    def _reconcile_charge_discharge(self, command_type: CommandType, payload: dict[str, Any]) -> bool:
        power_register = int(payload["power_register"])
        setpoint_register = int(payload["setpoint_register"])
        min_effective_kw = float(payload.get("min_effective_power_kw", 0.1))
        scale = float(payload.get("setpoint_scale", 10.0))

        setpoint_raw = self.adapter.read_holding_registers(setpoint_register, 1, unit_id=self.unit_id)[0]
        power_raw = self.adapter.read_holding_registers(power_register, 1, unit_id=self.unit_id)[0]

        setpoint_kw = self._decode_int16(setpoint_raw) / scale
        power_kw = self._decode_int16(power_raw) / scale

        if command_type == "charge":
            return setpoint_kw > 0 and power_kw >= min_effective_kw
        return setpoint_kw < 0 and power_kw <= (-min_effective_kw)

    def _apply_idle(self, payload: dict[str, Any]) -> None:
        register_address = int(payload["setpoint_register"])
        self.adapter.write_single_register(register_address, 0, unit_id=self.unit_id)

    def _reconcile_idle(self, payload: dict[str, Any]) -> bool:
        power_register = int(payload["power_register"])
        threshold_kw = float(payload.get("idle_power_threshold_kw", 0.05))
        scale = float(payload.get("setpoint_scale", 10.0))

        power_raw = self.adapter.read_holding_registers(power_register, 1, unit_id=self.unit_id)[0]
        power_kw = self._decode_int16(power_raw) / scale
        return abs(power_kw) <= threshold_kw

    def _apply_set_limit(self, payload: dict[str, Any]) -> None:
        register_address = int(payload["limit_register"])
        target_limit = int(payload["target_limit"])
        self.adapter.write_single_register(register_address, target_limit & 0xFFFF, unit_id=self.unit_id)

    def _reconcile_set_limit(self, payload: dict[str, Any]) -> bool:
        register_address = int(payload["limit_register"])
        target_limit = int(payload["target_limit"]) & 0xFFFF
        actual = self.adapter.read_holding_registers(register_address, 1, unit_id=self.unit_id)[0] & 0xFFFF
        return actual == target_limit

    def _apply_set_mode(self, payload: dict[str, Any]) -> None:
        register_address = int(payload["mode_register"])
        target_mode = int(payload["target_mode"])
        self.adapter.write_single_register(register_address, target_mode & 0xFFFF, unit_id=self.unit_id)

    def _reconcile_set_mode(self, payload: dict[str, Any]) -> bool:
        register_address = int(payload["mode_register"])
        target_mode = int(payload["target_mode"]) & 0xFFFF
        actual = self.adapter.read_holding_registers(register_address, 1, unit_id=self.unit_id)[0] & 0xFFFF
        return actual == target_mode

    @staticmethod
    def _command_type(payload: dict[str, Any]) -> CommandType:
        value = str(payload.get("command_type", "")).strip()
        allowed = {
            "charge",
            "discharge",
            "idle",
            "set_limit",
            "set_mode",
            "charge_setpoint_kw",
            "discharge_setpoint_kw",
            "set_grid_limit_kw",
            "set_export_limit_kw",
        }
        if value not in allowed:
            raise ModbusAdapterError("invalid_command", f"Unsupported command_type={value}")
        return value  # type: ignore[return-value]

    @staticmethod
    def _canonical_command(command_type: CommandType) -> CanonicalCommand:
        aliases: dict[str, CanonicalCommand] = {
            "charge": "charge_setpoint_kw",
            "discharge": "discharge_setpoint_kw",
            "idle": "idle",
            "set_limit": "set_grid_limit_kw",
            "set_mode": "set_mode",
            "charge_setpoint_kw": "charge_setpoint_kw",
            "discharge_setpoint_kw": "discharge_setpoint_kw",
            "set_grid_limit_kw": "set_grid_limit_kw",
            "set_export_limit_kw": "set_export_limit_kw",
        }
        return aliases[str(command_type)]

    @staticmethod
    def _decode_int16(value: int) -> int:
        unsigned = int(value) & 0xFFFF
        return unsigned - 0x10000 if unsigned & 0x8000 else unsigned
