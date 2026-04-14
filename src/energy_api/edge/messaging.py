# Author: Jerry Onyango
# Contribution: Defines pluggable messaging transport abstraction for edge-to-cloud communication.
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, UTC
from typing import Any

from .cloud_client import EdgeCloudClient

logger = logging.getLogger("energy_api.edge.messaging")

class EdgeMessagingClient(ABC):
    @abstractmethod
    def publish_telemetry(self, site_id: str, gateway_id: str, payload: dict[str, Any]) -> None:
        """Publishes a telemetry record to the cloud."""
        pass

    @abstractmethod
    def publish_command_ack(self, site_id: str, gateway_id: str, command_id: str, status: str, detail: str | None = None) -> None:
        """Publishes a command acknowledgement to the cloud."""
        pass

    @abstractmethod
    def report_heartbeat(self, gateway_id: str, status_payload: dict[str, Any]) -> None:
        """Reports gateway health/heartbeat to the cloud."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Closes the messaging client."""
        pass

class HTTPMessagingClient(EdgeMessagingClient):
    def __init__(self, base_url: str, timeout_seconds: float = 10.0, bearer_token: str | None = None) -> None:
        self._client = EdgeCloudClient(base_url=base_url, timeout_seconds=timeout_seconds, bearer_token=bearer_token)

    def publish_telemetry(self, site_id: str, gateway_id: str, payload: dict[str, Any]) -> None:
        self._client.upload_record(site_id=site_id, gateway_id=gateway_id, payload=payload)

    def publish_command_ack(self, site_id: str, gateway_id: str, command_id: str, status: str, detail: str | None = None) -> None:
        logger.info("http_command_ack_published site_id=%s gateway_id=%s command_id=%s status=%s detail=%s", 
                    site_id, gateway_id, command_id, status, detail)

    def report_heartbeat(self, gateway_id: str, status_payload: dict[str, Any]) -> None:
        try:
            self._client.report_heartbeat(gateway_id, status_payload)
        except Exception as exc:
            logger.warning("http_heartbeat_failed gateway_id=%s error=%s", gateway_id, exc)

    def close(self) -> None:
        self._client.close()

class MQTTMessagingClient(EdgeMessagingClient):
    def __init__(self, host: str, port: int, username: str | None = None, password: str | None = None, use_tls: bool = False) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        try:
            import paho.mqtt.client as mqtt # type: ignore
            self._mqtt_client = mqtt.Client()
            if self.username and self.password:
                self._mqtt_client.username_pw_set(self.username, self.password)
            if self.use_tls:
                self._mqtt_client.tls_set()
            self._mqtt_client.connect(self.host, self.port)
            self._mqtt_client.loop_start()
        except ImportError:
            logger.warning("paho-mqtt not installed, MQTTMessagingClient will operate in mock mode")
            self._mqtt_client = None

    def publish_telemetry(self, site_id: str, gateway_id: str, payload: dict[str, Any]) -> None:
        topic = f"ems/{site_id}/telemetry/{payload.get('canonical_key', 'unknown')}"
        message = json.dumps({
            "gateway_id": gateway_id,
            "ts": payload.get("ts"),
            "value": payload.get("value"),
            "unit": payload.get("unit"),
            "quality": payload.get("quality", "good"),
        })
        if self._mqtt_client:
            self._mqtt_client.publish(topic, message, qos=1)
        else:
            logger.info("mqtt_publish_mock topic=%s message=%s", topic, message)

    def publish_command_ack(self, site_id: str, gateway_id: str, command_id: str, status: str, detail: str | None = None) -> None:
        topic = f"ems/{site_id}/command/ack"
        message = json.dumps({
            "gateway_id": gateway_id,
            "command_id": command_id,
            "status": status,
            "detail": detail,
            "ts": datetime.now(UTC).isoformat()
        })
        if self._mqtt_client:
            self._mqtt_client.publish(topic, message, qos=1)
        else:
            logger.info("mqtt_publish_mock topic=%s message=%s", topic, message)

    def report_heartbeat(self, gateway_id: str, status_payload: dict[str, Any]) -> None:
        topic = f"ems/{gateway_id}/state/current"
        message = json.dumps(status_payload)
        if self._mqtt_client:
            self._mqtt_client.publish(topic, message, qos=1)
        else:
            logger.info("mqtt_publish_mock topic=%s message=%s", topic, message)

    def close(self) -> None:
        if self._mqtt_client:
            self._mqtt_client.loop_stop()
            self._mqtt_client.disconnect()
