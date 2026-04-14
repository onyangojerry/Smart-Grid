# Author: Jerry Onyango
# Contribution: Implements JWT/API-key authentication, role authorization, and tenant scope enforcement utilities.
from __future__ import annotations

import logging
import os
from secrets import compare_digest
from dataclasses import dataclass
from typing import Iterable

from datetime import datetime, timedelta, UTC
import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


INTERNAL_ROLES = {"ops_admin", "ml_engineer", "support_analyst", "customer_success"}
SUPER_ROLES = {"admin"}
DEFAULT_JWT_SECRET = "dev-secret-change-me"

bearer_scheme = HTTPBearer(auto_error=False)
logger = logging.getLogger("energy_api.security")


def create_access_token(
    subject: str,
    roles: list[str],
    client_id: str | None = None,
    facility_ids: list[str] | None = None,
    expires_in_minutes: int = 60,
) -> str:
    secret = _get_jwt_secret()
    algorithm = os.getenv("EA_JWT_ALGORITHM", "HS256")
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "roles": roles,
        "client_id": client_id,
        "facility_ids": facility_ids or [],
        "iat": now,
        "exp": now + timedelta(minutes=expires_in_minutes),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


@dataclass(frozen=True)
class Principal:
    subject: str
    roles: set[str]
    client_id: str | None
    facility_ids: set[str]
    token_type: str

    @property
    def is_internal(self) -> bool:
        return any(role in INTERNAL_ROLES for role in self.roles)


def _parse_service_keys() -> dict[str, Principal]:
    raw = os.getenv("EA_SERVICE_KEYS", "")
    if not raw:
        return {
            "ops-key": Principal(
                subject="svc_ops",
                roles={"ops_admin"},
                client_id=None,
                facility_ids=set(),
                token_type="service_key",
            ),
            "ml-key": Principal(
                subject="svc_ml",
                roles={"ml_engineer"},
                client_id=None,
                facility_ids=set(),
                token_type="service_key",
            ),
        }

    output: dict[str, Principal] = {}
    for part in raw.split(","):
        segment = part.strip()
        if not segment:
            continue
        key, subject, roles, client = (segment.split(":") + ["", "", "", ""])[:4]
        key = key.strip()
        if not key:
            continue
        role_set = {role.strip() for role in roles.split("|") if role.strip()}
        output[key] = Principal(
            subject=subject or "service_account",
            roles=role_set,
            client_id=client or None,
            facility_ids=set(),
            token_type="service_key",
        )
    return output


def _get_jwt_secret() -> str:
    env = os.getenv("EA_ENV", "development")
    secret = os.getenv("EA_JWT_SECRET", DEFAULT_JWT_SECRET)
    allow_weak_dev_secret = os.getenv("EA_ALLOW_WEAK_JWT_SECRET", "false").lower() == "true"

    if env != "development":
        if secret == DEFAULT_JWT_SECRET or len(secret) < 32:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWT secret misconfigured",
            )
        return secret

    if secret == DEFAULT_JWT_SECRET and not allow_weak_dev_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Set EA_JWT_SECRET or enable EA_ALLOW_WEAK_JWT_SECRET=true for local development",
        )

    return secret


def get_current_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> Principal:
    service_keys = _parse_service_keys()
    if x_api_key:
        for key, principal in service_keys.items():
            if compare_digest(key, x_api_key):
                logger.info("auth_principal_resolved token_type=service_key subject=%s", principal.subject)
                return principal
        logger.warning("auth_service_key_unrecognized")

    if not credentials:
        logger.warning("auth_missing_credentials")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    secret = _get_jwt_secret()
    algorithm = os.getenv("EA_JWT_ALGORITHM", "HS256")
    try:
        claims = jwt.decode(credentials.credentials, secret, algorithms=[algorithm])
    except jwt.InvalidTokenError as exc:
        logger.warning("auth_invalid_jwt")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    roles = claims.get("roles", [])
    if isinstance(roles, str):
        roles = [roles]

    principal = Principal(
        subject=str(claims.get("sub", "unknown")),
        roles={str(role) for role in roles},
        client_id=claims.get("client_id"),
        facility_ids={str(fid) for fid in claims.get("facility_ids", [])},
        token_type="jwt",
    )
    if not principal.roles:
        logger.warning("auth_principal_no_roles subject=%s", principal.subject)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No roles assigned")

    logger.info("auth_principal_resolved token_type=jwt subject=%s", principal.subject)

    return principal


def require_roles(*allowed: str):
    allowed_roles = set(allowed)

    def dependency(principal: Principal = Depends(get_current_principal)) -> Principal:
        if principal.roles & SUPER_ROLES:
            return principal
        if principal.roles.isdisjoint(allowed_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return principal

    return dependency


def enforce_client_scope(principal: Principal, client_id: str) -> None:
    if principal.is_internal:
        return
    if principal.client_id and principal.client_id != client_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Client scope mismatch")


def enforce_facility_scope(
    principal: Principal,
    facility_id: str,
    facility_client_id: str | None,
) -> None:
    if principal.is_internal:
        return

    if principal.facility_ids and facility_id not in principal.facility_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Facility scope mismatch")

    if principal.client_id and facility_client_id and principal.client_id != facility_client_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Facility client scope mismatch")
