# Remaining Features & Production Gaps

This document tracks the remaining features, optimizations, and operational requirements needed to reach full production readiness for the Smart Grid project.

## 1. Backend & Edge Runtime
- **MQTT Transport (Phase 7):** Implement the `EdgeMessagingClient` for MQTT. This is the preferred transport for field deployments to support bi-directional, low-latency communication and proper QoS levels for command acknowledgments.
- **Edge Token Strategy:** Design and implement a secure, automated system for issuing, rotating, and revoking bearer tokens for edge gateways.
- **Field-Ready Supervision:** Enhance the `EdgeRuntimeSupervisor` with hardware watchdog integration and more granular health reporting to the cloud.
- **Circuit Breaker for Writes:** Implement an additional safety layer in the `CommandExecutor` to prevent "chatter" or excessive writes to hardware registers in the event of an optimization logic failure.

## 2. Frontend & UI Integration
- **Dashboard API Consolidation:** Refactor `SiteDetailPage.tsx` to utilize the `/api/v1/sites/{site_id}/dashboard` aggregate endpoint. This will reduce initial page load latency and simplify state management.
- **Granular Device Mapping UI:** Build a specialized form or "mapper" component in `DevicesPage.tsx` that allows users to bind Modbus register addresses/counts to canonical telemetry keys without manually editing JSON.
- **Asset-Device Visual Binding:** Implement a UI for assigning devices to assets (e.g., binding a specific Inverter device to a "Solar Array" asset) to support more complex site topologies.
- **Real-time Log Stream:** Add a view in the UI (likely under "Edge Management") to stream live logs from a specific gateway for remote troubleshooting.

## 3. Operations & QA
- **Multi-Day Soak Testing:** Execute a 7-day continuous run in a simulated environment with fault injection (network drops, Modbus timeouts) to confirm 99.9% telemetry delivery.
- **Automated Field Runbooks:** Create scripts and documentation for "cold start" recovery and manual override procedures if an edge device loses cloud connectivity indefinitely.
- **Production Observability:** Integrate with a metrics provider (e.g., Prometheus/Grafana) to track global gateway health, latency, and command success rates across all sites.

## 4. Documentation
- **API Versioning Policy:** Define how breaking changes to the `/api/v1` contract will be handled for field-deployed edge devices that cannot be updated simultaneously.
- **Vendor-Specific Profile Library:** Expand the library of validated device profiles (SMA, Victron, etc.) with verified register maps and scaling factors.
