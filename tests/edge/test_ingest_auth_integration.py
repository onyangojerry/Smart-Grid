# Author: Jerry Onyango
# Contribution: Integration test for edge cloud client ingest through API auth resolution using service-key authentication.
from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from energy_api.edge.cloud_client import EdgeCloudClient
from energy_api.main import app


class _FakeControlRepository:
    def __init__(self) -> None:
        self.inserted_rows: list[dict[str, object]] = []

    def upsert_site_defaults(self, site_id: str) -> None:
        return None

    def resolve_stream_ids(self, site_id: str, keys: list[str]) -> dict[str, dict[str, str]]:
        return {key: {"id": f"str_{site_id}_{key}", "unit": "kW"} for key in keys}

    def insert_telemetry_points(self, rows: list[dict[str, object]]) -> int:
        self.inserted_rows.extend(rows)
        return len(rows)


class _TestClientHttpxAdapter:
    def __init__(self, base_url: str, timeout: float, headers: dict[str, str], test_client: TestClient) -> None:
        self._headers = headers
        self._test_client = test_client

    def post(self, path: str, json: dict[str, object]):
        return self._test_client.post(path, json=json, headers=self._headers)

    def close(self) -> None:
        return None


class TestIngestAuthIntegration(unittest.TestCase):
    @patch.dict(
        "os.environ",
        {
            "EA_SERVICE_KEYS": "ops-key:svc_ops:ops_admin:",
            "EA_JWT_SECRET": "this-is-a-strong-dev-secret-with-more-than-32-bytes",
        },
        clear=False,
    )
    def test_edge_client_ingests_with_api_key_auth(self) -> None:
        fake_repo = _FakeControlRepository()
        test_client = TestClient(app)

        with patch("energy_api.routers.control_loop.ControlRepository", return_value=fake_repo):
            with patch(
                "energy_api.edge.cloud_client.httpx.Client",
                side_effect=lambda **kwargs: _TestClientHttpxAdapter(test_client=test_client, **kwargs),
            ):
                cloud = EdgeCloudClient(
                    base_url="http://testserver",
                    api_key="ops-key",
                    bearer_token="unused-because-api-key-is-primary",
                )
                response = cloud.upload_record(
                    site_id="site_001",
                    gateway_id="gw_edge_01",
                    payload={
                        "canonical_key": "pv_kw",
                        "ts": "2026-03-30T10:00:00Z",
                        "value": 1.25,
                        "unit": "kW",
                        "quality": "good",
                    },
                )

        self.assertEqual(response["site_id"], "site_001")
        self.assertEqual(response["gateway_id"], "gw_edge_01")
        self.assertEqual(response["received"], 1)
        self.assertEqual(response["inserted"], 1)
        self.assertEqual(cloud.auth_mode, "api_key")
        self.assertEqual(len(fake_repo.inserted_rows), 1)


if __name__ == "__main__":
    unittest.main()
