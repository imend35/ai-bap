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

- Frontend coverage begins with authentication and project behavior; requirement,
  user-story, task, sprint, and archive-action flows need additional coverage.
- Backend integration execution requires an operator-prepared isolated
  PostgreSQL target and test-only password for every run; the latest unified
  execution met those requirements and passed.
- The unified runner intentionally excludes Docker, migrations, and deployment.
- A push-triggered CI run completed successfully for commit
  `1e4333738947f131816901b9fdb71e4fff61d4f2`. The workflow is configured for
  pull requests targeting `main`; direct pull-request execution evidence must
  be recorded separately. CI does not provide continuous deployment.
