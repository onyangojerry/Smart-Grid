# Author: Jerry Onyango
# Contribution: Validates service-key authentication path used by edge ingest in compose/local deployments.
from __future__ import annotations

import unittest
from unittest.mock import patch

from fastapi import HTTPException

from energy_api.security import get_current_principal


class TestSecurityServiceKeyAuth(unittest.TestCase):
    @patch.dict(
        "os.environ",
        {
            "EA_SERVICE_KEYS": "ops-key:svc_ops:ops_admin:",
            "EA_JWT_SECRET": "this-is-a-strong-dev-secret-with-more-than-32-bytes",
        },
        clear=False,
    )
    def test_service_key_returns_principal_without_bearer(self) -> None:
        principal = get_current_principal(credentials=None, x_api_key="ops-key")
        self.assertEqual(principal.subject, "svc_ops")
        self.assertIn("ops_admin", principal.roles)
        self.assertEqual(principal.token_type, "service_key")

    @patch.dict(
        "os.environ",
        {
            "EA_SERVICE_KEYS": "ops-key:svc_ops:ops_admin:",
        },
        clear=False,
    )
    def test_missing_auth_raises_401(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            get_current_principal(credentials=None, x_api_key=None)
        self.assertEqual(ctx.exception.status_code, 401)


if __name__ == "__main__":
    unittest.main()
