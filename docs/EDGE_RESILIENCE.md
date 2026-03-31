# Edge Resilience & Failure Classification (Phase 2-6)

## Overview

This document describes the failure classification system implemented to improve edge ingest resilience and failure observability. It covers deterministic auth precedence, classified exception handling, intelligent retry strategies, and the v2 reporting extension point.

## Table of Contents

1. [Failure Classification System](#failure-classification-system)
2. [Auth Resilience Guarantees](#auth-resilience-guarantees)
3. [Replay & Observability Improvements](#replay--observability-improvements)
4. [Backoff Strategy by Failure Class](#backoff-strategy-by-failure-class)
5. [v2 Reporting Extension Point](#v2-reporting-extension-point)
6. [Testing & Validation](#testing--validation)

---

## Failure Classification System

### Exception Hierarchy

All ingest failures are classified into specific exception types in `src/energy_api/edge/failures.py`:

```python
EdgeIngestFailure (base)
├── AuthFailure (401/403)
├── TransientServerError (429/500/502/503/504 + optional Retry-After)
├── TransportFailure (timeout, DNS, connection refused, etc.)
│   └── NetworkUnavailable (specific transport failure: API unreachable)
└── ValidationFailure (400/422 malformed payload)
```

### Classification Logic

**In `cloud_client.py`:**
- `_classify_http_error(status_code)` → returns failure_class string
- `_make_classified_exception(status_code)` → creates typed exception instance
- All caught errors are logged with `failure_class` field for observability

**In `replay.py`:**
- Catches `EdgeIngestFailure` subclasses
- Extracts `failure_class` from exception
- Stores `failure_class` in SQLite `telemetry_buffer.failure_class` column
- Applies failure-specific backoff strategy

### Storage Schema

**SQLite `telemetry_buffer` table:**
```sql
CREATE TABLE telemetry_buffer (
  id INTEGER PRIMARY KEY,
  site_id TEXT,
  payload_json TEXT,
  created_at TEXT,
  attempt_count INTEGER DEFAULT 0,
  next_attempt_at TEXT,
  last_error TEXT,
  failure_class TEXT DEFAULT 'unclassified'  -- v2 addition
)
```

The `failure_class` column enables operational triage by error category.

---

## Auth Resilience Guarantees

### Deterministic Precedence

**Environment configuration in `cloud_client.py`:**
```
if EDGE_API_KEY:
  → X-API-Key header (primary)
elif EDGE_API_BEARER_TOKEN:
  → Authorization: Bearer header (fallback)
else:
  → no auth headers
```

**Once determined, auth_mode is enforced for the session lifetime.** No switching between auth types mid-session.

### Bearer Fallback Behavior

If `EDGE_API_KEY` is absent/empty, the client falls back to `EDGE_API_BEARER_TOKEN`:
- Validates JWT token on auth response (if 401 + bearer, token is invalid)
- If bearer also fails with 401 → both methods exhausted
- No attempt to send both headers simultaneously (prevents auth header conflicts)

### Auth Failure Handling

**401/403 responses:**
- Classified as `AuthFailure(failure_class="auth_failure")`
- **NOT retried immediately** in replay (backoff_seconds = 999999)
- Operators must investigate credential configuration
- No exponential backoff churn on auth misconfigurations

**Observability:**
- Logs `edge_ingest_failed auth_mode={mode} failure_class=auth_failure status=401`
- Error stored in `last_error` column (e.g., "Authentication failure: HTTP 401")
- `failure_class` recorded for triage

---

## Replay & Observability Improvements

### Failure Classification Result

**Before:**
```python
result = replay.replay_once()
# → {"attempted": 100, "sent": 95, "failed": 5, "remaining": 0}
# No distinction between failure causes
```

**After:**
```python
result = replay.replay_once()
# → {
#     "attempted": 100,
#     "sent": 95,
#     "failed": 5,
#     "remaining": 0,
#     "failed_by_class": {
#       "auth_failure": 2,        # Do not retry
#       "transport_failure": 2,   # Exponential backoff
#       "transient_server_error": 1  # Exponential backoff
#     }
# }
```

### Observability Logging

**Cloud Client Logs:**
```
INFO edge_ingest_request auth_mode=api_key site_id=site1 gateway_id=gw1 canonical_key=battery_soc
INFO edge_ingest_success auth_mode=api_key site_id=site1 gateway_id=gw1 received=1 inserted=1
WARNING edge_ingest_failed auth_mode=api_key site_id=site1 gateway_id=gw1 status=401 failure_class=auth_failure
```

**Replay Service Logs:**
- Records `failure_class` when marking telemetry for retry
- Can be queried to analyze failure trends by category

**Queue Visibility:**
```python
pending = replay.rebuild_queue_snapshot()
for record in pending:
  print(f"{record['id']}: {record['failure_class']} - {record['last_error'][:80]}")
```

---

## Backoff Strategy by Failure Class

### Default Backoff Formula

For **transient failures**, uses exponential backoff:
```
backoff_seconds(attempt) = min(60, 2 * 2^(attempt-1))
  attempt 1 → 2 seconds
  attempt 2 → 4 seconds
  attempt 3 → 8 seconds
  attempt 4 → 16 seconds
  attempt 5 → 32 seconds
  attempt 6+ → 60 seconds (capped)
```

### By Failure Class

| Failure Class | Backoff | Retry? | Notes |
|---------------|---------|--------|-------|
| `auth_failure` (401/403) | 999999s | ❌ Do not retry | Configuration issue; requires operator intervention |
| `validation_failure` (400/422) | 999999s | ❌ Do not retry | Permanent error; payload validation failed |
| `transient_server_error` (429/500/503) | Exponential | ✅ Yes | Transient; retry with backoff |
| `transport_failure` (timeout/DNS/refused) | Exponential | ✅ Yes | Network transient; retry with backoff |
| `unclassified_exception` | Exponential | ✅ Yes | Unknown; default to transient treatment |

**Implementation in `replay.py`:**
```python
@staticmethod
def _backoff_for_failure_class(failure_class: str, attempt: int) -> int:
  if failure_class in {"auth_failure", "validation_failure"}:
    return 999999  # Signal: do not retry
  
  # Transient failures: exponential backoff
  value = 2 * (2 ** max(0, attempt - 1))
  return min(60, value)
```

---

## v2 Reporting Extension Point

### Economic Class Metadata

Commands now include optional `economic_class` field for future v2 reporting:

```python
@dataclass
class ScoredAction:
  action_type: ActionType
  target_power_kw: float
  score: ScoreBreakdown
  explanation: dict
  reason: str
  economic_class: str = "modeled"  # v2 Extension Mechanism
```

### Classification Logic

**`ScoredAction.classify_economic_intent(action_type) → str`:**
- **"modeled"**: charge/discharge commands (primary cost drivers in v1 reporting)
- **"neutral"**: idle/set_mode/set_limit (baseline-neutral in v1; tracked for observability)
- **"unknown"**: unrecognized action types

### Future v2 Extension Points

Prepared for future enhancement with additional classes:
- **"constrained_control"**: Demand response / time-of-use constrained charging
- **"atomic"**: Atomic operations that cannot be subdivided
- **"grid_service"**: Future grid services (frequency support, etc.)

### v2 Reporting Implications

**v1 Semantics (Current):**
```python
# Savings calculation: charge/discharge control cost impact
savings_percent = (baseline_cost - optimized_cost) / baseline_cost
# Commands classified as "neutral" do not affect economic model
```

**v2 Future Capability:**
```python
# Extended reporting broken down by economic_class:
{
  "baseline_cost": 100.0,
  "optimized_cost": 80.0,
  "savings_percent": 20.0,
  "command_breakdown": {
    "modeled": {
      "charge": 8,      # 8 charge commands (primary shifters)
      "discharge": 5    # 5 discharge commands (primary shifters)
    },
    "constrained_control": {
      "charge": 2       # 2 DR constrained charge (may have separate reporting)
    }
  }
}
```

---

## Testing & Validation

### Unit Tests

**Failure classification tests** (`tests/edge/test_cloud_client_failure_paths.py`):
- ✅ 401 auth failures classified as `AuthFailure`
- ✅ Connection timeouts classified as `TransportFailure`
- ✅ 500 server errors classified as `TransientServerError`
- ✅ Bearer fallback triggers auth failure with no headers
- ✅ All failures logged with `failure_class` field

**Replay failure classification tests** (`tests/edge/test_replay_failure_classification.py`):
- ✅ Auth failures tracked with `failure_class="auth_failure"`
- ✅ Transport failures tracked with `failure_class="transport_failure"`
- ✅ Backoff differs: auth=999999s, transport=exponential
- ✅ Failed by class breakdown in replay result

**Regression tests:**
- ✅ 6 battery policy tests (control logic unaffected)
- ✅ 2 auth precedence tests (happy path validated)
- ✅ 2 savings taxonomy tests (v1 reporting unchanged)
- ✅ 8 economic class tests (v2 extension point validated)

### Runtime Validation

**Compose stack health check:**
- All services start successfully
- Edge runtime makes repeated successful ingests (HTTP 200 OK)
- 0 auth failures in healthy environment (correct credentials)
- Logs show `edge_ingest_success` entries with auth_mode=api_key

---

## Implementation Checklist

- ✅ Phase 1: Audit edge ingest auth resilience (gaps documented)
- ✅ Phase 2: Auth failure validation tests (401/403/timeout captured)
- ✅ Phase 3: Replay/observability tightening (failure_class tracking)
- ✅ Phase 4: Reporting v2 prep (economic_class metadata)
- ✅ Phase 5: Validation evidence (26 tests pass, compose stack healthy)
- ✅ Phase 6: Documentation (this file) + API docs updates

---

## Migration Notes

### For Operators

**Old behavior:**
- All ingest failures retried equally (no distinction)
- Misleading "success" after repeated 401s

**New behavior:**
- Auth failures do NOT retry (999999s backoff signals permanent)
- Transport failures retry with exponential backoff
- Check `failure_class` column in `telemetry_buffer` to triage

### For Developers

**If extending failure handling:**
1. Create new `EdgeIngestFailure` subclass in `failures.py`
2. Update `_classify_http_error()` and `_make_classified_exception()` in `cloud_client.py`
3. Update `_backoff_for_failure_class()` in `replay.py` with retry strategy
4. Add tests to `test_cloud_client_failure_paths.py` and `test_replay_failure_classification.py`

---

## References

- [Control Logic](CONTROL_LOGIC.md) — Command dispatch and battery policy
- [Auth & RBAC](AUTH.md) — Service key and JWT validation
- [Deployment](deployment.md) — Environment variable configuration
- [API](API.md) — Ingest endpoint specification

---

**Last Updated:** 2026-03-31  
**Status:** Complete (Phase 6)
