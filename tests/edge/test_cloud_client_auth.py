# Author: Jerry Onyango
# Contribution: Verifies edge cloud client auth header wiring for bearer and service API key modes.
from __future__ import annotations

import unittest
from unittest.mock import patch

from energy_api.edge.cloud_client import EdgeCloudClient


class TestCloudClientAuth(unittest.TestCase):
    @patch("energy_api.edge.cloud_client.httpx.Client")
    def test_api_key_takes_precedence_over_bearer(self, mock_client_cls) -> None:
        EdgeCloudClient(
            base_url="http://api:8000",
            timeout_seconds=5.0,
            bearer_token="jwt-token",
            api_key="ops-key",
        )

        _, kwargs = mock_client_cls.call_args
        headers = kwargs.get("headers", {})
        self.assertEqual(headers.get("X-API-Key"), "ops-key")
        self.assertNotIn("Authorization", headers)

    @patch("energy_api.edge.cloud_client.httpx.Client")
    def test_bearer_used_when_api_key_absent(self, mock_client_cls) -> None:
        EdgeCloudClient(
            base_url="http://api:8000",
            timeout_seconds=5.0,
            bearer_token="jwt-token",
            api_key=None,
        )

        _, kwargs = mock_client_cls.call_args
        headers = kwargs.get("headers", {})
        self.assertEqual(headers.get("Authorization"), "Bearer jwt-token")
        self.assertNotIn("X-API-Key", headers)


if __name__ == "__main__":
    unittest.main()
