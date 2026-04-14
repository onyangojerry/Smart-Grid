# Author: Jerry Onyango
# Contribution: Publishes edge telemetry records to the cloud ingest API with optional bearer authentication.

from __future__ import annotations

from typing import Any

import httpx


class EdgeCloudClient:
    def __init__(self, base_url: str, timeout_seconds: float = 10.0, bearer_token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        headers: dict[str, str] = {}
        if bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"
        self._client = httpx.Client(base_url=self.base_url, timeout_seconds=timeout_seconds, headers=headers)

    def upload_record(self, site_id: str, gateway_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        value = payload.get("value")
        if value is None:
            return {"status": "skipped", "reason": "null_value"}

        body = {
            "site_id": site_id,
            "gateway_id": gateway_id,
            "points": [
                {
                    "canonical_key": payload.get("canonical_key"),
                    "ts": payload.get("ts"),
                    "value": float(value),
                    "unit": payload.get("unit"),
                    "quality": payload.get("quality", "good"),
                }
            ],
        }
        response = self._client.post("/api/v1/telemetry/ingest", json=body)
        response.raise_for_status()
        return response.json()

    def report_heartbeat(self, gateway_id: str, status_payload: dict[str, Any]) -> dict[str, Any]:
        response = self._client.patch(f"/api/v1/gateways/{gateway_id}/heartbeat", json=status_payload)
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        self._client.close()
