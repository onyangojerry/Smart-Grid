# Author: Test Author
# Contribution: Validates replay failure classification gaps (auth vs transport vs validation).

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from energy_api.edge.failures import AuthFailure, TransportFailure, TransientServerError
from energy_api.edge.replay import ReplayService
from energy_api.edge.storage.sqlite import EdgeSQLiteStore


class TestReplayFailureClassification(unittest.TestCase):
    """
    PHASE 2: Replay Failure Classification Validation
    
    Validates GAP 3: Replay stores generic str(exc) without failure classification.
    Current behavior: All exceptions (auth, transport, validation) stored as strings.
    Extension point: Subclass exceptions to enable failure_class tracking.
    """

    def test_replay_marks_auth_failure_with_failure_class(self) -> None:
        """
        Validates: Auth failure is caught and stored with failure_class field.
        PHASE 3 Result: failure_class column now tracks the failure category.
        """
        mock_store = MagicMock(spec=EdgeSQLiteStore)
        mock_store.list_pending_telemetry.return_value = [
            {
                "id": 1001,
                "site_id": "site1",
                "payload": {"canonical_key": "battery_soc", "value": 85.0, "timestamp": "2026-03-31T00:00:00Z"},
                "attempt_count": 0,
            }
        ]
        
        def upload_fn_auth_failure(site_id: str, record: dict) -> None:
            # Simulate auth failure
            raise AuthFailure("Authentication failure: HTTP 401", http_status=401)
        
        replay = ReplayService(store=mock_store, upload_fn=upload_fn_auth_failure)
        result = replay.replay_once(limit=100)
        
        # Verify: Failure recorded
        self.assertEqual(result["failed"], 1)
        self.assertEqual(result["sent"], 0)
        
        # Verify: failure_class tracked in result breakdown
        self.assertIn("auth_failure", result["failed_by_class"])
        self.assertEqual(result["failed_by_class"]["auth_failure"], 1)
        
        # Verify: mark_telemetry_retry called with failure_class
        mock_store.mark_telemetry_retry.assert_called_once()
        call_args = mock_store.mark_telemetry_retry.call_args
        failure_class = call_args.kwargs.get("failure_class")
        self.assertEqual(failure_class, "auth_failure")

    def test_replay_marks_transport_failure_with_failure_class(self) -> None:
        """
        Validates: Transport failure is caught and stored with failure_class field.
        PHASE 3 Result: failure_class column distinguishes transport from auth failure.
        """
        mock_store = MagicMock(spec=EdgeSQLiteStore)
        mock_store.list_pending_telemetry.return_value = [
            {
                "id": 1002,
                "site_id": "site1",
                "payload": {"canonical_key": "battery_soc", "value": 85.0, "timestamp": "2026-03-31T00:00:00Z"},
                "attempt_count": 0,
            }
        ]
        
        def upload_fn_timeout(site_id: str, record: dict) -> None:
            # Simulate connection timeout
            raise TransportFailure("Connection failed: Unable to reach api:8000")
        
        replay = ReplayService(store=mock_store, upload_fn=upload_fn_timeout)
        result = replay.replay_once(limit=100)
        
        # Verify: Failure recorded
        self.assertEqual(result["failed"], 1)
        
        # Verify: failure_class tracked as transport_failure
        self.assertIn("transport_failure", result["failed_by_class"])
        self.assertEqual(result["failed_by_class"]["transport_failure"], 1)
        
        # Verify: Backoff applied for transient failure (should be exponential)
        mock_store.mark_telemetry_retry.assert_called_once()
        call_args = mock_store.mark_telemetry_retry.call_args
        failure_class = call_args.kwargs.get("failure_class")
        backoff_seconds = call_args.kwargs.get("backoff_seconds")
        
        self.assertEqual(failure_class, "transport_failure")
        # First attempt (attempt_count=1) should have backoff=2
        self.assertEqual(backoff_seconds, 2)

    def test_replay_backoff_strategy_differs_by_failure_class(self) -> None:
        """
        Validates: Backoff calculation now depends on failure_class.
        PHASE 3 Result: Auth failures get max backoff (no retry); transport failures get exponential backoff.
        """
        mock_store = MagicMock(spec=EdgeSQLiteStore)
        mock_store.list_pending_telemetry.return_value = [
            {
                "id": 1001,
                "site_id": "site1",
                "payload": {"canonical_key": "battery_soc", "value": 85.0, "timestamp": "2026-03-31T00:00:00Z"},
                "attempt_count": 0,  # First attempt
            }
        ]
        
        # Test 1: Auth failure should get max backoff (do not retry)
        def upload_fn_auth(site_id: str, record: dict) -> None:
            raise AuthFailure("Unauthorized", http_status=401)
        
        replay = ReplayService(store=mock_store, upload_fn=upload_fn_auth)
        replay.replay_once(limit=100)
        
        call_args_auth = mock_store.mark_telemetry_retry.call_args
        backoff_auth = call_args_auth.kwargs.get("backoff_seconds")
        
        # Auth failure should get 999999 (do not retry signal)
        self.assertEqual(backoff_auth, 999999, msg="Auth failure should signal do-not-retry")
        
        # Test 2: Transport failure should get exponential backoff
        mock_store.reset_mock()
        mock_store.list_pending_telemetry.return_value = [
            {
                "id": 1002,
                "site_id": "site1",
                "payload": {"canonical_key": "battery_soc", "value": 85.0, "timestamp": "2026-03-31T00:00:00Z"},
                "attempt_count": 0,  # First attempt
            }
        ]
        
        def upload_fn_transport(site_id: str, record: dict) -> None:
            raise TransportFailure("Connection timeout")
        
        replay = ReplayService(store=mock_store, upload_fn=upload_fn_transport)
        replay.replay_once(limit=100)
        
        call_args_transport = mock_store.mark_telemetry_retry.call_args
        backoff_transport = call_args_transport.kwargs.get("backoff_seconds")
        
        # Transport failure at attempt 1 should get 2 seconds (2^0 = 1, then *2)
        self.assertEqual(backoff_transport, 2, msg="Transport failure should use exponential backoff")


if __name__ == "__main__":
    unittest.main()
