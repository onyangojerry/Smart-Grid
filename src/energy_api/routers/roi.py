# Author: Jerry Onyango
# Contribution: Boots the FastAPI application, registers domain routers, and serves health and contract endpoints.
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from energy_api.control import ControlRepository
from energy_api.roi import ROICalculationInput, ROIService
from energy_api.security import require_roles

router = APIRouter(prefix="/api/v1", tags=["ROI Calculator"])


class ROIInputSystem(BaseModel):
    battery_capacity_kwh: float = Field(default=100, ge=0)
    battery_power_kw: float = Field(default=50, ge=0)
    solar_capacity_kwp: float = Field(default=0, ge=0)
    round_trip_efficiency: float = Field(default=0.90, ge=0.5, le=1.0)


class ROIInputFinancial(BaseModel):
    installation_cost: float = Field(default=0, ge=0)
    annual_maintenance_cost: float = Field(default=0, ge=0)
    electricity_import_price: float = Field(default=0.20, ge=0)
    electricity_export_price: float = Field(default=0.05, ge=0)
    annual_energy_import_kwh: float = Field(default=0, ge=0)
    annual_energy_export_kwh: float = Field(default=0, ge=0)
    annual_peak_demand_kw: float = Field(default=0, ge=0)
    demand_charge_per_kw_month: float = Field(default=0, ge=0)


class ROIInputUsage(BaseModel):
    self_consumption_ratio: float = Field(default=0.70, ge=0, le=1.0)
    battery_cycles_per_year: float = Field(default=365, ge=0)
    degradation_rate_year1: float = Field(default=0.02, ge=0, le=1.0)
    degradation_rate_after: float = Field(default=0.005, ge=0, le=1.0)


class ROIInputTimeline(BaseModel):
    project_lifespan_years: int = Field(default=20, ge=1, le=50)
    discount_rate: float = Field(default=0.08, ge=0, le=1.0)
    inflation_rate: float = Field(default=0.02, ge=0, le=1.0)


class ROIInput(BaseModel):
    name: str = Field(default="Untitled Scenario")
    description: str | None = None
    system: ROIInputSystem = Field(default_factory=ROIInputSystem)
    financial: ROIInputFinancial = Field(default_factory=ROIInputFinancial)
    usage: ROIInputUsage = Field(default_factory=ROIInputUsage)
    timeline: ROIInputTimeline = Field(default_factory=ROIInputTimeline)


class ROIResult(BaseModel):
    annual_savings: float
    payback_years: float
    roi_percentage: float
    npv: float
    irr_percentage: float
    year_by_year: list[dict[str, Any]]


class ROIScenarioResponse(BaseModel):
    id: str
    site_id: str
    name: str
    description: str | None
    battery_capacity_kwh: float
    battery_power_kw: float
    solar_capacity_kwp: float
    installation_cost: float
    annual_savings: float | None
    payback_years: float | None
    roi_percentage: float | None
    npv: float | None
    irr_percentage: float | None
    created_at: str
    updated_at: str


@router.post("/sites/{site_id}/roi/calculate")
def calculate_roi(
    site_id: str,
    payload: ROIInput,
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "facility_manager", "energy_analyst", "ops_admin", "ml_engineer")
    ),
) -> ROIResult:
    repo = ControlRepository()
    if not repo.get_site(site_id):
        raise HTTPException(status_code=404, detail="site not found")

    input_params = ROICalculationInput(
        battery_capacity_kwh=payload.system.battery_capacity_kwh,
        battery_power_kw=payload.system.battery_power_kw,
        solar_capacity_kwp=payload.system.solar_capacity_kwp,
        round_trip_efficiency=payload.system.round_trip_efficiency,
        installation_cost=payload.financial.installation_cost,
        annual_maintenance_cost=payload.financial.annual_maintenance_cost,
        electricity_import_price=payload.financial.electricity_import_price,
        electricity_export_price=payload.financial.electricity_export_price,
        annual_energy_import_kwh=payload.financial.annual_energy_import_kwh,
        annual_energy_export_kwh=payload.financial.annual_energy_export_kwh,
        annual_peak_demand_kw=payload.financial.annual_peak_demand_kw,
        demand_charge_per_kw_month=payload.financial.demand_charge_per_kw_month,
        self_consumption_ratio=payload.usage.self_consumption_ratio,
        battery_cycles_per_year=payload.usage.battery_cycles_per_year,
        degradation_rate_year1=payload.usage.degradation_rate_year1,
        degradation_rate_after=payload.usage.degradation_rate_after,
        project_lifespan_years=payload.timeline.project_lifespan_years,
        discount_rate=payload.timeline.discount_rate,
        inflation_rate=payload.timeline.inflation_rate,
    )

    result = ROIService.calculate(input_params)
    return ROIResult(
        annual_savings=result.annual_savings,
        payback_years=result.payback_years,
        roi_percentage=result.roi_percentage,
        npv=result.npv,
        irr_percentage=result.irr_percentage,
        year_by_year=result.year_by_year,
    )


@router.post("/sites/{site_id}/roi/scenarios", status_code=201)
def create_roi_scenario(
    site_id: str,
    payload: ROIInput,
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "facility_manager", "energy_analyst", "ops_admin", "ml_engineer")
    ),
) -> dict[str, Any]:
    repo = ControlRepository()
    if not repo.get_site(site_id):
        raise HTTPException(status_code=404, detail="site not found")

    service = ROIService()
    params = {
        "name": payload.name,
        "description": payload.description,
        "battery_capacity_kwh": payload.system.battery_capacity_kwh,
        "battery_power_kw": payload.system.battery_power_kw,
        "solar_capacity_kwp": payload.system.solar_capacity_kwp,
        "round_trip_efficiency": payload.system.round_trip_efficiency,
        "installation_cost": payload.financial.installation_cost,
        "annual_maintenance_cost": payload.financial.annual_maintenance_cost,
        "electricity_import_price": payload.financial.electricity_import_price,
        "electricity_export_price": payload.financial.electricity_export_price,
        "annual_energy_import_kwh": payload.financial.annual_energy_import_kwh,
        "annual_energy_export_kwh": payload.financial.annual_energy_export_kwh,
        "annual_peak_demand_kw": payload.financial.annual_peak_demand_kw,
        "demand_charge_per_kw_month": payload.financial.demand_charge_per_kw_month,
        "self_consumption_ratio": payload.usage.self_consumption_ratio,
        "battery_cycles_per_year": payload.usage.battery_cycles_per_year,
        "degradation_rate_year1": payload.usage.degradation_rate_year1,
        "degradation_rate_after": payload.usage.degradation_rate_after,
        "project_lifespan_years": payload.timeline.project_lifespan_years,
        "discount_rate": payload.timeline.discount_rate,
        "inflation_rate": payload.timeline.inflation_rate,
    }

    return service.create_scenario(site_id, params)


@router.get("/sites/{site_id}/roi/scenarios")
def list_roi_scenarios(
    site_id: str,
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "facility_manager", "energy_analyst", "viewer", "ops_admin", "ml_engineer")
    ),
) -> dict[str, Any]:
    repo = ControlRepository()
    if not repo.get_site(site_id):
        raise HTTPException(status_code=404, detail="site not found")

    service = ROIService()
    items = service.list_scenarios(site_id)
    return {"items": items}


@router.get("/roi/scenarios/{scenario_id}")
def get_roi_scenario(
    scenario_id: str,
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "facility_manager", "energy_analyst", "viewer", "ops_admin", "ml_engineer")
    ),
) -> dict[str, Any]:
    service = ROIService()
    scenario = service.get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="scenario not found")

    input_params = ROICalculationInput(
        battery_capacity_kwh=float(scenario["battery_capacity_kwh"]),
        battery_power_kw=float(scenario["battery_power_kw"]),
        solar_capacity_kwp=float(scenario["solar_capacity_kwp"]),
        round_trip_efficiency=float(scenario["round_trip_efficiency"]),
        installation_cost=float(scenario["installation_cost"]),
        annual_maintenance_cost=float(scenario["annual_maintenance_cost"]),
        electricity_import_price=float(scenario["electricity_import_price"]),
        electricity_export_price=float(scenario["electricity_export_price"]),
        annual_energy_import_kwh=float(scenario["annual_energy_import_kwh"]),
        annual_energy_export_kwh=float(scenario["annual_energy_export_kwh"]),
        annual_peak_demand_kw=float(scenario["annual_peak_demand_kw"]),
        demand_charge_per_kw_month=float(scenario["demand_charge_per_kw_month"]),
        self_consumption_ratio=float(scenario["self_consumption_ratio"]),
        battery_cycles_per_year=float(scenario["battery_cycles_per_year"]),
        degradation_rate_year1=float(scenario["degradation_rate_year1"]),
        degradation_rate_after=float(scenario["degradation_rate_after"]),
        project_lifespan_years=int(scenario["project_lifespan_years"]),
        discount_rate=float(scenario["discount_rate"]),
        inflation_rate=float(scenario["inflation_rate"]),
    )
    result = ROIService.calculate(input_params)

    return {
        "scenario": scenario,
        "calculation": {
            "annual_savings": result.annual_savings,
            "payback_years": result.payback_years,
            "roi_percentage": result.roi_percentage,
            "npv": result.npv,
            "irr_percentage": result.irr_percentage,
            "year_by_year": result.year_by_year,
        },
    }


@router.delete("/roi/scenarios/{scenario_id}")
def delete_roi_scenario(
    scenario_id: str,
    _principal: dict[str, Any] = Depends(
        require_roles("client_admin", "facility_manager", "ops_admin")
    ),
) -> dict[str, Any]:
    service = ROIService()
    if not service.delete_scenario(scenario_id):
        raise HTTPException(status_code=404, detail="scenario not found")
    return {"status": "ok"}
