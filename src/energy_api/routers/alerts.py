# Author: Jerry Onyango
# Contribution: Boots the FastAPI application, registers domain routers, and serves health and contract endpoints.
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from energy_api.control import ControlRepository
from energy_api.security import require_roles

router = APIRouter(prefix="/api/v1", tags=["Alerts"])


class AlertCreateIn(BaseModel):
    alert_type: str
    severity: str = Field(pattern="^(info|warning|critical)$")
    title: str
    message: str
    source_key: str | None = None
    threshold_value: float | None = None
    actual_value: float | None = None


class AlertUpdateIn(BaseModel):
    state: str = Field(pattern="^(acknowledged|resolved)$")


@router.post("/sites/{site_id}/alerts")
def create_alert(
    site_id: str,
    payload: AlertCreateIn,
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "facility_manager", "ops_admin", "ml_engineer")
    ),
) -> dict[str, Any]:
    repo = ControlRepository()
    if not repo.get_site(site_id):
        raise HTTPException(status_code=404, detail="site not found")
    return repo.create_alert(
        site_id=site_id,
        alert_type=payload.alert_type,
        severity=payload.severity,
        title=payload.title,
        message=payload.message,
        source_key=payload.source_key,
        threshold_value=payload.threshold_value,
        actual_value=payload.actual_value,
    )


@router.get("/sites/{site_id}/alerts")
def list_alerts(
    site_id: str,
    state: str | None = Query(None, pattern="^(open|acknowledged|resolved)$"),
    limit: int = Query(100, ge=1, le=500),
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "facility_manager", "energy_analyst", "viewer", "ops_admin", "ml_engineer")
    ),
) -> dict[str, Any]:
    repo = ControlRepository()
    if not repo.get_site(site_id):
        raise HTTPException(status_code=404, detail="site not found")
    items = repo.list_alerts(site_id, state=state, limit=limit)
    return {"items": items}


@router.get("/sites/{site_id}/alerts/count")
def count_alerts(
    site_id: str,
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "facility_manager", "energy_analyst", "viewer", "ops_admin", "ml_engineer")
    ),
) -> dict[str, Any]:
    repo = ControlRepository()
    if not repo.get_site(site_id):
        raise HTTPException(status_code=404, detail="site not found")
    counts = repo.count_open_alerts(site_id)
    return {
        "site_id": site_id,
        "open": counts["info"] + counts["warning"] + counts["critical"],
        "by_severity": counts,
    }


@router.get("/alerts/{alert_id}")
def get_alert(
    alert_id: str,
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "facility_manager", "energy_analyst", "viewer", "ops_admin", "ml_engineer")
    ),
) -> dict[str, Any]:
    repo = ControlRepository()
    alert = repo.get_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="alert not found")
    return alert


@router.patch("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(
    alert_id: str,
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "facility_manager", "ops_admin", "ml_engineer")
    ),
) -> dict[str, Any]:
    repo = ControlRepository()
    alert = repo.acknowledge_alert(alert_id, _principal.get("user_id", "unknown"))
    if not alert:
        raise HTTPException(status_code=404, detail="alert not found or already processed")
    return alert


@router.patch("/alerts/{alert_id}/resolve")
def resolve_alert(
    alert_id: str,
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "facility_manager", "ops_admin", "ml_engineer")
    ),
) -> dict[str, Any]:
    repo = ControlRepository()
    alert = repo.resolve_alert(alert_id, _principal.get("user_id", "unknown"))
    if not alert:
        raise HTTPException(status_code=404, detail="alert not found or already resolved")
    return alert
