# ADIM 8.10.91 — Render Provisioning Readiness and Cost Review

## Step Name and Objective

Perform a final read-only assessment of the committed Render Blueprint before
any account action, billing selection, resource creation, migration, or public
deployment.

## Repository and Configuration Verified

- Branch: `docs/ci-pr-evidence`.
- Latest committed deployment preparation: `e109f0fcecab2d400253c4b9b800f49765a10dd4`
  (`feat: prepare secure Render deployment configuration`).
- Inspected committed versions of `render.yaml`, the Render deployment guide,
  backend Dockerfile, production migration/start scripts, and application
  configuration.
- Existing pending ADIM 8.10.76, 8.10.88, 8.10.89, and 8.10.90 reports were
  preserved unchanged.

## Blueprint Readiness Assessment

| Configuration | Assessment |
| --- | --- |
| Render Postgres `0.1c-256mb` | Supported current PostgreSQL plan ID; paid Basic 256 MB plan. |
| API `0.5c-512mb` | Supported current web-service plan ID; paid Starter-equivalent plan. |
| `frankfurt` | Supported Render region for the API and database. Static sites are globally hosted. |
| Docker configuration | `runtime: docker`, root build context, and Dockerfile path are documented Blueprint fields. Render uses the Dockerfile `CMD` when no Docker command is supplied. |
| Production migration | `preDeployCommand` is documented for migrations and is available to paid web services. The selected API plan is paid. A failure prevents the new deploy from proceeding. |
| `DATABASE_URL` | `fromDatabase.connectionString` is a documented private Render Postgres connection reference. The application normalizes it to the psycopg SQLAlchemy driver. |
| JWT secret | `generateValue: true` avoids committing a signing secret. |
| CORS | `sync: false` is supported and prompts for a value at initial Blueprint creation. The exact frontend HTTPS origin must be supplied as a JSON list. |
| Frontend URL | `fromService` references are supported. `VITE_API_BASE_URL` is a public build-time value, not a secret. |
| Static site | `runtime: static`, build command, publish path, and SPA rewrite are supported. |
| Automatic deployments | `autoDeployTrigger: off` is supported and disables commit-driven automatic deploys. |

## Cost and Eligibility Assessment

The selected PostgreSQL plan and API plan are paid plans. Therefore their
creation can incur recurring service charges, and Docker builds plus
pre-deploy commands consume pipeline minutes. The static frontend has no
compute plan and can be deployed free, but it still counts against included
bandwidth and pipeline-minute usage.

No price is asserted in this report because billing availability, current
currency, workspace plan, taxes, included credits, and account-specific limits
must be confirmed in the Render Dashboard immediately before provisioning.

The configured paid PostgreSQL plan avoids the free-database 30-day expiration
and free-tier lack of backups. Render documents point-in-time recovery for paid
Postgres, with the available recovery window depending on workspace plan. The
Human Product Owner must still confirm the selected workspace's backup, export,
recovery-window, and billing terms before creating data that matters.

## Uncertainties and Mandatory Provisioning Blockers

1. **Billing authorization:** creating the selected API and PostgreSQL plans
   can begin charges. Account eligibility and billing approval are unverified.
2. **Exact CORS value:** `CORS_ORIGINS` is intentionally operator-supplied.
   The initial Blueprint flow requires the exact frontend HTTPS origin as a
   JSON list. If the generated static-site URL differs from an assumed service
   URL, the operator must update CORS before browser API testing.
3. **Account capacity and name availability:** service/database names, plan
   availability, region availability, and service limits are account-specific
   and unverified.
4. **Runtime evidence:** Render has not built the Docker image, connected the
   managed database, executed the pre-deploy migration, or served public URLs.

## Manual Dashboard Provisioning Checklist

1. Sign in to the intended Render workspace and connect the approved GitHub
   repository and `docs/ci-pr-evidence` branch for this review deployment.
2. Select the repository Blueprint at `render.yaml`; review the three planned
   resources before confirming creation.
3. Confirm `frankfurt`, the paid PostgreSQL `0.1c-256mb` plan, the paid API
   `0.5c-512mb` plan, storage/recovery expectations, and all displayed billing
   implications. Do not proceed without Human Product Owner approval.
4. Confirm the database remains externally blocked by the empty public IP
   allowlist and that the API receives only the managed private connection
   reference.
5. Let Render generate `JWT_SECRET_KEY`; never replace it with a repository or
   chat value.
6. Provide `CORS_ORIGINS` as a JSON list containing only the exact frontend
   HTTPS origin. Confirm the static-site URL first if necessary, then update
   the API environment value before browser testing.
7. Confirm the API pre-deploy command is
   `python /usr/local/bin/migrate_production.py`; do not substitute the local
   fresh-database initializer. Review the deployment log to confirm migration
   success and advisory-lock release.
8. Manually deploy after a final approval, then verify the API health endpoint,
   frontend HTTPS response and refresh behavior, frontend-to-API requests, and
   an authenticated flow using a deliberately bootstrapped administrator.
9. Record the generated URLs, deployment log links, smoke-test results, and
   rollback owner without recording secrets. Configure a custom domain only in
   a separately approved scope.

## Commands Executed and Validation Results

- Read committed configuration with `git show HEAD:<path>` — PASS.
- Read-only official Render documentation review — PASS.
- No Render Dashboard, API, CLI, provisioning, billing, Docker, database, Git
  staging, commit, push, or PR action was performed.
- `git diff --check` and final working-tree review — pending after this report
  is created.

## Final GO / NO-GO

**GO for a Human Product Owner-led Render Dashboard review and explicit billing
decision.** The committed Blueprint uses supported current plan IDs and
deployment fields, and its production migration mechanism requires the paid
API plan it selects.

**NO-GO for unattended provisioning or public deployment.** Provisioning must
wait for billing approval, account-specific plan/name confirmation, the exact
frontend CORS origin, and a separately authorized deployment smoke-test step.

## Recommended Next Step

Obtain explicit authorization to open the Render Dashboard and review the
Blueprint creation screen. Confirm the paid-plan charges and exact frontend
origin before creating any resource.
