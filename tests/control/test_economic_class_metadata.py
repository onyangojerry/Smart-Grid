# Author: Test Author
# Contribution: Validates economic_class metadata for v2 reporting extension point.

from __future__ import annotations

import unittest

from energy_api.control.models import ScoredAction, ScoreBreakdown


class TestEconomicClassMetadata(unittest.TestCase):
    """
    PHASE 4: Reporting v2 Prep — Economic Class Metadata
    
    Documents extension point for v2 reporting:
    Commands can now be tagged with economic_class to enable future reporting
    that distinguishes modeled vs neutral vs constrained control commands.
    
    v1 Semantics:
    - "modeled": charge/discharge (primary cost drivers in v1)
    - "neutral": idle/set_mode/set_limit (tracked for observability but baseline-neutral in v1)
    
    v2 Extension Points:
    - "constrained_control": Future demand response / time-of-use constrained commands
    - "atomic": Future atomic operations that cannot be subdivided
    - "grid_service": Future grid services (frequency support, etc.)
    """

    def test_charge_command_classified_as_modeled(self) -> None:
        """Charge commands affect baseline_cost/optimized_cost in v1."""
        economic_class = ScoredAction.classify_economic_intent("charge")
        self.assertEqual(economic_class, "modeled")

    def test_discharge_command_classified_as_modeled(self) -> None:
        """Discharge commands affect baseline_cost/optimized_cost in v1."""
        economic_class = ScoredAction.classify_economic_intent("discharge")
        self.assertEqual(economic_class, "modeled")

    def test_charge_setpoint_command_classified_as_modeled(self) -> None:
        """Charge setpoint (modern) classified as modeled."""
        economic_class = ScoredAction.classify_economic_intent("charge_setpoint_kw")
        self.assertEqual(economic_class, "modeled")

    def test_idle_command_classified_as_neutral(self) -> None:
        """Idle commands are baseline-neutral in v1; tracked for observability."""
        economic_class = ScoredAction.classify_economic_intent("idle")
        self.assertEqual(economic_class, "neutral")

    def test_set_mode_command_classified_as_neutral(self) -> None:
        """Set mode commands are baseline-neutral in v1."""
        economic_class = ScoredAction.classify_economic_intent("set_mode")
        self.assertEqual(economic_class, "neutral")

    def test_set_limit_command_classified_as_neutral(self) -> None:
        """Set limit commands are baseline-neutral in v1."""
        economic_class = ScoredAction.classify_economic_intent("set_limit")
        self.assertEqual(economic_class, "neutral")

    def test_scored_action_carries_economic_class_metadata(self) -> None:
        """Scored actions now carry economic_class for v2 reporting."""
        score = ScoreBreakdown(
            energy_cost=0.1,
            battery_degradation_penalty=0.02,
            reserve_violation_penalty=0.0,
            command_churn_penalty=0.03,
            device_safety_penalty=0.0,
        )
        action = ScoredAction(
            action_type="charge_setpoint_kw",
            target_power_kw=2.5,
            score=score,
            explanation={"test": "data"},
            reason="pv_surplus_charge",
            economic_class="modeled",  # v2 Reporting: can now reference this field
        )

        # Verify: Action carries metadata for v2 reporting
        self.assertEqual(action.economic_class, "modeled")
        self.assertEqual(action.target_power_kw, 2.5)

    def test_v2_extension_point_example_constrained_control(self) -> None:
        """
        Example: v2 could extend with constrained_control class for demand response.
        Currently unused; documented as extension point.
        """
        # Future v2 usage:
        # action = ScoredAction(
        #     action_type="charge_setpoint_kw",
        #     target_power_kw=1.5,
        #     score=...,
        #     explanation=...,
        #     reason="grid_demand_response",
        #     economic_class="constrained_control",  # v2: New class for DR
        # )
        # v2 savings would then report:
        # - modeled_charge: 10 kWh (cost impact)
        # - constrained_charge: 2.5 kWh (grid support, no direct cost)

        # For now, document the extension point
        self.assertTrue(
            hasattr(ScoredAction, "classify_economic_intent"),
            msg="Extension point exists for future v2 classification logic",
        )


if __name__ == "__main__":
    unittest.main()
