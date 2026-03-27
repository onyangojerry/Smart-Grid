# Simulation Run Error: Unprocessable Entity (422) - Payload Binding Issue

## Problem Description

Users encountered an \"Unprocessable Entity\" error (HTTP 422) when attempting to run simulations. The backend logs showed the following error message:

```
Error: Unprocessable Entity

[
  {
    \"type\": \"missing\",
    \"loc\": [\"query\", \"payload\"],
    \"msg\": \"Field required\",
    \"input\": null
  }
]
```

The key part of this error is `\"loc\": [\"query\", \"payload\"]`, which indicates that FastAPI/Pydantic was unexpectedly looking for the `payload` parameter in the query string, rather than in the request body for a POST request. This caused validation to fail because `payload` was not found as a query parameter, and the `input: null` suggested the request body might not have been parsed correctly.

## Root Cause Analysis

The error suggested a misinterpretation of the `payload` parameter in the `run_site_simulation` backend endpoint. Despite being defined as a Pydantic model (`SimulationRunIn`) for the request body, FastAPI was trying to resolve it as a query parameter. 

Possible contributing factors:
* Frontend data serialization (`JSON.stringify`).
* Backend Pydantic model definition (`SimulationRunIn`).
* FastAPI's parameter resolution order.
* Implicit vs. Explicit binding of request body parameters.
* The most probable cause was that `payload` was not being correctly recognized or bound as a request body parameter by FastAPI.

## Solution Implemented

The issue was addressed by explicitly defining `payload` as a request body parameter in the backend and ensuring canonical parameter order.

### Backend Changes (`src/energy_api/routers/control_loop.py`)

1. **Explicit `Body` Binding**:
   * The `run_site_simulation` function signature was modified:
     ```python
     def run_site_simulation(
         site_id: str,
         payload: SimulationRunIn = Body(...),  # Explicitly marked as Body parameter
         _principal: dict[str, Any] = Depends(...),
     ) -> dict[str, Any]:
     ```
   * This ensures FastAPI binds the incoming JSON data to `payload` from the request body.
   * Added import `from fastapi import Body`.

2. **Parameter Reordering**:
   * Moved `payload` immediately after `site_id` path parameter and before dependencies.

3. **Robust `step_minutes` Handling**:
   * Updated to `step_minutes = payload.step_minutes if payload.step_minutes is not None else 5`.

### Frontend Refinements (`ui/src/features/simulation/SimulationPage.tsx`)

* Improved error messaging to \"Failed to run simulation. Please check input values.\"

## Outcome

The backend now correctly receives and parses simulation requests, resolving the error. The simulation feature is fully functional.

## Additional Notes from Investigation

The error `loc: [\"query\", \"payload\"]` indicated FastAPI confusion on parameter binding. Explicit `Body(...)` and reordering fixed it. Frontend sends correct JSON body via POST.
