# ADIM 8.10.67 — GitHub Actions Continuous Integration

## Step Name and Objective

Implement a secure GitHub Actions continuous-integration workflow that validates
the frontend and backend on pushes and pull requests targeting `main`, without
introducing deployment automation or weakening database safety.

## Summary of Completed Work

- Added a least-privilege CI workflow at `.github/workflows/ci.yml`.
- Added a frontend job that uses Node.js 22, npm dependency caching, `npm ci`,
  Vitest, the production build, and Oxlint.
- Added a backend job that uses Python 3.13, locked `uv` dependencies, an
  ephemeral PostgreSQL 16 GitHub Actions service, guarded Alembic migrations,
  Pytest, and Ruff.
- Updated the README and testing strategy with the actual CI design and local
  versus CI test-execution differences.

## Files Inspected or Modified

### Inspected

- `AGENTS.md`
- `docs/Project.md`
- `backend/pyproject.toml`
- `backend/uv.lock`
- `backend/tests/conftest.py`
- `backend/app/test_database_safety.py`
- `backend/scripts/run_isolated_test_alembic.py`
- `backend/migrations/env.py` and migration revisions
- `docs/isolated-test-database.md`
- `frontend/package.json`, `frontend/package-lock.json`, `frontend/vite.config.ts`, and `frontend/src/App.test.tsx`
- `scripts/test-all.ps1`
- `README.md` and `docs/testing-strategy.md`
- Existing `.github/workflows/` contents (none existed before this step)

### Created or Modified

- Created `.github/workflows/ci.yml`.
- Modified `README.md`.
- Modified `docs/testing-strategy.md`.
- Created this report.

## Workflow Design and Database Safety

The workflow triggers on pushes to `main` and pull requests targeting `main`.
It uses `permissions: contents: read` and does not use `pull_request_target`,
deployment credentials, production secrets, persistent volumes, or external
infrastructure.

The backend test guard requires the exact isolated target:

- host `127.0.0.1`
- port `55432`
- database `ai_bap_test`
- user `ai_bap_test_user`
- `AI_BAP_TEST_MODE=true`
- `AI_BAP_TEST_DATABASE_CONFIRMATION=isolated-postgresql-acknowledged`
- matching `POSTGRES_PASSWORD` and `AI_BAP_TEST_POSTGRES_PASSWORD`

The backend CI job supplies those exact values to an ephemeral PostgreSQL 16
service mapped as `55432:5432`. Its password is a synthetic job-local test
value and commands do not print it. The job runs migrations only through
`scripts/run_isolated_test_alembic.py`; that wrapper validates both the explicit
guard values and the effective SQLAlchemy target before it invokes Alembic.
This configuration is compatible with the existing guard and cannot target a
development database when the declared CI values are used.

## Commands Executed and Actual Results

- `npm run test -- --run` — PASS: 1 test file and 4 tests passed.
- `npm run build` — PASS: TypeScript and Vite production build completed.
- `npm run lint` — PASS: 0 errors; 16 existing `react(set-state-in-effect)` warnings remained in `src/App.tsx`.
- `uv run --no-sync ruff check app tests migrations/versions` — PASS: all checks passed.
- `git diff --check` — PASS. Git emitted existing line-ending conversion notices only; no whitespace errors were reported.
- Local GitHub Actions execution — NOT RUN: remote workflow execution requires a pushed branch or pull request, and no push was authorized.

## Validation and Test Results

- Frontend tests: PASS (4/4).
- Frontend production build: PASS.
- Frontend lint: PASS with 16 retained warnings and no errors.
- Backend Ruff: PASS.
- Backend Pytest and guarded Alembic migration: NOT RUN locally. They require the dedicated isolated PostgreSQL target; this step did not start Docker, modify databases, or run migrations.
- Workflow YAML: manually reviewed for trigger, job, service, environment, and command structure. A local GitHub Actions runner or YAML-specific workflow validator was not available, so remote GitHub Actions validation remains pending.

## Issues and Remaining Tasks

- The workflow has not yet run on GitHub because no commit or push was authorized.
- The 16 existing Oxlint warnings remain visible and do not produce a nonzero lint exit; their safe resolution remains separately scoped work.
- CI is validation-only. Continuous deployment, public deployment, observability, alerting, and controlled on-call response are outside this step.

## Recommended Next Step

Review the workflow, then commit and push it through a normal branch or pull
request. Confirm the first GitHub Actions run passes the frontend job and the
guarded backend migration/test/Ruff job before relying on CI evidence for the
submission rubric.
