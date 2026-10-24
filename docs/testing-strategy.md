# AI BAP — Testing Strategy

## Frontend Component Tests

The frontend uses Vitest, jsdom, React Testing Library, user-event, and jest-dom.
Run it without a live backend:

```powershell
Set-Location frontend
npm run test -- --run
```

The tests use mocked browser `fetch` responses and realistic accessible user
interactions. The initial suite covers the login form, native validation,
safe login failure feedback, and a successful mocked login that renders a
protected project workflow. No real account, token, API, Docker service, or
external provider is used.

## Backend Unit and Integration Tests

Backend tests include schema, security, contract, route, and integration
coverage. The shared Pytest fixture invokes the fail-closed database guard
before application imports. The supported backend command therefore requires
the explicitly prepared isolated PostgreSQL target:

```powershell
Set-Location backend
uv run --no-sync pytest -q --tb=short
```

The exact isolated target and test-only shell setup are documented in
[isolated-test-database.md](isolated-test-database.md). The development
database is never an acceptable fallback.

## Isolated Browser End-to-End Test

The repository includes one Playwright browser journey at
`frontend/e2e/authenticated-project.spec.ts`. It is intentionally separate
from Vitest and runs only against a newly created, disposable Docker Compose
project. The Playwright configuration requires an explicit loopback-only
`AI_BAP_E2E_BASE_URL` and literal `AI_BAP_E2E_ISOLATED=true`; it refuses a
non-loopback target. Synthetic account credentials are supplied only through
the calling process. Screenshots, traces, and videos are disabled by default.

The verified ADIM 8.10.168 execution used real local Google Chrome and a
fresh Compose project with loopback-only PostgreSQL, API, and frontend ports.
It verified all of the following:

- PostgreSQL health, successful migration, FastAPI health, frontend health,
  and same-origin API proxy health.
- Registration and UI login for a synthetic least-privileged
  business-analyst account.
- Projects navigation, project form completion, submission, and visible
  `role="status"` success feedback.
- Project visibility in the UI, browser reload, normal reauthentication, and
  retrieval of the persisted project after reload.
- A count-only PostgreSQL check scoped to the synthetic E2E project prefix.
- Ownership-verified removal of the disposable containers, network, volume,
  project image tags, and generated Playwright artifact, with the existing
  `ai-bap-rubric-test` stack preserved.

The result was **1 passed in 4.2 seconds**. This is isolated local browser
evidence only. It does not verify every product workflow, public deployment,
production HTTPS, continuous deployment, telemetry, alerting, or on-call
response. See [ADIM 8.10.168](codex-reports/adm_8.10.168.md) for the complete
sanitized execution record.

## Unified Runner

From the repository root, run:

```powershell
.\scripts\test-all.ps1
```

The runner executes frontend tests first. It then validates the required
isolated-test values in the current shell before it runs backend Pytest. If
that database setup is absent, it prints `SKIPPED`, gives the setup path, and
exits with code `2`; it never reports a partial run as overall success. It
does not start Docker, run migrations, or change a database.

The latest verified unified execution completed after the isolated environment
was explicitly prepared: the frontend phase passed 4 tests in 1 test file, the
backend phase passed 511 tests in 41.78 seconds, and the runner reported
`[TEST-ALL] PASS` (515 passed, 0 failed). This evidence does not remove the
preflight requirement for every future local run.

## Continuous Integration

GitHub Actions workflow [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)
runs on pushes and pull requests targeting `main`. Its frontend job installs
the lockfile with `npm ci`, then runs Vitest, the production build, and Oxlint.
Oxlint warnings remain visible in command output; a nonzero lint exit fails the
job.

The backend job runs against a fresh GitHub Actions PostgreSQL 16 service. The
service uses only synthetic CI values and is published to `127.0.0.1:55432`,
which is the exact host and port required by the existing fail-closed guard.
It also uses the required test database, user, confirmation value, and matching
test-password environment variables. Alembic runs only through
`scripts/run_isolated_test_alembic.py`, which verifies the effective target
before applying migrations. The service is ephemeral to the job and is not a
development or persistent database.

Local execution differs deliberately: `scripts/test-all.ps1` never starts
Docker or migrations, and exits nonzero when the documented isolated database
has not been prepared. GitHub Actions owns the disposable service lifecycle.

## Quality Checks

```powershell
Set-Location frontend
npm run build
npm run lint

Set-Location ..\backend
uv run --no-sync ruff check app tests migrations/versions
```

## Current Limitations

- Browser E2E coverage currently verifies one authenticated project workflow;
  requirement, user-story, task, sprint, archive-action, and role-specific
  workflows need additional coverage.
- Backend integration execution requires an operator-prepared isolated
  PostgreSQL target and test-only password for every run; the latest unified
  execution met those requirements and passed.
- The unified runner intentionally excludes Docker, migrations, and browser
  E2E. The browser journey has a separate, explicitly isolated Compose
  procedure and must never target a shared, development, or production
  database.
- Push-triggered CI for commit `1e4333738947f131816901b9fdb71e4fff61d4f2` and
  pull-request-triggered CI for commit `d88973895dced732e6aa7f00e4da5847ed0ba3d4`
  both completed successfully. CI does not provide continuous deployment.
