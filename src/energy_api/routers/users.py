# Author: Jerry Onyango
# Contribution: Boots the FastAPI application, registers domain routers, and serves health and contract endpoints.
from __future__ import annotations

import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from energy_api.security import Principal, get_current_principal, require_roles

router = APIRouter(prefix="/api/v1", tags=["Users"])


def _db_url() -> str:
    raw = os.getenv("EA_DATABASE_URL", "postgresql://energyallocation:energyallocation@localhost:5432/energyallocation")
    return raw.replace("postgresql+psycopg://", "postgresql://")


def _connect():
    import psycopg
    return psycopg.connect(_db_url(), autocommit=True)


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    status: str
    created_at: str


class UserCreateIn(BaseModel):
    email: str
    full_name: str | None = None
    role: str


class UserUpdateIn(BaseModel):
    full_name: str | None = None
    role: str | None = None
    status: str | None = None


class InvitationIn(BaseModel):
    email: str
    role: str


class InvitationOut(BaseModel):
    id: str
    email: str
    role: str
    expires_at: str
    accepted_at: str | None


def _log_audit(
    actor_id: str | None,
    action: str,
    target_user_id: str | None = None,
    target_email: str | None = None,
    details: dict | None = None,
) -> None:
    try:
        with _connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO user_audit_log(actor_id, action, target_user_id, target_email, details)
                    VALUES (%s::uuid, %s, %s::uuid, %s, %s)
                    """,
                    (actor_id, action, target_user_id, target_email, details),
                )
    except Exception:
        pass


@router.get("/users")
def list_users(
    principal: Principal = Depends(
        require_roles("client_admin", "admin", "owner")
    ),
) -> dict[str, Any]:
    org_id = getattr(principal, "organization_id", None)
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    u.id::text,
                    u.email,
                    COALESCE(u.full_name, '') AS full_name,
                    COALESCE(m.role, 'viewer') AS role,
                    u.status,
                    u.created_at::text
                FROM users u
                JOIN user_memberships m ON m.user_id = u.id
                WHERE m.organization_id::text = %s
                ORDER BY u.created_at DESC
                """,
                (org_id,),
            )
            rows = cur.fetchall()

    return {
        "items": [
            {
                "id": row[0],
                "email": row[1],
                "full_name": row[2],
                "role": row[3],
                "status": row[4],
                "created_at": row[5],
            }
            for row in rows
        ]
    }


@router.get("/users/{user_id}")
def get_user(
    user_id: str,
    principal: Principal = Depends(
        require_roles("client_admin", "admin", "owner", "facility_manager")
    ),
) -> dict[str, Any]:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    u.id::text,
                    u.email,
                    COALESCE(u.full_name, '') AS full_name,
                    COALESCE(m.role, 'viewer') AS role,
                    u.status,
                    u.created_at::text,
                    m.organization_id::text
                FROM users u
                JOIN user_memberships m ON m.user_id = u.id
                WHERE u.id::text = %s
                LIMIT 1
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": row[0],
        "email": row[1],
        "full_name": row[2],
        "role": row[3],
        "status": row[4],
        "created_at": row[5],
        "organization_id": row[6],
    }


@router.patch("/users/{user_id}")
def update_user(
    user_id: str,
    payload: dict[str, Any],
    principal: Principal = Depends(
        require_roles("client_admin", "admin", "owner")
    ),
) -> dict[str, Any]:
    allowed_fields = {"full_name", "role", "status"}
    updates = {k: v for k, v in payload.items() if k in allowed_fields and v is not None}
    
    if not updates:
        raise HTTPException(status_code=400, detail="No valid fields to update")

    user_id_principal = str(principal.subject)
    
    if user_id == user_id_principal:
        if "status" in updates and updates["status"] != "active":
            raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
        if "role" in updates:
            raise HTTPException(status_code=400, detail="Cannot change your own role")

    with _connect() as conn:
        with conn.cursor() as cur:
            if "full_name" in updates:
                cur.execute(
                    "UPDATE users SET full_name = %s WHERE id::text = %s",
                    (updates["full_name"], user_id),
                )

            if "status" in updates:
                cur.execute(
                    "UPDATE users SET status = %s WHERE id::text = %s",
                    (updates["status"], user_id),
                )

            if "role" in updates:
                cur.execute(
                    """
                    UPDATE user_memberships 
                    SET role = %s 
                    WHERE user_id::text = %s
                    """,
                    (updates["role"], user_id),
                )

            cur.execute(
                """
                SELECT 
                    u.id::text,
                    u.email,
                    COALESCE(u.full_name, '') AS full_name,
                    COALESCE(m.role, 'viewer') AS role,
                    u.status,
                    u.created_at::text
                FROM users u
                JOIN user_memberships m ON m.user_id = u.id
                WHERE u.id::text = %s
                LIMIT 1
                """,
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")

    _log_audit(
        actor_id=user_id_principal,
        action="update_user",
        target_user_id=user_id,
        details={"updates": updates},
    )

    return {
        "id": row[0],
        "email": row[1],
        "full_name": row[2],
        "role": row[3],
        "status": row[4],
        "created_at": row[5],
    }


@router.post("/users/invite")
def invite_user(
    payload: InvitationIn,
    principal: Principal = Depends(
        require_roles("client_admin", "admin", "owner")
    ),
) -> dict[str, Any]:
    org_id = getattr(principal, "organization_id", None)
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    user_id_principal = str(principal.subject)
    email = payload.email.strip().lower()
    role = payload.role

    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id::text FROM users WHERE lower(email) = lower(%s)",
                (email,),
            )
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="User with this email already exists")

            cur.execute(
                "SELECT 1 FROM user_invitations WHERE lower(email) = lower(%s) AND accepted_at IS NULL",
                (email,),
            )
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Pending invitation already exists for this email")

            token = secrets.token_urlsafe(32)
            expires_at = datetime.now(UTC) + timedelta(days=7)

            cur.execute(
                """
                INSERT INTO user_invitations(
                    organization_id, email, role, invited_by, token, expires_at
                ) VALUES (%s::uuid, %s, %s, %s::uuid, %s, %s)
                RETURNING id::text, email, role, expires_at::text, created_at::text
                """,
                (org_id, email, role, user_id_principal, token, expires_at),
            )
            row = cur.fetchone()

    _log_audit(
        actor_id=user_id_principal,
        action="invite_user",
        target_email=email,
        details={"role": role},
    )

    return {
        "id": row[0],
        "email": row[1],
        "role": row[2],
        "expires_at": row[3],
        "invitation_link": f"/invite/{token}",
        "token": token,
    }


@router.get("/users/invitations")
def list_invitations(
    principal: Principal = Depends(
        require_roles("client_admin", "admin", "owner")
    ),
) -> dict[str, Any]:
    org_id = getattr(principal, "organization_id", None)
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    id::text,
                    email,
                    role,
                    expires_at::text,
                    accepted_at::text,
                    created_at::text
                FROM user_invitations
                WHERE organization_id::text = %s
                ORDER BY created_at DESC
                """,
                (org_id,),
            )
            rows = cur.fetchall()

    return {
        "items": [
            {
                "id": row[0],
                "email": row[1],
                "role": row[2],
                "expires_at": row[3],
                "accepted_at": row[4],
                "created_at": row[5],
                "is_expired": datetime.fromisoformat(row[3].replace("Z", "+00:00")) < datetime.now(UTC),
            }
            for row in rows
        ]
    }


@router.delete("/users/invitations/{invitation_id}")
def revoke_invitation(
    invitation_id: str,
    principal: Principal = Depends(
        require_roles("client_admin", "admin", "owner")
    ),
) -> dict[str, str]:
    user_id_principal = str(principal.subject)

    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM user_invitations WHERE id::text = %s RETURNING email",
                (invitation_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Invitation not found")

    _log_audit(
        actor_id=user_id_principal,
        action="revoke_invitation",
        target_email=row[0],
    )

    return {"status": "ok"}


@router.post("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: str,
    principal: Principal = Depends(
        require_roles("client_admin", "admin", "owner")
    ),
) -> dict[str, Any]:
    user_id_principal = str(principal.subject)
    
    if user_id == user_id_principal:
        raise HTTPException(status_code=400, detail="Cannot deactivate your own account")

    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET status = 'inactive' WHERE id::text = %s RETURNING id::text",
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")

    _log_audit(
        actor_id=user_id_principal,
        action="deactivate_user",
        target_user_id=user_id,
    )

    return {"status": "ok", "message": "User deactivated"}


@router.post("/users/{user_id}/reactivate")
def reactivate_user(
    user_id: str,
    principal: Principal = Depends(
        require_roles("client_admin", "admin", "owner")
    ),
) -> dict[str, Any]:
    user_id_principal = str(principal.subject)

    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET status = 'active' WHERE id::text = %s RETURNING id::text",
                (user_id,),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="User not found")

    _log_audit(
        actor_id=user_id_principal,
        action="reactivate_user",
        target_user_id=user_id,
    )

    return {"status": "ok", "message": "User reactivated"}


@router.get("/users/audit-log")
def get_audit_log(
    limit: int = 100,
    principal: Principal = Depends(
        require_roles("client_admin", "admin", "owner")
    ),
) -> dict[str, Any]:
    with _connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    a.id::text,
                    a.action,
                    a.target_user_id::text,
                    a.target_email,
                    a.details,
                    a.created_at::text,
                    u.full_name AS actor_name
                FROM user_audit_log a
                LEFT JOIN users u ON u.id = a.actor_id
                ORDER BY a.created_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()

    return {
        "items": [
            {
                "id": row[0],
                "action": row[1],
                "target_user_id": row[2],
                "target_email": row[3],
                "details": row[4],
                "created_at": row[5],
                "actor_name": row[6],
            }
            for row in rows
        ]
    }
