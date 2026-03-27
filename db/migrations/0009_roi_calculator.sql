-- ROI Calculator schema for financial projections and scenario comparison
CREATE TABLE IF NOT EXISTS roi_scenarios (
    id TEXT PRIMARY KEY,
    site_id TEXT NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    
    -- System Configuration
    battery_capacity_kwh NUMERIC(10,2) NOT NULL DEFAULT 100,
    battery_power_kw NUMERIC(10,2) NOT NULL DEFAULT 50,
    solar_capacity_kwp NUMERIC(10,2) NOT NULL DEFAULT 0,
    round_trip_efficiency NUMERIC(5,4) NOT NULL DEFAULT 0.90,
    
    -- Financial Parameters
    installation_cost NUMERIC(12,2) NOT NULL DEFAULT 0,
    annual_maintenance_cost NUMERIC(10,2) NOT NULL DEFAULT 0,
    electricity_import_price NUMERIC(8,4) NOT NULL DEFAULT 0.20,
    electricity_export_price NUMERIC(8,4) NOT NULL DEFAULT 0.05,
    annual_energy_import_kwh NUMERIC(12,2) NOT NULL DEFAULT 0,
    annual_energy_export_kwh NUMERIC(12,2) NOT NULL DEFAULT 0,
    annual_peak_demand_kw NUMERIC(10,2) NOT NULL DEFAULT 0,
    demand_charge_per_kw_month NUMERIC(8,2) NOT NULL DEFAULT 0,
    
    -- Usage Pattern
    self_consumption_ratio NUMERIC(5,4) NOT NULL DEFAULT 0.70,
    battery_cycles_per_year NUMERIC(8,2) NOT NULL DEFAULT 365,
    degradation_rate_year1 NUMERIC(5,4) NOT NULL DEFAULT 0.02,
    degradation_rate_after NUMERIC(5,4) NOT NULL DEFAULT 0.005,
    
    -- Project Timeline
    project_lifespan_years INT NOT NULL DEFAULT 20,
    discount_rate NUMERIC(5,4) NOT NULL DEFAULT 0.08,
    inflation_rate NUMERIC(5,4) NOT NULL DEFAULT 0.02,
    
    -- Calculated Results (cached)
    annual_savings NUMERIC(12,2),
    payback_years NUMERIC(6,2),
    roi_percentage NUMERIC(8,2),
    npv NUMERIC(14,2),
    irr_percentage NUMERIC(8,2),
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_roi_scenarios_site ON roi_scenarios(site_id);
