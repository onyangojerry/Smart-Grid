# Author: Test Author
# Contribution: Validates failure-path handling in edge cloud client (auth failures, timeouts, network errors).

from __future__ import annotations

import logging
import unittest
from unittest.mock import MagicMock, patch

import httpx

from energy_api.edge.cloud_client import EdgeCloudClient
from energy_api.edge.failures import AuthFailure, TransportFailure, TransientServerError


class TestCloudClientFailurePaths(unittest.TestCase):
    """
    PHASE 2: Failure-Path Validation Tests
    
    These tests capture evidence of current logging gaps:
    - GAP 1: 401/403 not distinguished from other HTTP errors
    - GAP 2: Connection timeouts/network failures not caught properly
    - GAP 3: Replay stores generic str(exc) without failure classification
    """

    @patch("energy_api.edge.cloud_client.httpx.Client")
    def test_invalid_api_key_returns_401_captured_as_http_error(self, mock_client_cls) -> None:
        """
        Validates: Invalid API key returns 401 Unauthorized.
        Current behavior: Caught as HTTPStatusError, logged as generic "edge_ingest_failed" with status code.
        GAP: No distinction that this is an auth failure that should NOT retry.
        Evidence: Logs show "status=401" but NO "failure_class=auth_failure" or "should_retry=false"
        """
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="Unauthorized",
            request=MagicMock(),
            response=mock_response,
        )
        
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_cls.return_value = mock_client_instance
        
        client = EdgeCloudClient(
            base_url="http://api:8000",
            timeout_seconds=5.0,
            api_key="invalid-ops-key",
        )
        
        # Execute: attempt ingest with invalid key
        # Expected: AuthFailure raised; logged with failure_class=auth_failure
        with self.assertRaises(AuthFailure) as cm:
            client.upload_record(
                site_id="site1",
                gateway_id="gw1",
                payload={"canonical_key": "battery_soc", "value": 85.0, "timestamp": "2026-03-31T00:00:00Z"}
            )
        
        # Verify: Exception captured (logs shown in pytest output as "Captured log call")
        self.assertIn("401", str(cm.exception))

    @patch("energy_api.edge.cloud_client.httpx.Client")
    def test_api_unavailable_connection_timeout_not_caught(self, mock_client_cls) -> None:
        """
        Validates: Connection timeout when API is unavailable.
        Current behavior: httpx.ConnectError is NOT caught in cloud_client.py → propagates to replay.
        GAP: Replay's generic Exception handler converts to str(exc) without classification.
        """
        mock_client_instance = MagicMock()
        mock_client_instance.post.side_effect = httpx.ConnectError("Failed to connect to api:8000")
        mock_client_cls.return_value = mock_client_instance
        
        client = EdgeCloudClient(
            base_url="http://api:8000",
            timeout_seconds=5.0,
            api_key="ops-key",
        )
        
        # Execute: attempt ingest when API is unreachable
        # Expected: TransportFailure raised
        with self.assertRaises(TransportFailure):
            client.upload_record(
                site_id="site1",
                gateway_id="gw1",
                payload={"canonical_key": "battery_soc", "value": 85.0, "timestamp": "2026-03-31T00:00:00Z"}
            )

    @patch("energy_api.edge.cloud_client.httpx.Client")
    def test_bearer_fallback_when_api_key_absent_still_fails_on_401(self, mock_client_cls) -> None:
        """
        Validates: Bearer token used as fallback when API key absent.
        Current behavior: Falls through to no-auth (no bearer sent) if bearer_token is None/empty.
        GAP: No observability of fallback failure reason if bearer token is invalid.
        """
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="Unauthorized",
            request=MagicMock(),
            response=mock_response,
        )
        
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_cls.return_value = mock_client_instance
        
        client = EdgeCloudClient(
            base_url="http://api:8000",
            timeout_seconds=5.0,
            api_key=None,  # Force fallback to bearer
            bearer_token="invalid-jwt-token",
        )
        
        # Execute: attempt ingest with invalid bearer token
        # Expected: AuthFailure raised
        with self.assertRaises(AuthFailure) as cm:
            client.upload_record(
                site_id="site1",
                gateway_id="gw1",
                payload={"canonical_key": "battery_soc", "value": 85.0, "timestamp": "2026-03-31T00:00:00Z"}
            )
        
        # Verify: 401 response captured
        self.assertIn("401", str(cm.exception))

    @patch("energy_api.edge.cloud_client.httpx.Client")
    def test_http_500_server_error_grouped_with_auth_error(self, mock_client_cls) -> None:
        """
        Validates: Server error (500) response.
        Current behavior: HTTPStatusError caught generically, logged with status code but no error classification.
        GAP: Cannot distinguish 500 (retryable) from 401 (not retryable) — replay treats equally.
        """
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="Internal Server Error",
            request=MagicMock(),
            response=mock_response,
        )
        
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_cls.return_value = mock_client_instance
        
        client = EdgeCloudClient(
            base_url="http://api:8000",
            timeout_seconds=5.0,
            api_key="ops-key",
        )
        
        # Execute: attempt ingest when API returns 500
        # Expected: TransientServerError raised
        with self.assertRaises(TransientServerError) as cm:
            client.upload_record(
                site_id="site1",
                gateway_id="gw1",
                payload={"canonical_key": "battery_soc", "value": 85.0, "timestamp": "2026-03-31T00:00:00Z"}
            )
        
        # Verify: 500 response captured
        self.assertIn("500", str(cm.exception))

    @patch("energy_api.edge.cloud_client.httpx.Client")
    def test_no_auth_headers_sent_when_both_absent(self, mock_client_cls) -> None:
        """
        Validates: Request proceeds with no auth headers when both api_key and bearer_token absent.
        This will hit the API endpoint which expects auth → 401.
        """
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="Unauthorized",
            request=MagicMock(),
            response=mock_response,
        )
        
        mock_client_instance = MagicMock()
        mock_client_instance.post.return_value = mock_response
        mock_client_cls.return_value = mock_client_instance
        
        client = EdgeCloudClient(
            base_url="http://api:8000",
            timeout_seconds=5.0,
            api_key=None,
            bearer_token=None,
        )
        
        # Execute: attempt ingest with no credentials
        # Expected: AuthFailure raised
        with self.assertRaises(AuthFailure) as cm:
            client.upload_record(
                site_id="site1",
                gateway_id="gw1",
                payload={"canonical_key": "battery_soc", "value": 85.0, "timestamp": "2026-03-31T00:00:00Z"}
            )
        
        # Verify: 401 response
        self.assertIn("401", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
