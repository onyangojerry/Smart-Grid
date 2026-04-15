# Author: Jerry Onyango
# Contribution: Boots the FastAPI application, registers domain routers, and serves health and contract endpoints.
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from energy_api.control import ControlRepository
from energy_api.security import require_roles, create_access_token

router = APIRouter(prefix="/api/v1", tags=["Edge"])


class EdgeGatewayAuthIn(BaseModel):
    gateway_id: str
    provisioning_secret: str


class EdgeGatewayAuthOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


@router.post("/gateways/authenticate")
def authenticate_gateway(payload: EdgeGatewayAuthIn) -> EdgeGatewayAuthOut:
    repo = ControlRepository()
    gateway = repo.authenticate_edge_gateway(payload.gateway_id, payload.provisioning_secret)
    if not gateway:
        raise HTTPException(status_code=401, detail="invalid_gateway_credentials")

    # Issue a token for the gateway. Gateways have 'ops_admin' or similar 
    # restricted roles suitable for telemetry ingest.
    token = create_access_token(
        subject=gateway["id"],
        roles=["ops_admin"], # Gateways act with ops_admin privileges for ingest
        facility_ids=[gateway["site_id"]],
        expires_in_minutes=60,
    )
    return EdgeGatewayAuthOut(
        access_token=token,
        expires_in=3600,
    )


class EdgeGatewayIn(BaseModel):
    name: str
    host: str
    port: int = 502


class EdgeGatewayOut(BaseModel):
    id: str
    site_id: str
    name: str
    host: str
    port: int
    status: Literal["online", "offline", "error"]
    provisioning_secret: str | None = None
    last_seen_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PointMappingIn(BaseModel):
    device_id: str
    source_key: str
    canonical_key: str
    value_type: Literal["uint16", "int16", "uint32", "int32", "float32"] = "float32"
    register_address: int
    register_count: int = 1
    scale_factor: float = 1.0
    signed: bool = False
    byte_order: Literal["big", "little"] = "big"
    word_order: Literal["big", "little"] = "big"
    unit: str | None = None


class PointMappingOut(BaseModel):
    id: str
    device_id: str
    source_key: str
    canonical_key: str
    value_type: str
    register_address: int
    register_count: int
    scale_factor: float
    signed: bool
    byte_order: str
    word_order: str
    unit: str | None
    created_at: str


@router.post("/sites/{site_id}/gateways", status_code=201)
def create_gateway(
    site_id: str,
    payload: EdgeGatewayIn,
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "ops_admin")
    ),
) -> EdgeGatewayOut:
    repo = ControlRepository()
    if not repo.get_site(site_id):
        raise HTTPException(status_code=404, detail="site not found")

    gateway_id = repo.create_edge_gateway(
        site_id=site_id,
        name=payload.name,
        host=payload.host,
        port=payload.port,
    )
    return EdgeGatewayOut(**gateway_id)


@router.get("/sites/{site_id}/gateways")
def list_gateways(
    site_id: str,
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "facility_manager", "energy_analyst", "viewer", "ops_admin", "ml_engineer")
    ),
) -> dict[str, Any]:
    repo = ControlRepository()
    return {"items": repo.list_edge_gateways(site_id)}


@router.get("/gateways/{gateway_id}")
def get_gateway(
    gateway_id: str,
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "facility_manager", "energy_analyst", "viewer", "ops_admin", "ml_engineer")
    ),
) -> EdgeGatewayOut:
    repo = ControlRepository()
    gateway = repo.get_edge_gateway(gateway_id)
    if not gateway:
        raise HTTPException(status_code=404, detail="gateway not found")
    return EdgeGatewayOut(**gateway)


@router.patch("/gateways/{gateway_id}/heartbeat")
def update_gateway_heartbeat(
    gateway_id: str,
    payload: dict[str, Any] | None = None,
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "ops_admin", "ml_engineer")
    ),
) -> EdgeGatewayOut:
    repo = ControlRepository()
    gateway = repo.update_edge_gateway_heartbeat(gateway_id, status_payload=payload)
    if not gateway:
        raise HTTPException(status_code=404, detail="gateway not found")
    return EdgeGatewayOut(**gateway)


@router.post("/devices/{device_id}/mappings", status_code=201)
def create_point_mapping(
    device_id: str,
    payload: PointMappingIn,
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "facility_manager", "ops_admin", "ml_engineer")
    ),
) -> PointMappingOut:
    repo = ControlRepository()
    mapping = repo.create_device_mapping(
        device_id=payload.device_id,
        source_key=payload.source_key,
        canonical_key=payload.canonical_key,
        scale_factor=payload.scale_factor,
        byte_order=payload.byte_order,
        word_order=payload.word_order,
        value_type=payload.value_type,
        signed=payload.signed,
        register_address=payload.register_address,
        register_count=payload.register_count,
        unit=payload.unit,
    )
    return PointMappingOut(**mapping)


@router.get("/devices/{device_id}/mappings")
def list_point_mappings(
    device_id: str,
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "facility_manager", "energy_analyst", "viewer", "ops_admin", "ml_engineer")
    ),
) -> dict[str, Any]:
    repo = ControlRepository()
    return {"items": repo.list_point_mappings(device_id)}


@router.delete("/mappings/{mapping_id}")
def delete_point_mapping(
    mapping_id: str,
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "ops_admin")
    ),
) -> dict[str, Any]:
    repo = ControlRepository()
    if not repo.delete_point_mapping(mapping_id):
        raise HTTPException(status_code=404, detail="mapping not found")
    return {"items": repo.list_point_mappings(device_id)}


@router.delete("/mappings/{mapping_id}")
def delete_point_mapping(
    mapping_id: str,
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "ops_admin")
    ),
) -> dict[str, Any]:
    repo = ControlRepository()
    if not repo.delete_point_mapping(mapping_id):
        raise HTTPException(status_code=404, detail="mapping not found")
    return {"status": "ok"}


@router.get("/sites/{site_id}/edge/health")
def get_edge_health(
    site_id: str,
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "facility_manager", "energy_analyst", "viewer", "ops_admin", "ml_engineer")
    ),
) -> dict[str, Any]:
    repo = ControlRepository()
    if not repo.get_site(site_id):
        raise HTTPException(status_code=404, detail="site not found")

    gateways = repo.list_edge_gateways(site_id)
    devices = repo.list_devices(site_id)

    total_mappings = 0
    for device in devices:
        mappings = repo.list_point_mappings(device["id"])
        total_mappings += len(mappings)

    return {
        "site_id": site_id,
        "gateways": {
            "total": len(gateways),
            "online": sum(1 for g in gateways if g.get("status") == "online"),
            "offline": sum(1 for g in gateways if g.get("status") == "offline"),
            "error": sum(1 for g in gateways if g.get("status") == "error"),
        },
        "devices": {
            "total": len(devices),
        },
        "point_mappings": {
            "total": total_mappings,
        },
        "status": "healthy" if any(g.get("status") == "online" for g in gateways) else "no_online_gateway",
    }


@router.get("/edge/logs")
async def stream_edge_logs(
    log_file_path: str = Query(default="./data/edge/edge.log"),
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "ops_admin")
    ),
):
    async def iter_logs():
        try:
            with open(log_file_path, "r") as f:
                # Seek to the end of the file initially
                f.seek(0, 2)
                while True:
                    line = f.readline()
                    if not line:
                        await asyncio.sleep(0.1) # Wait for new lines
                        continue
                    yield line.encode("utf-8") # Stream as bytes
        except FileNotFoundError:
            yield b"Log file not found.\n"
        except Exception as e:
            yield f"Error reading log file: {e}\n".encode("utf-8")
            
    return StreamingResponse(iter_logs(), media_type="text/plain")

    return {
        "site_id": site_id,
        "gateways": {
            "total": len(gateways),
            "online": sum(1 for g in gateways if g.get("status") == "online"),
            "offline": sum(1 for g in gateways if g.get("status") == "offline"),
            "error": sum(1 for g in gateways if g.get("status") == "error"),
        },
        "devices": {
            "total": len(devices),
        },
        "point_mappings": {
            "total": total_mappings,
        },
        "status": "healthy" if any(g.get("status") == "online" for g in gateways) else "no_online_gateway",
    }

@router.get("/edge/logs")
async def stream_edge_logs(
    log_file_path: str = Query(default="./data/edge/edge.log"),
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "ops_admin")
    ),
):
    async def iter_logs():
        try:
            with open(log_file_path, "r") as f:
                # Seek to the end of the file initially
                f.seek(0, 2)
                while True:
                    line = f.readline()
                    if not line:
                        await asyncio.sleep(0.1) # Wait for new lines
                        continue
                    yield line.encode("utf-8") # Stream as bytes
        except FileNotFoundError:
            yield b"Log file not found.\n"
        except Exception as e:
            yield f"Error reading log file: {e}\n".encode("utf-8")
            
    return StreamingResponse(iter_logs(), media_type="text/plain")


    return {
        "site_id": site_id,
        "gateways": {
            "total": len(gateways),
            "online": sum(1 for g in gateways if g.get("status") == "online"),
            "offline": sum(1 for g in gateways if g.get("status") == "offline"),
            "error": sum(1 for g in gateways if g.get("status") == "error"),
        },
        "devices": {
            "total": len(devices),
        },
        "point_mappings": {
            "total": total_mappings,
        },
        "status": "healthy" if any(g.get("status") == "online" for g in gateways) else "no_online_gateway",
    }
