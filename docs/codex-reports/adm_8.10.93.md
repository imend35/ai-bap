# ADIM 8.10.93 — Render Free Blueprint and Fail-Closed Startup Implementation

## Step Name and Objective

Implement a separate, zero-cost Render deployment configuration and a safe
migration-before-start mechanism without changing the paid Render Blueprint or
provisioning any cloud resource.

## Summary of Completed Work

- Added `render.free.yaml`, separate from the existing paid `render.yaml`.
  It defines a Free PostgreSQL database, Free Docker API service, and static
  React frontend in Frankfurt.
- Configured the Free API with a managed private `DATABASE_URL`, generated
  `JWT_SECRET_KEY`, operator-supplied `CORS_ORIGINS`, `/api/v1/health` health
  check, disabled automatic deployment, and no `preDeployCommand`.
- Configured the static frontend with a public `VITE_API_BASE_URL` service
  reference and an SPA rewrite. The `autoDeployTrigger` values are quoted so
  YAML parsers retain Render's documented `"off"` value.
- Added `docker/backend/start_api_free.py`. It launches the existing
  `migrate_production.py` first, so the existing PostgreSQL advisory lock and
  `alembic upgrade head` remain the sole migration implementation. It replaces
  itself with the existing `start_api.py` only on success.
- The Free wrapper returns nonzero on migration or API-process start failure,
  does not print secrets, and uses `os.execv` so the started API has correct
  process/signal ownership.
- Updated the backend Dockerfile only to copy and own the new wrapper. Its
  default command remains `start_api.py`; local Compose and the paid Blueprint
  therefore retain their existing startup behavior.
- Added six database-independent tests for the Free Blueprint, Docker
  selection, migration-before-API ordering, failure behavior, and absence of
  initialization/bootstrap behavior.
- Added `docs/deployment-render-free.md` with Free-tier limits, manual setup,
  migration behavior, required variable names, smoke tests, recovery limits,
  and the unresolved administrator-bootstrap gate.

## Files Inspected or Modified

### Inspected

- `AGENTS.md`
- `render.yaml` (preserved unchanged)
- `docker/backend/Dockerfile`
- `docker/backend/migrate_production.py`
- `docker/backend/start_api.py`
- `backend/app/config.py`
- `backend/tests/test_deployment_configuration.py`
- `docs/deployment-render.md`
- `docs/codex-reports/adm_8.10.92.md`
- `backend/app/test_database_safety.py` and `backend/tests/conftest.py`

### Created or modified

- `render.free.yaml`
- `docker/backend/start_api_free.py`
- `docker/backend/Dockerfile`
- `backend/tests/test_render_free_deployment_configuration.py`
- `docs/deployment-render-free.md`
- `docs/codex-reports/adm_8.10.93.md`

## Commands Executed and Actual Results

- Read-only repository/configuration inspection and branch/status review —
  PASS. The branch remained `docs/ci-pr-evidence`; all pre-existing reports
  were preserved.
- Initial static validation attempt with `uv run --no-sync` inside the file
  sandbox — BLOCKED because the existing user-level `uv` cache was inaccessible
  to the sandbox. No project file was changed by that attempt.
- `uv run --no-sync ruff check app/config.py
  tests/test_deployment_configuration.py
  tests/test_render_free_deployment_configuration.py
  ../docker/backend/migrate_production.py ../docker/backend/start_api.py
  ../docker/backend/start_api_free.py` — PASS: `All checks passed!`.
- `uv run --no-sync python -c ...` to parse the wrapper with Python AST and
  parse/assert the Free Blueprint structure — PASS.
- Focused pytest first run — FAIL: 5 passed, 1 failed because an unquoted YAML
  `off` was parsed as boolean `False` by the local YAML parser. The Free
  Blueprint was corrected by quoting the two `"off"` values; this was a
  configuration clarity correction, not a test weakening.
- `uv run --no-sync pytest -q tests/test_render_free_deployment_configuration.py`
  with process-local synthetic values solely for the pre-existing fail-closed
  pytest guard — PASS: `6 passed in 0.06s`. The test module parses files and
  mocks process execution; it creates no database engine, connection, schema,
  data, Docker resource, or network request.
- No frontend source changed, so a frontend build was NOT RUN as not relevant
  to this focused backend/Blueprint change.
- No full backend suite or database integration test was run.

## Test Results

| Check | Result |
| --- | --- |
| Free Blueprint static structure | PASS |
| Free startup wrapper Python syntax | PASS |
| Focused Free deployment tests | PASS — 6 passed |
| Ruff on affected Python files | PASS |
| Frontend build | NOT RUN — frontend source unchanged |
| Database integration tests | NOT RUN — no verified isolated test credential was used |
| Render provisioning/runtime verification | NOT RUN — prohibited by scope |

## Security and Safety Considerations

- `render.yaml` was not modified; the paid `preDeployCommand` path is intact.
- The Free Blueprint contains no credentials. It uses a managed database
  reference and generated JWT secret, while CORS remains operator-supplied.
- The wrapper never calls `initialize_fresh_database.py`, creates an
  administrator, or performs reset, truncate, drop, downgrade, or seed work.
- Migrations retain the existing advisory lock and fail closed before the API
  begins serving traffic.
- No cloud provisioning, billing action, Docker operation, database operation,
  Git staging, commit, push, pull-request action, or deployment occurred.

## Issues and Remaining Tasks

1. The current interactive administrator bootstrap cannot safely run against
   an externally blocked Render Free database because Free web services have no
   shell access. This remains the required security decision before an
   authenticated public demo.
2. Render Free PostgreSQL expires after 30 days and has no managed backup;
   Render Free APIs can cold-start after idle time. This configuration is only
   appropriate for disposable demo data.
3. The Free Blueprint and wrapper have static and mocked-test evidence only.
   A separately authorized disposable public runtime verification is required
   before any public-deployment claim.
4. Provider plan availability and account eligibility remain dashboard checks.

## Recommended Next Step

Obtain approval for a narrowly scoped, security-reviewed initial-administrator
bootstrap method. Then conduct a separately authorized Render Free provisioning
and public smoke-test step with disposable data, recording only sanitized
evidence.
