# ADIM 8.10.98 — Isolated Test Environment Recovery

## Step Name and Objective

Identify the documented, non-destructive procedure for restoring the current PowerShell session's isolated PostgreSQL integration-test configuration without recovering, displaying, or changing credentials or database resources.

## Summary of Completed Work

- Reviewed the documented isolated-test procedure, test Compose file, non-secret Compose variables, pytest fixture, database safety guard, and application configuration requirements.
- Performed presence-only checks for required process-local variables; no values were read or printed.
- Performed read-only Docker inspection limited to the test container's Compose labels, health status, named-volume mount, and loopback port publication.
- Confirmed that the documented operator procedure supports secure interactive supply of the existing test-only password. No password was searched for, recovered, generated, copied, or changed.

## Files Inspected or Modified

### Inspected

- `AGENTS.md`
- `docs/isolated-test-database.md`
- `compose.test.yaml`
- `docker/compose-test.variables`
- `backend/tests/conftest.py`
- `backend/app/test_database_safety.py`
- `backend/app/config.py`

### Modified

- `docs/codex-reports/adm_8.10.98.md` (this report only).

All pre-existing working-tree changes were preserved.

## Verified Facts

The currently running test resource is structurally attributable to the dedicated `ai-bap-test` Compose project, rather than being identified by a database name alone:

- Container: `ai-bap-test-db-test-1`, PostgreSQL image, healthy.
- Compose labels identify project `ai-bap-test` and service `db-test`.
- The database data mount is the dedicated, Compose-labelled `ai-bap-test_ai_bap_test_data` volume.
- PostgreSQL is published only on the documented loopback test port (`127.0.0.1:55432`), not a public interface.

This is sufficient evidence that the existing Docker resource is the documented isolated Compose topology. It does not grant access to credentials or authorize database access.

## Required Session Variables and Classification

### Non-secret isolated-target values

- `AI_BAP_TEST_MODE`
- `AI_BAP_TEST_DATABASE_CONFIRMATION`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`

The exact confirmation literal and isolated target tuple must come directly from `backend/app/test_database_safety.py` and `docs/isolated-test-database.md`; the guard requires an exact match and overwrites later-loaded database settings with that verified tuple.

### Secrets

- `AI_BAP_TEST_POSTGRES_PASSWORD` — existing test-only PostgreSQL password, supplied interactively by the operator.
- `POSTGRES_PASSWORD` — must be set to the same in-session value as `AI_BAP_TEST_POSTGRES_PASSWORD`.
- `JWT_SECRET_KEY` — application signing secret required by application settings; it must be supplied securely by the operator and must satisfy the existing configuration validation. It is not a database password.

### Presence result

At the time of this review, all variables above were absent from the Codex process. Their values were not inspected. This absence prevents guarded pytest initialization and is an intended fail-closed condition.

## Safe Operator Setup Procedure

The following procedure restores values only in the current operator PowerShell session. It does not create, reset, start, stop, connect to, migrate, or otherwise modify Docker or PostgreSQL resources. The operator must obtain the existing test-only password and an existing valid local JWT signing secret from their approved secure source; neither value should be pasted into chat or committed to a file.

```powershell
# From the repository root. Input remains hidden at the prompt.
$env:AI_BAP_TEST_POSTGRES_PASSWORD = Read-Host "Enter existing test database password" -AsSecureString |
    ForEach-Object { [System.Net.NetworkCredential]::new("", $_).Password }

$env:AI_BAP_TEST_MODE = "true"
$env:AI_BAP_TEST_DATABASE_CONFIRMATION = "isolated-postgresql-acknowledged"
$env:POSTGRES_HOST = "127.0.0.1"
$env:POSTGRES_PORT = "55432"
$env:POSTGRES_DB = "ai_bap_test"
$env:POSTGRES_USER = "ai_bap_test_user"
$env:POSTGRES_PASSWORD = $env:AI_BAP_TEST_POSTGRES_PASSWORD

# Supply an existing valid signing secret without echoing it.
$env:JWT_SECRET_KEY = Read-Host "Enter existing local test JWT signing secret" -AsSecureString |
    ForEach-Object { [System.Net.NetworkCredential]::new("", $_).Password }

# Presence-only check: this prints no values.
$required = @(
    "AI_BAP_TEST_MODE", "AI_BAP_TEST_DATABASE_CONFIRMATION", "POSTGRES_HOST",
    "POSTGRES_PORT", "POSTGRES_DB", "POSTGRES_USER",
    "AI_BAP_TEST_POSTGRES_PASSWORD", "POSTGRES_PASSWORD", "JWT_SECRET_KEY"
)
$required | ForEach-Object {
    if (-not (Test-Path "Env:$_")) { throw "Required isolated-test variable is missing: $_" }
}
```

The operator should not substitute the application `.env` file, use the default application Compose project, or generate a replacement PostgreSQL password. The documented `docker compose ... up` command is intentionally not part of this recovery procedure because the dedicated test container is already healthy and this step does not authorize Docker lifecycle operations.

## Commands Executed and Results

| Command or check | Result |
| --- | --- |
| Read-only review of documented test configuration and guards | PASS — exact fail-closed requirements identified. |
| Presence-only process-environment check | PASS — all required variable names checked; all were absent; no values shown. |
| Read-only Docker container, volume-label, mount, and port inspection | PASS — the healthy resource matches the dedicated `ai-bap-test` Compose topology. |
| Database connection, migration, test, initialization, restart, or cleanup | NOT RUN — prohibited by this recovery-only step. |

## Issues, Uncertainties, and Cost Implications

- The existing test-only PostgreSQL password and the required JWT signing secret are unavailable in the current process. This is the sole operational blocker.
- The Compose labels and loopback binding verify Docker resource isolation, but no database connection was made; live schema and contents were intentionally not inspected.
- No cloud service, paid resource, image build, container lifecycle action, or database operation occurred. This assessment has no new cost implication.

## Recommended Next Step

After the operator completes the interactive session setup above, run the separately authorized guarded integration verification from `backend`:

```powershell
uv run --no-sync pytest -q tests/test_initial_admin_bootstrap_integration.py tests/test_bootstrap_admin.py tests/test_auth_login_api.py
```

The existing guard must remain enabled. If any prerequisite cannot be provided securely, keep the integration suite blocked rather than substituting credentials or targeting another database.

## Final GO / NO-GO

**GO for operator-led restoration of the current session using the documented interactive procedure.**

**NO-GO for Codex-run integration tests until those existing secrets and guard variables are present in the invoking process.**
