# Render Deployment Guide

## Scope

This guide prepares a public AI BAP demonstration with Render managed
PostgreSQL, a Docker FastAPI service, and a Vite static site. It does not
authorize deployment by itself.

## Blueprint

[`render.yaml`](../render.yaml) defines the managed PostgreSQL instance, the
Docker API service, and the static frontend. Automatic deployment is disabled
so a Human Product Owner must explicitly initiate each deployment.

The API uses Render's private database connection string through `DATABASE_URL`.
The database has an empty public IP allowlist, so it is not exposed publicly.

## Required Configuration

Render generates `JWT_SECRET_KEY`. Supply `CORS_ORIGINS` in the Render
Dashboard after the frontend URL is known, using a JSON list with the exact
HTTPS frontend origin. Do not add wildcard origins.

The static-site build receives `VITE_API_BASE_URL` from the API service's public
Render URL. It is a public build-time value, not a secret.

Optional AI drafting requires `OPENAI_API_KEY` and, if needed, `OPENAI_MODEL`.
Leave those variables unset when the feature is not part of the demo.

## Migrations

The API pre-deploy command runs `migrate_production.py`. It requires a valid
managed PostgreSQL connection, obtains a PostgreSQL advisory lock, and runs
`alembic upgrade head`. A failure blocks the new API deploy.

The local Compose-only `initialize_fresh_database.py` is not used in Render.
It intentionally skips existing databases and is not a production migration
tool. Never reset, drop, or automatically downgrade the managed database.

## Initial Administrator

After confirming the production database target, run the documented interactive
administrator bootstrap process from [bootstrap-admin.md](bootstrap-admin.md).
It prompts for credentials and does not accept or print a fixed password.

## Public URLs and CORS

- API health: `https://<api-service>/api/v1/health`
- Frontend: `https://<frontend-service>/`
- API documentation: `https://<api-service>/docs`

Render terminates public HTTPS. The frontend calls the public API URL baked into
the static build, so the backend CORS allowlist must contain the exact frontend
origin before browser testing.

## Smoke Test

1. Confirm the API health endpoint returns HTTP 200.
2. Confirm the frontend loads over HTTPS and browser refresh preserves the SPA.
3. Sign in with the deliberately bootstrapped administrator account.
4. Create only disposable demonstration data and verify a project workflow.
5. Confirm the browser rejects API calls from an unapproved origin.

## Rollback and Recovery

Roll back the API and frontend to their last successful Render deploy only after
checking migration compatibility. Do not use automatic Alembic downgrades.
Before a public demo, confirm the selected managed PostgreSQL plan's backup and
restore features and document the recovery owner.

## Limitations

This configuration does not provide continuous deployment, a custom domain,
production observability, alerting, or an on-call responder. Render plan
availability, pricing, and pre-deploy eligibility must be confirmed in the
selected account before provisioning.
