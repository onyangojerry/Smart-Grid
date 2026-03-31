# Author: Jerry Onyango
# Contribution: Supervises edge runtime lifecycle loops, status emission, and graceful shutdown sequencing.

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .config import EdgeServiceSettings
from .runtime import EdgeRuntime


@dataclass
class EdgeRuntimeSupervisor:
    runtime: EdgeRuntime
    settings: EdgeServiceSettings
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("energy_api.edge.supervisor"))

    _stop_event: threading.Event = field(default_factory=threading.Event, init=False)
    _started_at: datetime | None = field(default=None, init=False)
    _last_replay_time: datetime | None = field(default=None, init=False)
    _last_command_time: datetime | None = field(default=None, init=False)
    _degraded: bool = field(default=False, init=False)
    _last_poll_result: dict[str, Any] | None = field(default=None, init=False)
    _last_command_result: dict[str, Any] | None = field(default=None, init=False)

    def run_forever(self) -> None:
        self._started_at = datetime.now(UTC)
        self.logger.info(
            "edge_runtime_supervisor_starting mode=%s site_id=%s gateway_id=%s modbus=%s:%s",
            self.settings.runtime_mode,
            self.settings.site_id,
            self.settings.gateway_id,
            self.settings.modbus_host,
            self.settings.modbus_port,
        )

        recovery = self.runtime.startup_recovery()
        self.logger.info(
            "edge_startup_recovery_complete pending_telemetry=%s unresolved_commands=%s reconciled_commands=%s replay_queue_rebuilt=%s",
            recovery.pending_telemetry,
            recovery.unresolved_commands,
            recovery.reconciled_commands,
            recovery.replay_queue_rebuilt,
        )

        next_status_emit = time.monotonic()
        next_command_cycle = time.monotonic()

        while not self._stop_event.is_set():
            loop_started = time.monotonic()
            try:
                self._last_poll_result = self.runtime.run_poll_cycle()
                self._last_replay_time = datetime.now(UTC)

                if time.monotonic() >= next_command_cycle:
                    self._last_command_result = self.runtime.process_command_backlog(limit=20)
                    self._last_command_time = datetime.now(UTC)
                    next_command_cycle = time.monotonic() + self.settings.command_interval_seconds

                if time.monotonic() >= next_status_emit:
                    snapshot = self.status_snapshot()
                    self._write_status_file(snapshot)
                    self.logger.info("edge_runtime_status %s", json.dumps(snapshot, separators=(",", ":")))
                    next_status_emit = time.monotonic() + self.settings.status_interval_seconds

                self._degraded = False
            except Exception as exc:
                self.runtime.observability.increment_error("supervisor_loop_error")
                self._degraded = True
                self.logger.exception("edge_supervisor_cycle_failed error=%s", exc)
                if not self.settings.continue_on_poll_error:
                    raise

            elapsed = time.monotonic() - loop_started
            remaining = max(0.0, self.settings.poll_interval_seconds - elapsed)
            self._stop_event.wait(timeout=remaining)

        final_snapshot = self.status_snapshot()
        self._write_status_file(final_snapshot)
        self.logger.info("edge_runtime_supervisor_stopped")

    def shutdown(self) -> None:
        self.logger.info("edge_runtime_supervisor_shutdown_requested")
        self._stop_event.set()

    def status_snapshot(self) -> dict[str, Any]:
        health = self.runtime.health_snapshot()
        per_device_health = health.get("per_device_health", {})
        error_counts = health.get("error_counts", {})
        degraded = bool(self._degraded or any(not v.get("healthy", True) for v in per_device_health.values()))

        return {
            "service_started_successfully": self.runtime._recovery_done,
            "runtime_mode": self.settings.runtime_mode,
            "device_profile": self.settings.profile_name,
            "device_enabled": self.settings.device_enabled,
            "read_only_mode": self.settings.read_only_mode,
            "observation_only_mode": self.settings.observation_only_mode,
            "site_id": self.settings.site_id,
            "gateway_id": self.settings.gateway_id,
            "active_devices_count": len(per_device_health),
            "last_poll_time": health.get("last_poll_time"),
            "last_replay_time": self._last_replay_time.isoformat() if self._last_replay_time else None,
            "last_command_cycle_time": self._last_command_time.isoformat() if self._last_command_time else None,
            "unresolved_command_count": health.get("command_backlog", 0),
            "queue_depth": health.get("replay_queue_size", 0),
            "degraded": degraded,
            "fault_state": [k for k, v in error_counts.items() if int(v) > 0],
            "poll": health.get("poll_latency", {}),
            "last_poll_result": self._last_poll_result,
            "last_command_result": self._last_command_result,
            "updated_at": datetime.now(UTC).isoformat(),
        }

    def _write_status_file(self, snapshot: dict[str, Any]) -> None:
        path = Path(self.settings.status_file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(snapshot, indent=2, sort_keys=True), encoding="utf-8")
