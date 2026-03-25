# Energy Allocation Platform Foundation

Minimal entry point for the repository. Detailed implementation, tooling, operations, and integration guidance lives in `docs/`.

## Service Offered
Energy Allocation is a multi-tenant energy optimization service for industrial and commercial facilities.
It ingests meter and connector data, builds facility-level usage features, and generates allocation recommendations that reduce cost, improve utilization, and support decarbonization targets.
The platform exposes these capabilities through a secured API and a frontend dashboard for onboarding, monitoring, alerts, recommendations, ROI analysis, and partner integrations.

## Documentation
- `docs/backend-structure.md`
- `docs/system-architecture.md`
- `docs/data-model-and-migrations.md`
- `docs/deployment.md`
- `docs/rbac-auth.md`
- `docs/alerting-system.md`
- `docs/pricing-and-roi.md`
- `docs/model-production-path.md`
- `docs/frontend-integration.md`
- `docs/partner-integration-api.md`
- `docs/partner-security-policy.md`
- `docs/partner-integration-implementation.md`
- `docs/batch-first-roadmap.md`
- `docs/gap-analysis-and-upgrade.md`

## Key Assets
- API contract: `openapi/openapi.v1.yaml`
- Migrations: `db/migrations/`
- Backend source: `src/energy_api/`
- ROI calculator source: `src/roi_calculator/`
- Frontend source: `ui/`

## Partner Onboarding
- Quick start: `PARTNER_QUICK_START.md`
- Integration summary: `PARTNER_INTEGRATION_SUMMARY.md`
