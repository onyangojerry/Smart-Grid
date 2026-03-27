export type UUID = string;

export type Site = {
  id: UUID;
  name: string;
  timezone: string;
  reserve_soc_min: number;
  polling_interval_seconds: number;
  created_at: string;
  updated_at: string;
};

export type SiteCreateBody = {
  site_id: string;
  name: string;
  timezone: string;
  reserve_soc_min: number;
  polling_interval_seconds: number;
};

export type AssetType = "battery" | "inverter" | "meter" | "pv_array" | "load" | "gateway";
export type Protocol = "modbus_tcp" | "mqtt" | "rest" | "simulated";
export type DeviceStatus = "active" | "inactive" | "fault";

export type Device = {
  id: UUID;
  site_id: UUID;
  device_type: string;
  protocol: string;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

export type DeviceCreateBody = {
  device_type: string;
  protocol: string;
  metadata?: Record<string, unknown>;
};

export type TelemetryPointIn = {
  canonical_key: string;
  ts: string;
  value: number;
  unit: string;
  quality: "good" | "estimated" | "bad";
};

export type TelemetryIngestBody = {
  site_id: UUID;
  gateway_id: UUID;
  points: TelemetryPointIn[];
};

export type TelemetryIngestResponse = {
  site_id: string;
  gateway_id: string;
  received: number;
  inserted: number;
  deduplicated: number;
};

export type CommandType = "charge" | "discharge" | "idle" | "set_limit" | "set_mode";
export type CommandStatus = "queued" | "sent" | "acknowledged" | "executed" | "failed" | "rejected";

export type Command = {
  id: UUID;
  site_id: UUID;
  device_id: UUID | null;
  command_type: CommandType;
  target_power_kw: number | null;
  target_soc: number | null;
  reason: string | null;
  status: "queued" | "sent" | "acked" | "failed";
  failure_reason: string | null;
  requested_at: string;
  sent_at: string | null;
  acked_at: string | null;
};

export type CommandCreateBody = {
  command_type: CommandType;
  target_power_kw?: number;
  target_soc?: number;
  reason: string;
};

export type ExplanationPayload = {
  decision: string;
  target_power_kw: number;
  top_factors: Array<{ factor: string; value: number; effect: string }>;
  summary: string;
};

export type OptimizationRun = {
  id?: UUID;
  optimization_run_id?: UUID;
  site_id: UUID;
  mode: "live" | "simulation" | "backtest";
  action_type?: CommandType;
  target_power_kw?: number;
  created_at?: string;
  explanation?: ExplanationPayload;
  selected_action?: {
    command_type: CommandType;
    target_power_kw: number;
    explanation: ExplanationPayload;
  };
};

export type OptimizationRunBody = {
  mode: "live" | "simulation" | "backtest";
  horizon_minutes: number;
  step_minutes: number;
  allow_export: boolean;
  reserve_soc_min: number;
};

export type SavingsSummary = {
  snapshot_id: string;
  site_id: string;
  window_start: string;
  window_end: string;
  baseline_cost: number;
  optimized_cost: number;
  savings_percent: number;
  battery_cycles: number;
  self_consumption_percent: number;
  peak_demand_reduction: number;
};

export type SimulationRunBody = {
  mode: "simulation" | "backtest";
  horizon_minutes?: number;
  step_minutes?: number;
  allow_export?: boolean;
  reserve_soc_min?: number;
};

export type SimulationRunDetail = {
  site_id: string;
  baseline_cost: number;
  optimized_cost: number;
  savings_percent: number;
  battery_cycles: number;
  self_consumption_percent: number;
  peak_demand_reduction: number;
  action_history: Array<{
    step: number;
    action: CommandType;
    target_power_kw: number;
    soc: number;
    price: number;
  }>;
};

export type User = {
  id: UUID;
  email: string;
  full_name: string;
  role: string;
  organization_id: UUID;
};

export type AlertSeverity = "info" | "warning" | "critical";
export type AlertState = "open" | "acknowledged" | "resolved";

export type Alert = {
  id: UUID;
  site_id: UUID;
  alert_type: string;
  severity: AlertSeverity;
  state: AlertState;
  title: string;
  message: string;
  source_key: string | null;
  threshold_value: number | null;
  actual_value: number | null;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
  resolved_by: string | null;
  resolved_at: string | null;
  created_at: string;
  updated_at: string;
};

export type AlertCreateBody = {
  alert_type: string;
  severity: AlertSeverity;
  title: string;
  message: string;
  source_key?: string;
  threshold_value?: number;
  actual_value?: number;
};

export type AlertCount = {
  site_id: string;
  open: number;
  by_severity: {
    info: number;
    warning: number;
    critical: number;
  };
};

export type ROIInputSystem = {
  battery_capacity_kwh: number;
  battery_power_kw: number;
  solar_capacity_kwp: number;
  round_trip_efficiency: number;
};

export type ROIInputFinancial = {
  installation_cost: number;
  annual_maintenance_cost: number;
  electricity_import_price: number;
  electricity_export_price: number;
  annual_energy_import_kwh: number;
  annual_energy_export_kwh: number;
  annual_peak_demand_kw: number;
  demand_charge_per_kw_month: number;
};

export type ROIInputUsage = {
  self_consumption_ratio: number;
  battery_cycles_per_year: number;
  degradation_rate_year1: number;
  degradation_rate_after: number;
};

export type ROIInputTimeline = {
  project_lifespan_years: number;
  discount_rate: number;
  inflation_rate: number;
};

export type ROIInput = {
  name: string;
  description?: string;
  system: ROIInputSystem;
  financial: ROIInputFinancial;
  usage: ROIInputUsage;
  timeline: ROIInputTimeline;
};

export type ROIResult = {
  annual_savings: number;
  payback_years: number;
  roi_percentage: number;
  npv: number;
  irr_percentage: number;
  year_by_year: Array<{
    year: number;
    annual_savings: number;
    cumulative_savings: number;
    npv: number;
    degradation_factor: number;
    inflation_factor: number;
    break_even: boolean;
  }>;
};

export type ROIScenario = {
  id: string;
  site_id: string;
  name: string;
  description: string | null;
  battery_capacity_kwh: number;
  battery_power_kw: number;
  solar_capacity_kwp: number;
  installation_cost: number;
  annual_savings: number | null;
  payback_years: number | null;
  roi_percentage: number | null;
  npv: number | null;
  irr_percentage: number | null;
  created_at: string;
  updated_at: string;
};
