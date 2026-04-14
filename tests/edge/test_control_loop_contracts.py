# Author: Jerry Onyango
# Contribution: Verifies control-loop route integrity, manual command construction, and telemetry unit mapping.
from __future__ import annotations

import unittest
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

from energy_api.control.models import ScoredAction
from energy_api.main import app
from energy_api.routers.control_loop import get_telemetry_history, get_telemetry_latest, issue_command


class TestControlLoopContracts(unittest.TestCase):
    def test_duplicate_device_mapping_route_kept_in_edge_router(self) -> None:
        routes = [
            route
            for route in app.routes
            if getattr(route, "path", None) == "/api/v1/devices/{device_id}/mappings"
            and "POST" in getattr(route, "methods", set())
        ]

        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0].endpoint.__module__, "energy_api.routers.edge")
        self.assertEqual(routes[0].endpoint.__name__, "create_point_mapping")

    @patch("energy_api.routers.control_loop.CommandDispatcher")
    @patch("energy_api.routers.control_loop.ControlRepository")
    @patch("energy_api.routers.control_loop.StateEngine")
    @patch("energy_api.routers.control_loop.RuleEngine")
    def test_manual_command_constructs_direct_scored_action(
        self,
        mock_rule_engine_cls,
        mock_state_engine_cls,
        mock_repo_cls,
        mock_dispatcher_cls,
    ) -> None:
        mock_repo = MagicMock()
        mock_repo.get_primary_device_id.return_value = "dev-1"
        mock_repo_cls.return_value = mock_repo

        mock_dispatcher = MagicMock()
        mock_dispatcher.dispatch.return_value = {"status": "sent", "command": {"id": "cmd-1"}}
        mock_dispatcher_cls.return_value = mock_dispatcher

        payload = {
            "command_type": "charge",
            "target_power_kw": 1.5,
            "target_soc": 80.0,
            "reason": "operator_request",
            "idempotency_key": "manual-123",
        }

        result = issue_command("site-1", type("Payload", (), payload)(), _principal={})

        mock_rule_engine_cls.assert_not_called()
        mock_state_engine_cls.assert_not_called()
        mock_repo.get_primary_device_id.assert_called_once_with("site-1")
        mock_dispatcher.dispatch.assert_called_once()

        action = mock_dispatcher.dispatch.call_args.kwargs["action"]
        self.assertIsInstance(action, ScoredAction)
        self.assertEqual(action.score.total, 0.0)
        self.assertEqual(action.explanation["decision"], "manual_command")
        self.assertEqual(action.explanation["operator_intent"], "charge")
        self.assertEqual(action.explanation["reason"], "operator_request")
        self.assertEqual(result["status"], "sent")

    def test_telemetry_latest_uses_canonical_units(self) -> None:
        mock_repo = MagicMock()
        mock_repo.get_latest_state_rows.return_value = {
            "battery_soc": {"value": 50.0, "quality": "good", "ts": datetime(2026, 4, 1, tzinfo=UTC), "unit": None},
            "battery_temp_c": {"value": 31.0, "quality": "suspect", "ts": datetime(2026, 4, 1, tzinfo=UTC), "unit": None},
            "price_import": {"value": 0.21, "quality": "good", "ts": datetime(2026, 4, 1, tzinfo=UTC), "unit": None},
            "inverter_mode": {"value": 2, "quality": "good", "ts": datetime(2026, 4, 1, tzinfo=UTC), "unit": None},
        }

        with patch("energy_api.routers.control_loop.ControlRepository", return_value=mock_repo):
            result = get_telemetry_latest("site-1", _principal={})

        self.assertEqual(result["battery_soc"]["unit"], "%")
        self.assertEqual(result["battery_temp_c"]["unit"], "C")
        self.assertEqual(result["price_import"]["unit"], "EUR/kWh")
        self.assertEqual(result["inverter_mode"]["unit"], "")
        self.assertEqual(result["battery_temp_c"]["quality"], "estimated")

    def test_telemetry_history_uses_canonical_units(self) -> None:
        mock_repo = MagicMock()
        mock_repo.get_telemetry_history.return_value = [
            {
                "canonical_key": "battery_voltage_v",
                "ts": datetime(2026, 4, 1, tzinfo=UTC),
                "value": 52.4,
                "unit": None,
                "quality": "good",
            },
            {
                "canonical_key": "battery_current_a",
                "ts": datetime(2026, 4, 1, tzinfo=UTC),
                "value": -10.2,
                "unit": "",
                "quality": "suspect",
            },
        ]

        with patch("energy_api.routers.control_loop.ControlRepository", return_value=mock_repo):
            result = get_telemetry_history("site-1", key="battery_voltage_v", start=datetime(2026, 4, 1, tzinfo=UTC), end=datetime(2026, 4, 1, tzinfo=UTC), _principal={})

        self.assertEqual(result[0]["unit"], "V")
        self.assertEqual(result[1]["unit"], "A")
        self.assertEqual(result[1]["quality"], "estimated")


if __name__ == "__main__":
    unittest.main()
