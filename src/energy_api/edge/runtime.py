# Author: Jerry Onyango
# Contribution: Orchestrates startup recovery, polling, command processing, reconciliation, and runtime health reporting.
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from .commands import CommandExecutor
from .observability import RuntimeObservability
from .poller import EdgePoller
from .replay import ReplayService
from .storage.sqlite import EdgeSQLiteStore


CommandReconcileFn = Callable[[dict], str]


@dataclass
class StartupRecoveryResult:
    pending_telemetry: int
    unresolved_commands: int
    reconciled_commands: int
    replay_queue_rebuilt: int

# The EdgeRuntime class serves as the central orchestrator for the edge device's 
# operations. It manages the lifecycle of the edge runtime, including startup 
# recovery to handle any pending telemetry or unresolved commands, 
# periodic polling of devices to collect telemetry data, processing of 
# incoming control commands with safety checks and reconciliation, and 
# maintaining observability metrics for monitoring the health and performance 
# of the edge runtime. The run_poll_cycle method is designed to be called in a 
# loop (e.g., every few seconds) to continuously operate the edge runtime, while 
# submit_command can be called by external systems to send control commands to the 
# edge device.

@dataclass
class EdgeRuntime:
    store: EdgeSQLiteStore
    replay: ReplayService
    poller: EdgePoller
    command_executor: CommandExecutor
    site_id: str
    command_reconcile_fn: CommandReconcileFn
    observability: RuntimeObservability | None = None
    _recovery_done: bool = False

    def __post_init__(self) -> None:
        if self.observability is None:
            self.observability = RuntimeObservability()

    def startup_recovery(self) -> StartupRecoveryResult:
        self.store.initialize()

        unsynced = self.store.list_pending_telemetry(limit=100000)
        unresolved = self.store.list_unresolved_commands()

        reconciled = 0
        for command in unresolved:
            self.store.append_reconciliation_log(command["command_id"], "startup_reconcile_begin", "in_progress", None)
            try:
                target_status = self.command_reconcile_fn(command)
                if target_status not in {"queued", "sent", "applying", "acked", "failed"}:
                    target_status = "failed"
                self.store.update_command_status(command["command_id"], target_status)
                self.store.append_reconciliation_log(command["command_id"], "startup_reconcile_finish", target_status, None)
                reconciled += 1
            except Exception as exc:
                self.store.update_command_status(command["command_id"], "failed", error=str(exc))
                self.store.append_reconciliation_log(command["command_id"], "startup_reconcile_error", "failed", str(exc))
                reconciled += 1

        rebuilt = len(self.replay.rebuild_queue_snapshot(limit=100000))
        self._recovery_done = True
        self.observability.record_sync()

        return StartupRecoveryResult(
            pending_telemetry=len(unsynced),
            unresolved_commands=len(unresolved),
            reconciled_commands=reconciled,
            replay_queue_rebuilt=rebuilt,
        )

    def run_poll_cycle(self) -> dict[str, int | bool]:
        if not self._recovery_done:
            raise RuntimeError("startup_recovery must complete before pollers start")

        started = time.perf_counter()
        adapter = getattr(self.poller, "adapter", None)
        if adapter is not None:
            device_id = f"{getattr(adapter, 'host', 'unknown')}:{getattr(adapter, 'port', 'unknown')}"
        else:
            device_id = "unknown:unknown"
        records = self.poller.poll_once()
        self.store.enqueue_telemetry(site_id=self.site_id, records=records)

        poll_latency_ms = (time.perf_counter() - started) * 1000.0
        self.observability.record_poll_latency(poll_latency_ms)

        has_errors = any(record.quality != "good" for record in records)
        self.observability.mark_device_health(device_id, healthy=not has_errors, reason=None if not has_errors else "poll_quality_issue")
        if has_errors:
            self.observability.increment_error("poll_quality_issue")

        replay_result = self.replay.replay_once(limit=500)
        self.observability.record_sync()
        if replay_result["failed"] > 0:
            self.observability.increment_error("replay_failed")

        return {
            "recovery_done": self._recovery_done,
            "records_polled": len(records),
            "replay_sent": replay_result["sent"],
            "replay_failed": replay_result["failed"],
            "replay_remaining": replay_result["remaining"],
        }

    def submit_command(
        self,
        command_id: str,
        payload: dict,
        idempotency_key: str | None = None,
    ) -> dict:
        if payload.get("command_type") not in {
            "charge",
            "discharge",
            "idle",
            "set_limit",
            "set_mode",
            "charge_setpoint_kw",
            "discharge_setpoint_kw",
            "set_grid_limit_kw",
            "set_export_limit_kw",
        }:
            raise ValueError("invalid command_type")

        existing = self.store.get_command(command_id=command_id)
        if existing:
            return {"status": "deduplicated", "command": existing}

        if idempotency_key:
            existing = self.store.get_command(site_id=self.site_id, idempotency_key=idempotency_key)
            if existing:
                return {"status": "deduplicated", "command": existing}

        if self.store.has_unresolved_command(self.site_id):
            return {"status": "blocked", "reason": "previous_unresolved_command"}

        command = self.store.upsert_command(
            command_id=command_id,
            site_id=self.site_id,
            payload=payload,
            status="queued",
            idempotency_key=idempotency_key,
        )
        return {"status": "queued", "command": command}

    def process_command_backlog(self, limit: int = 20) -> dict[str, int]:
        unresolved = self.store.list_unresolved_commands()[:limit]
        processed = 0
        acked = 0
        failed = 0

        for command in unresolved:
            command_id = command["command_id"]
            status = command["status"]

            if self.store.has_unresolved_command(self.site_id, except_command_id=command_id):
                self.store.append_reconciliation_log(command_id, "safety_block", "blocked", "previous_unresolved_command")
                continue

            processed += 1
            self.store.update_command_status(command_id, "applying")

            try:
                if status in {"sent", "applying"}:
                    ok, detail = self.command_executor.reconcile_only(command["payload"])
                else:
                    ok, detail = self.command_executor.execute_and_reconcile(command["payload"])

                if ok:
                    self.store.update_command_status(command_id, "acked")
                    self.store.append_reconciliation_log(command_id, "reconcile", "acked", detail)
                    acked += 1
                else:
                    self.store.update_command_status(command_id, "failed", error=detail)
                    self.store.append_reconciliation_log(command_id, "reconcile", "failed", detail)
                    self.observability.increment_error("command_reconcile_failed")
                    failed += 1
            except Exception as exc:
                self.store.update_command_status(command_id, "failed", error=str(exc))
                self.store.append_reconciliation_log(command_id, "execute_error", "failed", str(exc))
                self.observability.increment_error("command_execute_error")
                failed += 1

        self.observability.record_sync()
        return {"processed": processed, "acked": acked, "failed": failed}

    def health_snapshot(self) -> dict:
        return self.observability.snapshot(
            replay_queue_size=self.store.count_buffered_telemetry(),
            command_backlog=self.store.count_command_backlog(site_id=self.site_id),
        )
