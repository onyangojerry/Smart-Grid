<!-- /Users/loan/Desktop/energyallocation/docs/API.md -->
# API

## Auth
- `/api/v1/*` endpoints use JWT role checks via `require_roles`.
- `/api/v1/*` endpoints also accept service keys via `X-API-Key` (resolved from `EA_SERVICE_KEYS`).
- Edge runtime precedence: `EDGE_API_KEY` (`X-API-Key`) is primary; bearer is used only if API key is absent.
- Login endpoint: `POST /api/v1/auth/login`.
- Current user endpoint: `GET /api/v1/auth/me`.
- Logout endpoint: `POST /api/v1/auth/logout`.
- Dev token endpoint (`POST /api/v1/auth/dev-token`) is available only when development auth mode is enabled.

## Control loop endpoints

### POST /api/v1/telemetry/ingest
- Auth: `client_admin | facility_manager | ops_admin | ml_engineer`
- Accepted auth transport: JWT bearer or `X-API-Key` service key
- Telemetry units are resolved per canonical key; fields like SOC, temperature, voltage/current, and price do not default to `kW`.
- Request:
```json
{
  "site_id": "site_001",
  "gateway_id": "gw_edge_01",
  "points": [
    {"canonical_key": "pv_kw", "ts": "2026-03-25T10:00:00Z", "value": 14.2, "unit": "kW", "quality": "good"}
  ]
}
```
- Response:
```json
{"site_id":"site_001","gateway_id":"gw_edge_01","received":1,"inserted":1,"deduplicated":0}
```

### POST /api/v1/sites/{site_id}/optimize/run
- Auth: `client_admin | facility_manager | energy_analyst | ops_admin | ml_engineer`
- Request:
```json
{"mode":"live","horizon_minutes":60,"step_minutes":5,"allow_export":true,"reserve_soc_min":20,"forecast_peak":false}
```
- Response fields: `optimization_run_id`, `selected_action`, `dispatch`, `mqtt_publish`.

### POST /api/v1/sites/{site_id}/commands
- Auth: `client_admin | facility_manager | ops_admin | ml_engineer`
- Request:
```json
{"command_type":"charge","target_power_kw":2.0,"target_soc":75,"reason":"manual_override","idempotency_key":"cmd-001"}
```
- Manual commands are recorded as operator intent and do not reuse optimization scoring or state evaluation.
- Response fields: `status`, `command`, `transport`, `retries`.

### GET /api/v1/sites
- Auth: `client_admin | facility_manager | energy_analyst | viewer | ops_admin | ml_engineer`
- Response: `{"items": [...]}`.

### POST /api/v1/sites
- Auth: `client_admin | ops_admin | ml_engineer`
- Creates or updates a site and initializes defaults.

### GET /api/v1/sites/{site_id}/optimize/runs
- Auth: `client_admin | facility_manager | energy_analyst | viewer | ops_admin | ml_engineer`
- Returns recent optimization runs for a site.

### POST /api/v1/sites/{site_id}/simulation/run
- Auth: `client_admin | facility_manager | energy_analyst | ops_admin | ml_engineer`
- Runs in-memory simulation and returns cost/savings metrics.

### POST /api/v1/commands/{command_id}/ack
- Auth: `client_admin | facility_manager | ops_admin | ml_engineer`
- Request: empty
- Response: command row with `status=acked`.

### GET /api/v1/sites/{site_id}/savings/summary
- Auth: `client_admin | facility_manager | energy_analyst | viewer | ops_admin`
- Command taxonomy normalization in reporting supports legacy and modern command names (`charge`, `charge_setpoint_kw`, `discharge`, `discharge_setpoint_kw`, `idle`, `set_mode`, `set_limit`, `set_grid_limit_kw`, `set_export_limit_kw`).
- v1 economics model: charge/discharge are economically modeled; `idle`, `set_mode`, and grid/export limit commands are reported in taxonomy counts and treated as baseline-neutral.
- Response:
```json
{
  "snapshot_id": "sav_xxx",
  "site_id": "site_001",
  "baseline_cost": 12.34,
  "optimized_cost": 10.55,
  "savings_percent": 14.5,
  "battery_cycles": 0.8,
  "self_consumption_percent": 68.0,
  "peak_demand_reduction": 1.5
}
```

## Alerts endpoints

### POST /api/v1/sites/{site_id}/alerts
- Auth: `client_admin | facility_manager | ops_admin | ml_engineer`
- Request:
```json
{
  "alert_type": "high_temp",
  "severity": "warning",
  "title": "Battery Temperature High",
  "message": "Battery temperature exceeded threshold",
  "source_key": "battery_temp_c",
  "threshold_value": 45.0,
  "actual_value": 48.5
}
```
- Response: alert object with `id`, `state` (open|acknowledged|resolved)

### GET /api/v1/sites/{site_id}/alerts
- Auth: `client_admin | facility_manager | energy_analyst | viewer | ops_admin | ml_engineer`
- Query params: `state` (open|acknowledged|resolved), `limit` (default 100)
- Response: `{"items": [...]}`

### GET /api/v1/sites/{site_id}/alerts/count
- Auth: `client_admin | facility_manager | energy_analyst | viewer | ops_admin | ml_engineer`
- Response: severity breakdown of open alerts

### PATCH /api/v1/alerts/{alert_id}/acknowledge
- Auth: `client_admin | facility_manager | ops_admin | ml_engineer`
- Response: alert with `state=acknowledged`

### PATCH /api/v1/alerts/{alert_id}/resolve
- Auth: `client_admin | facility_manager | ops_admin | ml_engineer`
- Response: alert with `state=resolved`

## Edge management endpoints

### POST /api/v1/sites/{site_id}/gateways
- Auth: `client_admin | ops_admin`
- Creates an edge gateway for the site
- See [docs/EDGE_GATEWAY.md](EDGE_GATEWAY.md) for full gateway lifecycle endpoints

### GET /api/v1/sites/{site_id}/gateways
- Auth: `client_admin | facility_manager | energy_analyst | viewer | ops_admin | ml_engineer`
- Lists gateways for site

### POST /api/v1/devices/{device_id}/mappings
- Auth: `client_admin | facility_manager | ops_admin | ml_engineer`
- Creates a canonical point mapping from Modbus register to telemetry key
- See [docs/EDGE_GATEWAY.md](EDGE_GATEWAY.md) for mapping schema

### GET /api/v1/devices/{device_id}/mappings
- Auth: `client_admin | facility_manager | energy_analyst | viewer | ops_admin | ml_engineer`
- Lists point mappings for device

### GET /api/v1/sites/{site_id}/edge/health
- Auth: `client_admin | facility_manager | energy_analyst | viewer | ops_admin | ml_engineer`
- Returns edge runtime health summary: gateway count/status, device count, mapping count

## ROI Calculator endpoints

### POST /api/v1/sites/{site_id}/roi/calculate
- Auth: `client_admin | facility_manager | energy_analyst | ops_admin | ml_engineer`
- Request: financial system/usage/timeline params (see router implementation for full schema)
- Response: `{"annual_savings", "payback_years", "roi_percentage", "npv", "irr_percentage", "year_by_year"}`

### POST /api/v1/sites/{site_id}/roi/scenarios
- Auth: `client_admin | facility_manager | energy_analyst | ops_admin | ml_engineer`
- Creates and persists an ROI scenario for later analysis

### GET /api/v1/sites/{site_id}/roi/scenarios
- Auth: `client_admin | facility_manager | energy_analyst | viewer | ops_admin | ml_engineer`
- Lists saved ROI scenarios for site

### GET /api/v1/roi/scenarios/{scenario_id}
- Auth: `client_admin | facility_manager | energy_analyst | viewer | ops_admin | ml_engineer`
- Gets scenario details with live ROI calculation

### DELETE /api/v1/roi/scenarios/{scenario_id}
- Auth: `client_admin | facility_manager | ops_admin`
- Deletes a saved scenario

## Users and membership endpoints

### GET /api/v1/users
- Auth: `client_admin | admin | owner`
- Lists users in current organization

### GET /api/v1/users/{user_id}
- Auth: `client_admin | admin | owner | facility_manager`
- Gets user details and role

### PATCH /api/v1/users/{user_id}
- Auth: `client_admin | admin | owner`
- Updates user `full_name`, `role`, or `status`

### POST /api/v1/users/invite
- Auth: `client_admin | admin | owner`
- Invites a user by email; returns invitation token and expiration

### GET /api/v1/users/invitations
- Auth: `client_admin | admin | owner`
- Lists pending invitations

## Canonical namespace
- Canonical backend namespace is `/api/v1`.
- All six service routers (auth, control_loop, alerts, edge, roi, users) are mounted under this namespace.
- Legacy routes and old OpenAPI contract file were retired.
