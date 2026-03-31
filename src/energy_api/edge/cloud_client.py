# Author: Jerry Onyango
# Contribution: Publishes edge telemetry records to the cloud ingest API with optional bearer authentication.

from __future__ import annotations

import logging
from typing import Any

import httpx


logger = logging.getLogger("energy_api.edge.cloud_client")


class EdgeCloudClient:
    def __init__(
        self,
        base_url: str,
        timeout_seconds: float = 10.0,
        bearer_token: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth_mode = "none"
        headers: dict[str, str] = {}
        # Deterministic precedence: service API key is primary for edge runtime ingest.
        if api_key:
            headers["X-API-Key"] = api_key
            self.auth_mode = "api_key"
        elif bearer_token:
            headers["Authorization"] = f"Bearer {bearer_token}"
            self.auth_mode = "bearer"
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout_seconds, headers=headers)

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
        logger.info(
            "edge_ingest_request auth_mode=%s site_id=%s gateway_id=%s canonical_key=%s",
            self.auth_mode,
            site_id,
            gateway_id,
            payload.get("canonical_key"),
        )
        try:
            response = self._client.post("/api/v1/telemetry/ingest", json=body)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code if exc.response is not None else "unknown"
            logger.warning(
                "edge_ingest_failed auth_mode=%s site_id=%s gateway_id=%s status=%s",
                self.auth_mode,
                site_id,
                gateway_id,
                status_code,
            )
            raise

        response_body = response.json()
        logger.info(
            "edge_ingest_success auth_mode=%s site_id=%s gateway_id=%s received=%s inserted=%s deduplicated=%s",
            self.auth_mode,
            site_id,
            gateway_id,
            response_body.get("received"),
            response_body.get("inserted"),
            response_body.get("deduplicated"),
        )
        return response_body

    def close(self) -> None:
        self._client.close()
