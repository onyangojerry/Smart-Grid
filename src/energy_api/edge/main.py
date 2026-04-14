# Author: Jerry Onyango
# Contribution: Boots the edge runtime service, wires dependencies, and manages signal-driven shutdown.

from __future__ import annotations

import logging
import os
import signal
import sys
from types import FrameType
from pathlib import Path # Import Path here

from energy_api.core import configure_logging

from .cloud_client import EdgeCloudClient
from .commands import CommandExecutor
from .config import EdgeServiceSettings
from .modbus_adapter import ModbusAdapter
from .messaging import EdgeMessagingClient, HTTPMessagingClient, MQTTMessagingClient
from .poller import EdgePoller
from .profile_validation import validate_profile
from .replay import ReplayService
from .runtime import EdgeRuntime
from .storage.sqlite import EdgeSQLiteStore
from .supervisor import EdgeRuntimeSupervisor


def run() -> None:
    settings = EdgeServiceSettings.from_env()
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    # Configure logging to file and console
    log_file_path = Path(os.getenv("EDGE_LOG_FILE_PATH", "./data/edge/edge.log"))
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    configure_logging(level=log_level, log_file_path=str(log_file_path))
    logger = logging.getLogger("energy_api.edge.main")

    profile_errors = validate_profile(settings.profile)
    if profile_errors and settings.device_enabled:
        logger.warning("edge_profile_validation_errors profile=%s errors=%s", settings.profile_name, profile_errors)
        if settings.profile_name != "simulated_home_bess":
            raise RuntimeError(f"Invalid profile configuration: {profile_errors}")

    startup_errors = settings.startup_validation_errors()
    if startup_errors:
        raise RuntimeError(f"Invalid startup configuration: {startup_errors}")

    store = EdgeSQLiteStore(settings.sqlite_path)
    adapter = ModbusAdapter(
        host=settings.modbus_host,
        port=settings.modbus_port,
        timeout_seconds=settings.modbus_timeout_seconds,
    )
    poller = EdgePoller(
        adapter=adapter,
        mappings=settings.point_mappings,
        polling_interval_seconds=settings.poll_interval_seconds,
        unit_id=settings.modbus_unit_id,
    )
    allow_writes = settings.device_enabled and (not settings.read_only_mode) and (not settings.observation_only_mode) and settings.profile.supports_writes
    command_executor = CommandExecutor(
        adapter=adapter,
        unit_id=settings.modbus_unit_id,
        profile=settings.profile,
        allow_writes=allow_writes,
    )

    cloud = EdgeCloudClient(
        base_url=settings.api_base_url,
        timeout_seconds=settings.api_timeout_seconds,
        bearer_token=settings.api_bearer_token,
        api_key=settings.api_key,
    )

    if settings.messaging_mode == "mqtt":
        messaging = MQTTMessagingClient(
            host=settings.mqtt_host,
            port=settings.mqtt_port,
            username=settings.mqtt_username,
            password=settings.mqtt_password,
            use_tls=settings.mqtt_use_tls,
        )
    else:
        messaging = HTTPMessagingClient(
            base_url=settings.api_base_url,
            timeout_seconds=settings.api_timeout_seconds,
            bearer_token=settings.api_bearer_token,
        )

    replay = ReplayService(
        store=store,
        upload_fn=lambda site_id, payload: messaging.publish_telemetry(site_id=site_id, gateway_id=settings.gateway_id, payload=payload),
        base_backoff_seconds=settings.replay_base_backoff_seconds,
        max_backoff_seconds=settings.replay_max_backoff_seconds,
    )

    def reconcile_fn(command: dict) -> str:
        try:
            ok, _detail = command_executor.reconcile_only(command.get("payload", {}))
            return "acked" if ok else "failed"
        except Exception:
            return "failed"

    runtime = EdgeRuntime(
        store=store,
        replay=replay,
        poller=poller,
        command_executor=command_executor,
        site_id=settings.site_id,
        command_reconcile_fn=reconcile_fn,
    )
    supervisor = EdgeRuntimeSupervisor(runtime=runtime, settings=settings, messaging=messaging)

    def _handle_signal(signum: int, _frame: FrameType | None) -> None:
        logger.info("edge_signal_received signum=%s", signum)
        supervisor.shutdown()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    try:
        try:
            adapter.connect()
            logger.info(
                "edge_modbus_connected host=%s port=%s profile=%s unit_id=%s unit_id_source=%s profile_default_unit_id=%s write_enabled=%s",
                settings.modbus_host,
                settings.modbus_port,
                settings.profile_name,
                settings.modbus_unit_id,
                settings.modbus_unit_id_source,
                settings.profile_default_unit_id,
                allow_writes,
            )
        except Exception as exc:
            logger.warning("edge_modbus_connect_failed host=%s port=%s error=%s", settings.modbus_host, settings.modbus_port, exc)

        supervisor.run_forever()
    finally:
        messaging.close()
        try:
            adapter.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    run()
