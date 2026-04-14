# Authentication

## Endpoints
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/dev-token` (development mode only)

## Supported auth methods
- JWT bearer tokens (`Authorization: Bearer <token>`)
- Service API keys (`X-API-Key: <key>`), resolved from `EA_SERVICE_KEYS`

Service keys are intended for trusted service-to-service calls (for example compose edge runtime ingest).

## Edge runtime precedence
- Edge runtime auth selection is deterministic:
  - if `EDGE_API_KEY` is set, edge sends only `X-API-Key`
  - otherwise, if `EDGE_API_BEARER_TOKEN` is set, edge sends bearer auth
- This avoids ambiguous dual-auth behavior and keeps service auth explicit.

## Login contract
Request:
```json
{
  "email": "admin@ems.local",
  "password": "admin123!"
}
```

Response:
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

## JWT claims
Access tokens include:
- `sub` (user id)
- `email`
- `role`
- `roles`
- `organization_id`
- `iat`
- `exp`

## Local development seed
Migration `db/migrations/0005_auth_passwords.sql` seeds:
- User: `admin@ems.local`
- Password: `admin123!`
- Role: `client_admin`

## Notes
- UI stores the bearer token in local storage key `ems_access_token`.
- Invalid/expired tokens trigger a `401` and route users back to `/login`.
- `POST /api/v1/auth/logout` currently performs stateless client logout.
- Compose/local edge runtime uses `EDGE_API_KEY` -> `X-API-Key` by default for `/api/v1/telemetry/ingest`.
- API auth resolver logs auth type resolution and failures without logging secrets.
