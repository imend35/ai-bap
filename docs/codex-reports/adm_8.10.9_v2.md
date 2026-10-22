# ADIM 8.10.9 v2 — Resolve Isolated Test Environment Setup

## Step name and objective

Prepare a safe operator procedure for supplying the isolated PostgreSQL test
environment to the current PowerShell session, checking schema state without
writing data, and avoiding unnecessary Docker elevation.

## Summary of completed work

- Distinguished this environment-setup task from the original ADIM 8.10.9
  execution precheck recorded in `adm_8.10.9.md`.
- Identified the documented isolated-test variables and non-secret target
  values from `docs/isolated-test-database.md`.
- Documented the secure interactive password-entry approach: read the existing
  test-only password into the current shell without printing or storing it in a
  repository file.
- Identified the guarded Alembic wrapper as the documented mechanism for
  schema inspection or migration work against the isolated target.

## Files inspected or modified

Inspected, based on the recorded task scope:

- `docs/isolated-test-database.md`
- `backend/app/test_database_safety.py`
- `backend/tests/conftest.py`
- `compose.test.yaml`
- `docker/compose-test.variables`

Modified:

- `docs/codex-reports/adm_8.10.9_v2.md` (retrospective reconstruction only)

## Commands executed and actual results

The recorded ADIM 8.10.9 v2 task was read-only and did not authorize pytest,
Ruff, migrations, Docker lifecycle changes, Git changes, or database writes.
No step-specific command output proves those operations were run.

The documented operator procedure uses an interactive, current-session
test-password prompt and the fail-closed isolated-test confirmation values.
The exact procedure remains in `docs/isolated-test-database.md`; no secret or
credential assignment is reproduced in this retrospective report.

The proposed read-only schema-state check was the guarded command below, to be
run only after the environment values were supplied:

```powershell
Set-Location backend
uv run python scripts/run_isolated_test_alembic.py current
```

## Validation and test results

- Isolated target variable names and non-secret values: documented from the
  checked-in procedure.
- Pytest: NOT RUN in this setup-only task.
- Ruff: NOT RUN in this setup-only task.
- Migrations and database writes: NOT RUN.
- Docker lifecycle changes: NOT RUN.

## Issues and remaining tasks

- The original `adm_8.10.9_v2.md` file was empty.
- The test-only password must be supplied by an authorized operator in the
  current shell; it must not be committed, printed, or included in a report.
- Docker elevation is not required for environment-variable setup or guarded
  Alembic invocation. Docker access is only needed when inspecting or operating
  the isolated container and should be requested only when the normal user
  lacks Docker daemon access.

## Recommended next step

After confirming the isolated container and schema, run the separately approved
backend verification commands with the guarded environment in place.
