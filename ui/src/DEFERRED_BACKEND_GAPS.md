# Deferred Backend Gaps (Frontend Wiring)

This file lists UI features and backend integrations that are currently pending or in-progress.

## UI Wiring (Backend Implemented)
- **Dashboard Aggregate API:** `GET /api/v1/sites/{site_id}/dashboard` is fully implemented in the backend but `SiteDetailPage.tsx` still uses individual calls for telemetry, optimization, and savings.
- **Granular Device Mapping UI:** `POST /api/v1/devices/{device_id}/mappings` exists in the backend and API client, but the granular field-mapping interface in `DevicesPage.tsx` is still under development.
- **Asset-Device Binding UI:** `POST /api/v1/assets/{asset_id}/devices` exists in the backend, but the direct binding drag-and-drop/selection UI is pending.

## Backend Production Gaps
- **MQTT Transport (Phase 7):** The edge-to-cloud publish/ack loop currently defaults to HTTP fallback; the MQTT transport layer is a production blocker.
- **Operational Hardening:** Field-ready supervisor logs, hardware watchdog integration, and automated recovery runbooks for edge devices.
- **Edge Token Management:** Production-grade strategy for edge gateway authentication token issuance and rotation.

## Resolved (Previously Deferred)
The following were previously listed as gaps but are now fully implemented and wired:
- Site Assets and Devices CRUD (`/api/v1/sites/{site_id}/assets`, `/api/v1/sites/{site_id}/devices`)
- Telemetry Latest and History APIs
- Optimization Run Details
- Command Stream and Acknowledgment
- Simulation Execution and Detail retrieval

## Notes
- Frontend uses real endpoints for all active features.
- Deferred advanced configuration boxes are explicitly marked in the UI to guide users to the API.
- No mocked responses are used in the primary production paths.
