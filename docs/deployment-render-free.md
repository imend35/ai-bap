# Render Free Demonstration Deployment Guide

## Scope

I use this configuration only for a short-lived, zero-cost AI BAP capstone
demonstration. It is not a production deployment and does not authorize cloud
provisioning by itself.

[`render.free.yaml`](../render.free.yaml) is separate from the paid
[`render.yaml`](../render.yaml) Blueprint. It creates a Free Render PostgreSQL
database, a Free Docker FastAPI service, and a static React frontend. Automatic
deployments are disabled.

## Free-Plan Limitations

- Free Render Postgres is limited to 1 GB, expires 30 days after creation, and
  has no managed backups or connection pooling.
- Render may restart the database or Free API service. A Free web service spins
  down after 15 minutes without inbound traffic; the first later request can
  take about one minute while it wakes.
- Free services have monthly included resource limits. A workspace with a
  payment method can incur overages; without one, Render can suspend affected
  services or builds after limits are reached.
- Treat all demonstration data as disposable. Export or recreate it before the
  database expiration; do not depend on this configuration for recovery.

See the current provider limits before provisioning:
<https://render.com/docs/free>.

## Manual Deployment Process

1. In the intended Render workspace, choose the repository Blueprint at
   `render.free.yaml`; do not substitute the paid `render.yaml`.
2. Confirm the Free plans, `frankfurt` region, resource names, and account
   eligibility in the Render Dashboard before creating anything.
3. Keep the database public IP allowlist empty. The API receives
   `DATABASE_URL` from the managed database reference over Render's private
   network.
4. Let Render generate `JWT_SECRET_KEY`. Never add this value to Git, chat,
   or frontend build variables.
5. After the static frontend URL is known, provide `CORS_ORIGINS` as a JSON
   list containing only that exact HTTPS origin. Do not use a wildcard.
6. Keep `PUBLIC_REGISTRATION_ENABLED=false`. Public account creation is not
   appropriate for the shared demo workspace. Login remains available for
   deliberately provisioned, active accounts.
7. Deploy only after a Human Product Owner authorizes provisioning and billing
   review.

## Migration-Before-Start Behavior

Free web services cannot use Render's paid-only pre-deploy command. The Free
API therefore overrides the Docker command with
`python /usr/local/bin/start_api_free.py`.

The wrapper runs the existing `migrate_production.py` first. That script
requires the managed PostgreSQL configuration, obtains the deployment advisory
lock, and runs `alembic upgrade head`. Only after a successful exit does the
wrapper replace itself with the existing `start_api.py` process. A migration or
process-start failure returns nonzero and leaves the API unavailable.

The local Compose-only `initialize_fresh_database.py` is never used. The
configuration does not reset, drop, truncate, downgrade, seed, or otherwise
destructively initialize a database.

## One-Time Initial Administrator Bootstrap

The Free startup wrapper runs, in order: the advisory-locked Alembic migration,
the internal environment bootstrap adapter, and the API process. The bootstrap
adapter is disabled unless `AI_BAP_INITIAL_ADMIN_BOOTSTRAP_ENABLED` is exactly
`true`.

For one approved first deployment, configure all of the following directly in
the Render Dashboard:

- `AI_BAP_INITIAL_ADMIN_BOOTSTRAP_ENABLED=true`
- `AI_BAP_INITIAL_ADMIN_EMAIL`
- `AI_BAP_INITIAL_ADMIN_FULL_NAME`
- `AI_BAP_INITIAL_ADMIN_PASSWORD` as a secret value

The adapter validates the existing `UserRegister` rules and reuses the
existing Argon2id password hashing and transaction-scoped active-administrator
advisory lock. It exposes no public HTTP route. It creates at most one active
administrator, leaves existing users unchanged, and treats an existing active
administrator as a safe no-op.

Enabled but incomplete/invalid values, an existing-email conflict, or a
bootstrap failure prevent API startup. Do not add these values to the
Blueprint, source files, local environment files, logs, or browser requests.
Immediately after successful first creation, remove all four values in the
Render Dashboard and trigger a controlled redeploy. The application never
attempts to alter Render environment configuration itself.

After bootstrap, use an authorized admin-only mechanism to provision only the
least-privileged business-analyst account(s) required for the demonstration.
Never publish the administrator or demo credentials. Share demo credentials
only with explicitly authorized evaluators through a private channel; never
place them in Git, the README, frontend environment variables, browser bundles,
or public URLs.

Use a dedicated fresh demonstration database containing synthetic data only.
Before public exposure, verify that no unauthorized existing accounts are
present; disabling registration does not revoke accounts already in the
database. All provisioned business analysts share the demonstration workspace.
This configuration does not provide tenant isolation, so do not use real or
confidential data. If arbitrary untrusted visitors need publicly posted login
credentials, this shared-workspace design is insufficient and must not be
represented as safe for that use case. Login throttling or account lockout has
not been established and remains a residual risk.

## Required Environment Variables

- `DATABASE_URL`: supplied by the managed database reference; secret.
- `JWT_SECRET_KEY`: generated and stored by Render; secret.
- `CORS_ORIGINS`: operator-supplied JSON list of exact frontend HTTPS origins.
- `PORT`: configured for the API service by the Blueprint.
- `PUBLIC_REGISTRATION_ENABLED`: keep `false` for the controlled public demo;
  the application default is also `false`. Enable only in an isolated local
  development environment when registration behavior is specifically needed.
- `VITE_API_BASE_URL`: public API URL reference used only during static-site
  build; it is public, not a secret.

The one-time `AI_BAP_INITIAL_ADMIN_*` variables are deliberately omitted from
the Blueprint. See [bootstrap-admin.md](bootstrap-admin.md) for their
temporary, operator-managed lifecycle.

Optional AI drafting variables are not needed for a basic demonstration. If
used, configure them only as platform secrets and never in the frontend build.

## HTTPS Smoke Tests

After separately authorized provisioning, use disposable data only:

1. Request `https://<api>/api/v1/health` and expect HTTP 200.
2. Request `https://<frontend>/` and refresh an application route to confirm
   the SPA rewrite works.
3. Confirm the browser sends API requests to the public API HTTPS URL.
4. Confirm the configured frontend origin is accepted and an unapproved origin
   is rejected by CORS.
5. Record URLs and results without recording credentials or connection URLs.

## Administrator Bootstrap Approval Gate

The startup bootstrap code is implemented and tested locally, but no Render
service has been provisioned. A Human Product Owner must separately approve
the temporary Render-secret lifecycle, then verify creation and mandatory
secret removal with disposable data during an authorized runtime test.

Registration protection is implemented at the API boundary as well as
configured in this Free Blueprint. Render provisioning and deployment still
require separate Human Product Owner authorization; this documentation does
not authorize either action.

## Recovery

This Free configuration has no managed database backup or durable recovery
promise. If a migration fails, do not force an Alembic downgrade. Preserve
deployment logs, diagnose against a disposable copy where possible, and obtain
approval for any recovery action. A failed start is intentionally safer than
serving an API against an unknown schema.
