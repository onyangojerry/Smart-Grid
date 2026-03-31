# Author: Jerry Onyango
# Contribution: Publishes edge telemetry records to the cloud ingest API with optional bearer authentication.

from __future__ import annotations

import logging
from typing import Any

import httpx

from .failures import AuthFailure, EdgeIngestFailure, TransientServerError, TransportFailure, ValidationFailure


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
                "edge_ingest_failed auth_mode=%s site_id=%s gateway_id=%s status=%s failure_class=%s",
                self.auth_mode,
                site_id,
                gateway_id,
                status_code,
                self._classify_http_error(status_code),
            )
            # Re-raise as classified exception for replay to handle appropriately
            raise self._make_classified_exception(status_code) from exc
        except httpx.ConnectError as exc:
            logger.warning(
                "edge_ingest_failed auth_mode=%s site_id=%s gateway_id=%s failure_class=transport_failure error=%s",
                self.auth_mode,
                site_id,
                gateway_id,
                str(exc)[:100],
            )
            raise TransportFailure(f"Connection failed: {exc}") from exc
        except httpx.RequestError as exc:
            logger.warning(
                "edge_ingest_failed auth_mode=%s site_id=%s gateway_id=%s failure_class=transport_failure error=%s",
                self.auth_mode,
                site_id,
                gateway_id,
                str(exc)[:100],
            )
            raise TransportFailure(f"Request failed: {exc}") from exc

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

    @staticmethod
    def _classify_http_error(status_code: int | str) -> str:
        """Classify HTTP error code for retry strategy."""
        status = int(status_code) if isinstance(status_code, str) else status_code
        if status in {401, 403}:
            return "auth_failure"
        if status in {400, 422}:
            return "validation_failure"
        if status in {429, 500, 502, 503, 504}:
            return "transient_server_error"
        return "unknown_http_error"

    @staticmethod
    def _make_classified_exception(status_code: int | str) -> EdgeIngestFailure:
        """Create appropriate exception based on HTTP status code."""
        status = int(status_code) if isinstance(status_code, str) else status_code
        if status in {401, 403}:
            return AuthFailure(f"Authentication failure: HTTP {status}", http_status=status)
        if status in {400, 422}:
            return ValidationFailure(f"Validation failure: HTTP {status}", http_status=status)
        if status in {429, 500, 502, 503, 504}:
            return TransientServerError(f"Transient server error: HTTP {status}", http_status=status)
        return EdgeIngestFailure(f"Ingest failed: HTTP {status}", http_status=status)

    def close(self) -> None:
        self._client.close()
