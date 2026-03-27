# Author: Jerry Onyango
# Contribution: Implements login, current-user lookup, logout behavior, and development token minting for JWT authentication.
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
import psycopg
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from psycopg.types.json import Jsonb

from energy_api.security import Principal, get_current_principal

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])

ALLOWED_ROLES = {
    "client_admin",
    "facility_manager",
    "energy_analyst",
    "viewer",
    "ops_admin",
    "ml_engineer",
    "customer_success",
    "support_analyst",
    "admin",
    "owner",
    "operator",
}


def _db_url() -> str:
    raw = os.getenv("EA_DATABASE_URL", "postgresql://energyallocation:energyallocation@localhost:5432/energyallocation")
    return raw.replace("postgresql+psycopg://", "postgresql://")


def _connect():
    return psycopg.connect(_db_url(), autocommit=True)


def _ensure_auth_schema() -> None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS password_hash TEXT")


def _ensure_dev_seed_user() -> None:
    if not _is_dev_mode_enabled():
        return

    seed_email = os.getenv("EA_DEV_ADMIN_EMAIL", "admin@ems.local").strip().lower()
    seed_password = os.getenv("EA_DEV_ADMIN_PASSWORD", "admin123!")
    seed_name = os.getenv("EA_DEV_ADMIN_NAME", "EMS Admin")

    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id::text, password_hash FROM users WHERE lower(email) = lower(%s) LIMIT 1", (seed_email,))
            existing_user = cur.fetchone()

            if existing_user:
                user_id = existing_user[0]
                password_hash = existing_user[1]
            else:
                cur.execute(
                    """
                    INSERT INTO users(email, full_name, status)
                    VALUES (%s, %s, 'active')
                    RETURNING id::text, password_hash
                    """,
                    (seed_email, seed_name),
                )
                created_user = cur.fetchone()
                if not created_user:
                    return
                user_id = created_user[0]
                password_hash = created_user[1]

            if not password_hash:
                cur.execute("UPDATE users SET password_hash = %s WHERE id::text = %s", (hash_password(seed_password), user_id))

            cur.execute("SELECT id::text FROM organizations ORDER BY created_at ASC LIMIT 1")
            org = cur.fetchone()
            if org:
                org_id = org[0]
            else:
                cur.execute(
                    """
                    INSERT INTO organizations(name, legal_name, industry, timezone)
                    VALUES ('Local EMS', 'Local EMS', 'energy', 'UTC')
                    RETURNING id::text
                    """
                )
                inserted_org = cur.fetchone()
                if not inserted_org:
                    return
                org_id = inserted_org[0]

            cur.execute(
                """
                SELECT 1
                FROM user_memberships
                WHERE user_id::text = %s AND organization_id::text = %s AND role = 'client_admin'
                LIMIT 1
                """,
                (user_id, org_id),
            )
            membership_exists = cur.fetchone()
            if not membership_exists:
                cur.execute(
                    """
                    INSERT INTO user_memberships(user_id, organization_id, role)
                    VALUES (%s::uuid, %s::uuid, 'client_admin')
                    """,
                    (user_id, org_id),
                )


def hash_password(password: str) -> str:
    iterations = int(os.getenv("EA_PBKDF2_ITERATIONS", "260000"))
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    salt_b64 = base64.b64encode(salt).decode("utf-8")
    digest_b64 = base64.b64encode(digest).decode("utf-8")
    return f"pbkdf2_sha256${iterations}${salt_b64}${digest_b64}"


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith("pbkdf2_sha256$"):
        try:
            _, iterations_raw, salt_b64, digest_b64 = password_hash.split("$", 3)
            iterations = int(iterations_raw)
            salt = base64.b64decode(salt_b64.encode("utf-8"))
            expected_digest = base64.b64decode(digest_b64.encode("utf-8"))
            candidate_digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
            return hmac.compare_digest(candidate_digest, expected_digest)
        except (ValueError, TypeError):
            return False

    if password_hash.startswith("$2"):
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT crypt(%s, %s) = %s", (password, password_hash, password_hash))
                row = cur.fetchone()
                return bool(row and row[0])

    return False


def _is_dev_mode_enabled() -> bool:
    env = os.getenv("EA_ENV", "development")
    return _is_truthy(os.getenv("AUTH_DEV_MODE")) or _is_truthy(os.getenv("EA_ENABLE_DEV_AUTH")) or env == "development"


def create_access_token(user: dict[str, Any]) -> str:
    secret = os.getenv("JWT_SECRET", os.getenv("EA_JWT_SECRET", "dev-secret-change-me"))
    algorithm = os.getenv("JWT_ALGORITHM", os.getenv("EA_JWT_ALGORITHM", "HS256"))
    expires_in_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", os.getenv("EA_JWT_EXP_MIN", "60")))
    now = datetime.now(UTC)
    payload = {
        "sub": str(user["id"]),
        "email": user["email"],
        "role": user["role"],
        "roles": [user["role"]],
        "organization_id": str(user["organization_id"]),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expires_in_minutes)).timestamp()),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def _find_user_for_login(email: str) -> dict[str, Any] | None:
    _ensure_auth_schema()
    _ensure_dev_seed_user()
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  u.id::text,
                  u.email,
                  COALESCE(u.full_name, '') AS full_name,
                  COALESCE(m.role, 'viewer') AS role,
                  m.organization_id::text,
                  u.password_hash
                FROM users u
                LEFT JOIN LATERAL (
                  SELECT role, organization_id
                  FROM user_memberships
                  WHERE user_id = u.id
                  ORDER BY created_at ASC
                  LIMIT 1
                ) m ON true
                WHERE lower(u.email) = lower(%s)
                  AND u.status = 'active'
                LIMIT 1
                """,
                (email,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "email": row[1],
                "full_name": row[2],
                "role": row[3],
                "organization_id": row[4],
                "password_hash": row[5],
            }


def _get_user_by_id(user_id: str) -> dict[str, Any] | None:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                  u.id::text,
                  u.email,
                  COALESCE(u.full_name, '') AS full_name,
                  COALESCE(m.role, 'viewer') AS role,
                  m.organization_id::text
                FROM users u
                LEFT JOIN LATERAL (
                  SELECT role, organization_id
                  FROM user_memberships
                  WHERE user_id = u.id
                  ORDER BY created_at ASC
                  LIMIT 1
                ) m ON true
                WHERE u.id::text = %s
                  AND u.status = 'active'
                LIMIT 1
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "email": row[1],
                "full_name": row[2],
                "role": row[3],
                "organization_id": row[4],
            }


def _is_truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


@router.post("/dev-token")
def mint_dev_token(payload: dict[str, Any]) -> dict[str, Any]:
    if not _is_dev_mode_enabled():
        raise HTTPException(status_code=404, detail="Not found")

    secret = os.getenv("EA_JWT_SECRET", "dev-secret-change-me")
    algorithm = os.getenv("EA_JWT_ALGORITHM", "HS256")
    expiry_minutes = int(os.getenv("EA_JWT_EXP_MIN", "120"))
    requested_roles = payload.get("roles", ["viewer"])
    if isinstance(requested_roles, str):
        requested_roles = [requested_roles]

    roles = [str(role) for role in requested_roles if str(role) in ALLOWED_ROLES]
    if not roles:
        raise HTTPException(status_code=400, detail="At least one valid role is required")

    now = datetime.now(UTC)
    claims = {
        "sub": payload.get("sub", "usr_dev"),
        "roles": roles,
        "client_id": payload.get("client_id"),
        "facility_ids": payload.get("facility_ids", []),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=expiry_minutes)).timestamp()),
    }
    token = jwt.encode(claims, secret, algorithm=algorithm)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_minutes": expiry_minutes,
        "claims": claims,
    }



@router.post("/signup")
def signup(payload: dict[str, Any]) -> dict[str, Any]:
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    full_name = str(payload.get("name", "")).strip()

    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password are required")

    with _connect() as conn:
        with conn.cursor() as cur:
            # Check if user exists
            cur.execute("SELECT id FROM users WHERE lower(email) = lower(%s)", (email,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="User already exists")

            # Get default organization
            cur.execute("SELECT id::text FROM organizations ORDER BY created_at ASC LIMIT 1")
            org = cur.fetchone()
            if not org:
                # Create one if missing
                cur.execute(
                    "INSERT INTO organizations(name, legal_name, industry) VALUES ('Default Org', 'Default Org', 'energy') RETURNING id::text"
                )
                org = cur.fetchone()

            org_id = org[0]

            # Create user
            cur.execute(
                """
                INSERT INTO users(email, full_name, password_hash, status)
                VALUES (%s, %s, %s, 'active')
                RETURNING id::text
                """,
                (email, full_name or email.split("@")[0], hash_password(password)),
            )
            user_id = cur.fetchone()[0]

            # Create membership
            cur.execute(
                "INSERT INTO user_memberships(user_id, organization_id, role) VALUES (%s::uuid, %s::uuid, 'client_admin')",
                (user_id, org_id),
            )

    user = _find_user_for_login(email)
    if not user:
        raise HTTPException(status_code=500, detail="Failed to retrieve user after signup")

    token = create_access_token(user)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login")
def login(payload: dict[str, Any]) -> dict[str, Any]:
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    if not email or not password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user = _find_user_for_login(email)
    if not user or not user.get("password_hash"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
def me(principal: Principal = Depends(get_current_principal)) -> dict[str, Any]:
    user = _get_user_by_id(principal.subject)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.post("/logout")
def logout(_: Principal = Depends(get_current_principal)) -> dict[str, str]:
    return {"status": "ok"}


class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    timezone: str | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


@router.patch("/me")
def update_profile(
    payload: dict[str, Any],
    principal: Principal = Depends(get_current_principal),
) -> dict[str, Any]:
    user_id = principal.subject
    allowed_fields = {"full_name", "timezone"}
    updates = {k: v for k, v in payload.items() if k in allowed_fields and v is not None}

    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    set_clause = ", ".join([f"{k} = %s" for k in updates.keys()])
    values = list(updates.values())
    values.append(user_id)

    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE users SET {set_clause} WHERE id::text = %s RETURNING id::text, email, full_name",
                values,
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")
            return {
                "id": row[0],
                "email": row[1],
                "full_name": row[2],
            }


@router.post("/me/password")
def change_password(
    payload: dict[str, Any],
    principal: Principal = Depends(get_current_principal),
) -> dict[str, str]:
    current_password = payload.get("current_password", "")
    new_password = payload.get("new_password", "")

    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail="Current and new passwords are required")

    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")

    user_id = principal.subject

    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT password_hash FROM users WHERE id::text = %s",
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")

            current_hash = row[0]
            if current_hash and not verify_password(current_password, current_hash):
                raise HTTPException(status_code=401, detail="Current password is incorrect")

            new_hash = hash_password(new_password)
            cur.execute(
                "UPDATE users SET password_hash = %s WHERE id::text = %s",
                (new_hash, user_id),
            )

    return {"status": "ok", "message": "Password changed successfully"}


@router.get("/me/preferences")
def get_preferences(
    principal: Principal = Depends(get_current_principal),
) -> dict[str, Any]:
    user_id = principal.subject
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT preferences FROM user_preferences WHERE user_id::text = %s",
                (user_id,),
            )
            row = cur.fetchone()
            if row and row[0]:
                return row[0]
            return {}


@router.put("/me/preferences")
def update_preferences(
    payload: dict[str, Any],
    principal: Principal = Depends(get_current_principal),
) -> dict[str, Any]:
    user_id = principal.subject

    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_preferences(user_id, preferences)
                VALUES (%s::uuid, %s)
                ON CONFLICT (user_id) DO UPDATE SET preferences = %s
                RETURNING preferences
                """,
                (user_id, Jsonb(payload), Jsonb(payload)),
            )
            row = cur.fetchone()
            return row[0] if row else {}


@router.get("/me/organization")
def get_organization(
    principal: Principal = Depends(get_current_principal),
) -> dict[str, Any]:
    user_id = principal.subject
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT o.id::text, o.name, o.legal_name, o.industry, o.timezone,
                       m.role, o.created_at
                FROM organizations o
                JOIN user_memberships m ON m.organization_id = o.id
                WHERE m.user_id::text = %s
                LIMIT 1
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Organization not found")
            return {
                "id": row[0],
                "name": row[1],
                "legal_name": row[2],
                "industry": row[3],
                "timezone": row[4],
                "role": row[5],
                "created_at": row[6].isoformat() if row[6] else None,
            }


@router.get("/roles")
def list_roles(
    _: Principal = Depends(get_current_principal),
) -> dict[str, list[str]]:
    return {"roles": sorted(ALLOWED_ROLES)}
