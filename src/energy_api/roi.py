# Author: Jerry Onyango
# Contribution: Boots the FastAPI application, registers domain routers, and serves health and contract endpoints.
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import psycopg
from psycopg.rows import dict_row


def _db_url() -> str:
    return os.getenv(
        "EA_DATABASE_URL",
        "postgresql://energyallocation:energyallocation@localhost:5432/energyallocation",
    )


@dataclass
class ROICalculationInput:
    battery_capacity_kwh: float
    battery_power_kw: float
    solar_capacity_kwp: float
    round_trip_efficiency: float
    installation_cost: float
    annual_maintenance_cost: float
    electricity_import_price: float
    electricity_export_price: float
    annual_energy_import_kwh: float
    annual_energy_export_kwh: float
    annual_peak_demand_kw: float
    demand_charge_per_kw_month: float
    self_consumption_ratio: float
    battery_cycles_per_year: float
    degradation_rate_year1: float
    degradation_rate_after: float
    project_lifespan_years: int
    discount_rate: float
    inflation_rate: float


@dataclass
class ROICalculationResult:
    annual_savings: float
    payback_years: float
    roi_percentage: float
    npv: float
    irr_percentage: float
    year_by_year: list[dict[str, Any]]


class ROIService:
    def __init__(self, db_url: str | None = None) -> None:
        self._db_url = db_url or _db_url()
        self._ensure_schema()

    def _connect(self):
        return psycopg.connect(self._db_url, row_factory=dict_row, autocommit=True)

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS roi_scenarios (
                        id TEXT PRIMARY KEY,
                        site_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        description TEXT,
                        battery_capacity_kwh NUMERIC(10,2) NOT NULL DEFAULT 100,
                        battery_power_kw NUMERIC(10,2) NOT NULL DEFAULT 50,
                        solar_capacity_kwp NUMERIC(10,2) NOT NULL DEFAULT 0,
                        round_trip_efficiency NUMERIC(5,4) NOT NULL DEFAULT 0.90,
                        installation_cost NUMERIC(12,2) NOT NULL DEFAULT 0,
                        annual_maintenance_cost NUMERIC(10,2) NOT NULL DEFAULT 0,
                        electricity_import_price NUMERIC(8,4) NOT NULL DEFAULT 0.20,
                        electricity_export_price NUMERIC(8,4) NOT NULL DEFAULT 0.05,
                        annual_energy_import_kwh NUMERIC(12,2) NOT NULL DEFAULT 0,
                        annual_energy_export_kwh NUMERIC(12,2) NOT NULL DEFAULT 0,
                        annual_peak_demand_kw NUMERIC(10,2) NOT NULL DEFAULT 0,
                        demand_charge_per_kw_month NUMERIC(8,2) NOT NULL DEFAULT 0,
                        self_consumption_ratio NUMERIC(5,4) NOT NULL DEFAULT 0.70,
                        battery_cycles_per_year NUMERIC(8,2) NOT NULL DEFAULT 365,
                        degradation_rate_year1 NUMERIC(5,4) NOT NULL DEFAULT 0.02,
                        degradation_rate_after NUMERIC(5,4) NOT NULL DEFAULT 0.005,
                        project_lifespan_years INT NOT NULL DEFAULT 20,
                        discount_rate NUMERIC(5,4) NOT NULL DEFAULT 0.08,
                        inflation_rate NUMERIC(5,4) NOT NULL DEFAULT 0.02,
                        annual_savings NUMERIC(12,2),
                        payback_years NUMERIC(6,2),
                        roi_percentage NUMERIC(8,2),
                        npv NUMERIC(14,2),
                        irr_percentage NUMERIC(8,2),
                        created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                    )
                    """
                )

    @staticmethod
    def calculate(input_params: ROICalculationInput) -> ROICalculationResult:
        horizon = input_params.project_lifespan_years
        discount = input_params.discount_rate
        inflation = input_params.inflation_rate
        efficiency = input_params.round_trip_efficiency

        annual_energy_savings_kwh = (
            input_params.annual_energy_import_kwh *
            input_params.self_consumption_ratio *
            (1 - (1 / (1 + input_params.solar_capacity_kwp / max(input_params.annual_energy_import_kwh / 8760, 1))))
        )

        baseline_energy_cost = (
            input_params.annual_energy_import_kwh * input_params.electricity_import_price +
            input_params.annual_peak_demand_kw * input_params.demand_charge_per_kw_month * 12
        )
        
        optimized_energy_cost = (
            (input_params.annual_energy_import_kwh - annual_energy_savings_kwh) * input_params.electricity_import_price +
            max(0, input_params.annual_peak_demand_kw * 0.9) * input_params.demand_charge_per_kw_month * 12
        )

        export_revenue = (
            annual_energy_savings_kwh * input_params.self_consumption_ratio * input_params.electricity_export_price
        )

        year_by_year = []
        cumulative_savings = 0.0
        npv_sum = 0.0
        total_nominal_savings = 0.0

        for year in range(1, horizon + 1):
            if year == 1:
                degradation = input_params.degradation_rate_year1
            else:
                degradation = input_params.degradation_rate_after

            year_factor = (1 - degradation) ** (year - 1)
            inflation_factor = (1 + inflation) ** (year - 1)

            energy_savings = annual_energy_savings_kwh * year_factor * inflation_factor
            demand_savings = input_params.annual_peak_demand_kw * input_params.demand_charge_per_kw_month * 12 * 0.1 * inflation_factor
            export_rev = export_revenue * year_factor * inflation_factor
            maintenance = input_params.annual_maintenance_cost * inflation_factor

            net_annual_savings = energy_savings + demand_savings + export_rev - maintenance

            pv_factor = 1 / ((1 + discount) ** year)
            npv_contribution = net_annual_savings * pv_factor

            cumulative_savings += net_annual_savings
            npv_sum += npv_contribution
            total_nominal_savings += net_annual_savings

            year_by_year.append({
                "year": year,
                "annual_savings": round(net_annual_savings, 2),
                "cumulative_savings": round(cumulative_savings, 2),
                "npv": round(npv_sum, 2),
                "degradation_factor": round(year_factor, 4),
                "inflation_factor": round(inflation_factor, 4),
                "break_even": cumulative_savings >= input_params.installation_cost
            })

        payback = 0.0
        for y in year_by_year:
            if y["cumulative_savings"] >= input_params.installation_cost:
                prev_savings = y["cumulative_savings"] - y["annual_savings"]
                fraction = (input_params.installation_cost - prev_savings) / y["annual_savings"]
                payback = y["year"] - 1 + fraction
                break
        
        if payback == 0 and year_by_year:
            payback = year_by_year[-1]["year"] + 1

        total_investment = input_params.installation_cost
        roi = ((total_nominal_savings - total_investment) / total_investment) * 100 if total_investment > 0 else 0

        npv = npv_sum - input_params.installation_cost

        irr = ROIService._calculate_irr(
            -input_params.installation_cost,
            [y["annual_savings"] for y in year_by_year]
        )

        return ROICalculationResult(
            annual_savings=round(year_by_year[0]["annual_savings"] if year_by_year else 0, 2),
            payback_years=round(payback, 2),
            roi_percentage=round(roi, 2),
            npv=round(npv, 2),
            irr_percentage=round(irr, 2) if irr else 0,
            year_by_year=year_by_year
        )

    @staticmethod
    def _calculate_irr(initial_investment: float, cash_flows: list[float]) -> float:
        if not cash_flows:
            return 0.0
        
        rate = 0.1
        for _ in range(1000):
            npv = -initial_investment
            for i, cf in enumerate(cash_flows, 1):
                npv += cf / ((1 + rate) ** i)
            
            d_npv = 0
            for i, cf in enumerate(cash_flows, 1):
                d_npv -= (i * cf) / ((1 + rate) ** (i + 1))
            
            if abs(d_npv) < 1e-10:
                break
            
            rate -= npv / d_npv
            
            if rate < -0.99:
                rate = -0.99
            elif rate > 10:
                rate = 10
        
        return rate * 100

    def create_scenario(self, site_id: str, params: dict[str, Any]) -> dict[str, Any]:
        scenario_id = f"roi_{os.urandom(4).hex()}"
        
        input_params = ROICalculationInput(
            battery_capacity_kwh=float(params.get("battery_capacity_kwh", 100)),
            battery_power_kw=float(params.get("battery_power_kw", 50)),
            solar_capacity_kwp=float(params.get("solar_capacity_kwp", 0)),
            round_trip_efficiency=float(params.get("round_trip_efficiency", 0.90)),
            installation_cost=float(params.get("installation_cost", 0)),
            annual_maintenance_cost=float(params.get("annual_maintenance_cost", 0)),
            electricity_import_price=float(params.get("electricity_import_price", 0.20)),
            electricity_export_price=float(params.get("electricity_export_price", 0.05)),
            annual_energy_import_kwh=float(params.get("annual_energy_import_kwh", 0)),
            annual_energy_export_kwh=float(params.get("annual_energy_export_kwh", 0)),
            annual_peak_demand_kw=float(params.get("annual_peak_demand_kw", 0)),
            demand_charge_per_kw_month=float(params.get("demand_charge_per_kw_month", 0)),
            self_consumption_ratio=float(params.get("self_consumption_ratio", 0.70)),
            battery_cycles_per_year=float(params.get("battery_cycles_per_year", 365)),
            degradation_rate_year1=float(params.get("degradation_rate_year1", 0.02)),
            degradation_rate_after=float(params.get("degradation_rate_after", 0.005)),
            project_lifespan_years=int(params.get("project_lifespan_years", 20)),
            discount_rate=float(params.get("discount_rate", 0.08)),
            inflation_rate=float(params.get("inflation_rate", 0.02)),
        )
        
        result = self.calculate(input_params)
        
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO roi_scenarios(
                        id, site_id, name, description, battery_capacity_kwh, battery_power_kw,
                        solar_capacity_kwp, round_trip_efficiency, installation_cost,
                        annual_maintenance_cost, electricity_import_price, electricity_export_price,
                        annual_energy_import_kwh, annual_energy_export_kwh, annual_peak_demand_kw,
                        demand_charge_per_kw_month, self_consumption_ratio, battery_cycles_per_year,
                        degradation_rate_year1, degradation_rate_after, project_lifespan_years,
                        discount_rate, inflation_rate, annual_savings, payback_years, roi_percentage, npv, irr_percentage
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING *
                    """,
                    (
                        scenario_id, site_id, params.get("name", "Untitled"),
                        params.get("description"), params.get("battery_capacity_kwh", 100),
                        params.get("battery_power_kw", 50), params.get("solar_capacity_kwp", 0),
                        params.get("round_trip_efficiency", 0.90), params.get("installation_cost", 0),
                        params.get("annual_maintenance_cost", 0), params.get("electricity_import_price", 0.20),
                        params.get("electricity_export_price", 0.05), params.get("annual_energy_import_kwh", 0),
                        params.get("annual_energy_export_kwh", 0), params.get("annual_peak_demand_kw", 0),
                        params.get("demand_charge_per_kw_month", 0), params.get("self_consumption_ratio", 0.70),
                        params.get("battery_cycles_per_year", 365), params.get("degradation_rate_year1", 0.02),
                        params.get("degradation_rate_after", 0.005), params.get("project_lifespan_years", 20),
                        params.get("discount_rate", 0.08), params.get("inflation_rate", 0.02),
                        result.annual_savings, result.payback_years, result.roi_percentage, result.npv, result.irr_percentage
                    ),
                )
                row = cur.fetchone()
        
        return {
            "scenario": row,
            "calculation": {
                "annual_savings": result.annual_savings,
                "payback_years": result.payback_years,
                "roi_percentage": result.roi_percentage,
                "npv": result.npv,
                "irr_percentage": result.irr_percentage,
                "year_by_year": result.year_by_year
            }
        }

    def list_scenarios(self, site_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM roi_scenarios WHERE site_id = %s ORDER BY created_at DESC",
                    (site_id,),
                )
                return cur.fetchall()

    def get_scenario(self, scenario_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM roi_scenarios WHERE id = %s", (scenario_id,))
                return cur.fetchone()

    def delete_scenario(self, scenario_id: str) -> bool:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM roi_scenarios WHERE id = %s RETURNING id", (scenario_id,))
                return cur.fetchone() is not None

    def recalculate_scenario(self, scenario_id: str) -> dict[str, Any]:
        scenario = self.get_scenario(scenario_id)
        if not scenario:
            raise ValueError("Scenario not found")
        
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
        
        result = self.calculate(input_params)
        
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE roi_scenarios SET 
                        annual_savings = %s, payback_years = %s, roi_percentage = %s,
                        npv = %s, irr_percentage = %s, updated_at = now()
                    WHERE id = %s
                    RETURNING *
                    """,
                    (result.annual_savings, result.payback_years, result.roi_percentage, result.npv, result.irr_percentage, scenario_id),
                )
                updated = cur.fetchone()
        
        return {
            "scenario": updated,
            "calculation": {
                "annual_savings": result.annual_savings,
                "payback_years": result.payback_years,
                "roi_percentage": result.roi_percentage,
                "npv": result.npv,
                "irr_percentage": result.irr_percentage,
                "year_by_year": result.year_by_year
            }
        }
