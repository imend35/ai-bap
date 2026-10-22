# ADIM 8.10.84 — Render Deployment Configuration Preparation

## Step Name and Objective

Prepare a secure, repeatable Render deployment configuration for managed
PostgreSQL, a Docker-based FastAPI API, and a Vite static frontend without
provisioning services or modifying existing Docker or database resources.

## Summary of Completed Work

- Added a Render Blueprint that defines a managed PostgreSQL database, a
  Docker API service, and a static frontend service.
- Added a managed `DATABASE_URL` configuration path while preserving the
  existing local `POSTGRES_*` configuration path and failing closed when
  neither supplies a passworded database target.
- Added a deployment migration command that takes a PostgreSQL advisory lock
  before running `alembic upgrade head`. It does not use the local
  fresh-database initializer, reset data, bootstrap an administrator, or run
  downgrades.
- Added platform-port API startup so Render can provide `PORT` while local
  Compose retains port 8000 by default.
- Changed the production frontend fallback from an embedded localhost API URL
  to same-origin relative requests. The Blueprint explicitly injects the API
  public URL at static-build time.
- Added deployment configuration unit coverage and deployment documentation.

## Files Inspected or Modified

Inspected: `AGENTS.md`, `compose.yaml`, backend configuration and entry-point
modules, Alembic configuration and migrations, backend/frontend Dockerfiles,
frontend API handling, nginx configuration, `.env.example`, README, isolated
database guidance, and administrator bootstrap guidance.

Modified or created:

- `.env.example`
- `README.md`
- `backend/app/config.py`
- `backend/tests/test_deployment_configuration.py`
- `docker/backend/Dockerfile`
- `docker/backend/migrate_production.py`
- `docker/backend/start_api.py`
- `docs/deployment-render.md`
- `frontend/src/App.tsx`
- `render.yaml`

Pre-existing pending files were preserved unchanged:

- `docs/codex-reports/adm_8.10.76.md`
- `docs/codex-reports/adm_8.10.82.md`
- `docs/codex-reports/adm_8.10.83.md`

## Deployment Design

`render.yaml` uses a private managed PostgreSQL connection supplied to the API
as `DATABASE_URL`, a generated `JWT_SECRET_KEY`, an operator-supplied explicit
`CORS_ORIGINS` value, Render's platform `PORT`, a health check at
`/api/v1/health`, and a static-site SPA rewrite. Automatic deploys are disabled
for human approval. The frontend receives only the public API URL as a build
variable; it receives no secret.

The API pre-deploy command serializes migrations with a PostgreSQL advisory
lock. A failed migration prevents the new API deployment from proceeding. No
automatic downgrade is configured; rollback requires reviewing migration
compatibility and selecting a prior successful service deployment.

## Commands Executed and Results

- `uv run --no-sync ruff check app/config.py ../docker/backend/migrate_production.py ../docker/backend/start_api.py tests/test_deployment_configuration.py` — PASS: all checks passed.
- `uv run --no-sync pytest -q tests/test_deployment_configuration.py` — NOT RUN: collection stopped before test execution because the existing fail-closed guard requires `AI_BAP_TEST_MODE=true`. No guard was bypassed and no database was contacted.
- `uv run --no-sync python -c "... Settings(_env_file=None) ..."` with synthetic values — PASS: the managed PostgreSQL `DATABASE_URL` was accepted and normalized to the `postgresql+psycopg` driver without a database connection.
- `uv run --no-sync python -c "... yaml.safe_load('../render.yaml') ..."` — PASS: YAML parsed and the expected database plus two-service shape was confirmed. Render-schema compatibility was also manually reviewed against Render Blueprint documentation; it is not a live Render validation.
- `npm run build` — PASS: TypeScript and Vite production build completed successfully.
- `npm run lint` — PASS with 16 existing non-blocking `react(set-state-in-effect)` warnings and no lint errors.
- `git diff --check` — PASS.
- `git status --short` — reviewed; only the ADIM 8.10.84 files and the three explicitly preserved pre-existing pending reports were pending.

No Docker build, container lifecycle command, database operation, migration,
deployment, staging, commit, or push was performed by this step.

## Validation and Test Results

- Modified Python static checks: PASS.
- Managed database configuration self-check: PASS.
- Blueprint YAML and expected-shape check: PASS.
- Frontend production build: PASS.
- Frontend lint: PASS with 16 existing non-blocking warnings.
- Targeted backend pytest: NOT RUN because the isolated-test environment was
  not configured in this process. The test guard remained fail-closed.
- Docker, Render provisioning, production migration execution, and public
  deployment smoke tests: NOT RUN by task restriction.

## Security Considerations

- No credential, JWT, database URL, or API key value is committed.
- Render generates the JWT signing secret; CORS must be configured with the
  exact public frontend HTTPS origin.
- The managed database remains privately addressed by the API service and is
  not a public database endpoint.
- The production migration path is intentionally separate from the guarded
  local fresh-database initializer.

## Issues and Remaining Tasks

- Render provisioning, plan availability, pre-deploy-command eligibility, and
  actual public URL values require confirmation in the selected Render account.
- No public deployment, production HTTPS verification, CD, observability,
  alerting, or on-call capability is established by this preparation step.
- An authorized deployment should confirm platform-specific private database
  connectivity and execute the documented smoke test with disposable data.

## Recommended Next Step

Complete static validation, then obtain explicit approval before creating
Render resources or deploying the Blueprint. Review the generated service
names, exact CORS origin, plan availability, and managed database backup
settings with the Human Product Owner.
