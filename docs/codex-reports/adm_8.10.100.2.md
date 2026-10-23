# ADIM 8.10.100.2 — Bootstrap Integration Failure Diagnosis & Fix

## Step Name and Objective

Diagnose and correct the two failing isolated initial-administrator bootstrap integration tests while preserving the fail-closed PostgreSQL guard, advisory-lock protection, Argon2id hashing, and non-sensitive production failure handling.

## Root Cause

The environment adapter was not the source of either failure. Its validation is performed before session creation and maps the existing bootstrap operation's result value directly to `EnvironmentBootstrapResult`.

The observed `FAILED` result in both scenarios proves that `bootstrap_initial_admin()` handled a `SQLAlchemyError`. In particular, the existing-email scenario cannot reach an insert or a record-number trigger before returning `EMAIL_EXISTS`; the shared operation that runs before its email lookup is acquisition of the PostgreSQL advisory lock.

Code review identified that the shared lifecycle helper passed the large advisory-lock key through an untyped SQL text bind. PostgreSQL advisory locking is overloaded, and the bootstrap key is intentionally larger than the 32-bit advisory-lock form. The bind now has an explicit `BIGINT` SQL cast, selecting the required one-key PostgreSQL advisory-lock signature deterministically.

This is the smallest fix to the shared operation implicated by both failures. It does not remove locking, alter lock scope, change the key, expose database errors, or modify result mapping.

## Implementation Changes

- Updated `backend/app/admin_user_lifecycle.py` so the transaction-scoped advisory lock invokes `pg_advisory_xact_lock` with an explicit `BIGINT` lock-key cast.
- Updated `backend/tests/test_bootstrap_admin.py` with a regression assertion that verifies the explicit `BIGINT` cast remains present.

The existing adapter continues to:

- require the exact literal `true` enable flag;
- reuse `UserRegister` validation;
- delegate to `bootstrap_initial_admin` rather than duplicating database logic;
- use existing Argon2id hashing;
- return generic safe outcomes rather than database details; and
- preserve email-conflict, active-administrator, and failure behavior.

## Files Inspected or Modified

### Inspected

- `AGENTS.md`
- `backend/app/initial_admin_bootstrap.py`
- `backend/app/admin_user_lifecycle.py`
- `backend/scripts/bootstrap_admin.py`
- `backend/app/database.py`
- `backend/app/models/user.py`
- `backend/app/routers/auth.py`
- `backend/app/schemas/auth.py`
- `backend/app/password_service.py`
- `backend/tests/test_bootstrap_admin.py`
- `backend/tests/test_initial_admin_bootstrap.py`
- `backend/tests/test_initial_admin_bootstrap_integration.py`
- `backend/tests/test_auth_login_api.py`
- `backend/tests/test_render_free_deployment_configuration.py`
- `docker/backend/bootstrap_initial_admin_from_environment.py`

### Modified

- `backend/app/admin_user_lifecycle.py`
- `backend/tests/test_bootstrap_admin.py`
- `docs/codex-reports/adm_8.10.100.2.md`

All unrelated pre-existing working-tree changes were preserved.

## Commands Executed and Results

| Command or check | Result |
| --- | --- |
| Source-path trace of adapter validation, result mapping, session handling, lifecycle lock, model, authentication route, and focused tests | PASS — the shared pre-email lock path was identified as the only common database operation for both returned `FAILED` outcomes. |
| `uv run --no-sync pytest -q tests/test_bootstrap_admin.py tests/test_initial_admin_bootstrap.py tests/test_render_free_deployment_configuration.py` | NOT RUN — pytest collection was stopped by the existing global fail-closed guard because required isolated-test variables and secrets were absent. No test module executed and no database connection was attempted. |
| `uv run --no-sync ruff check app/admin_user_lifecycle.py app/initial_admin_bootstrap.py scripts/bootstrap_admin.py tests/test_bootstrap_admin.py tests/test_initial_admin_bootstrap.py tests/test_initial_admin_bootstrap_integration.py tests/test_render_free_deployment_configuration.py ../docker/backend/bootstrap_initial_admin_from_environment.py ../docker/backend/start_api_free.py` | PASS — `All checks passed!` |
| `python -m py_compile` for the changed bootstrap and focused test modules | PASS — completed with exit code 0 and no output. |
| Process-local guarded environment presence check | BLOCKED — all required confirmation, target, database-password, and JWT variables were absent; values were not read or displayed. |
| `git diff --check` before creating this report | PASS — no whitespace errors; only pre-existing LF-to-CRLF warnings were emitted. |

## Security and Isolation Checks

- No database connection, query, migration, reset, cleanup, or test data mutation occurred during this step.
- The global pytest guard remained active; the blocked test command confirms it was not bypassed.
- The production Free startup entrypoint retains generic failure output and does not expose configured values, database errors, passwords, hashes, or URLs.
- The transaction-scoped PostgreSQL advisory lock is preserved, now with an unambiguous `BIGINT` argument.
- Existing users remain protected: email conflicts still return before any insert, and the implementation contains no promotion, overwrite, deletion, or deactivation path.

## Test Results

| Verification | Status |
| --- | --- |
| Static regression for explicit advisory-lock argument type | PASS — source-level assertion added and syntax validated; pytest execution awaits guarded environment setup. |
| Ruff | PASS |
| Focused bootstrap unit/static pytest modules | NOT RUN — blocked during global guard collection before test execution. |
| Initial-admin integration tests | NOT RUN — required test-only configuration and existing credentials are unavailable in this process. |
| Authentication/bootstrap database regressions | NOT RUN — same guarded-environment blocker. |

## Uncertainties and Blockers

The exact PostgreSQL server diagnostic was intentionally unavailable because no guarded test session was configured and no database connection was permitted. The code-path evidence identifies the shared overloaded lock call as the common source of the two converted `FAILED` outcomes; the guarded integration run remains required to prove the corrected PostgreSQL behavior end-to-end.

No cloud, Render, Docker lifecycle, database, Git staging, commit, or push action occurred. There is no new cost implication.

## Recommended Next Step

An operator should restore the existing isolated-test session by following `docs/isolated-test-database.md` and ADIM 8.10.98 without printing or replacing credentials. From `backend`, then run:

```powershell
uv run --no-sync pytest -q tests/test_initial_admin_bootstrap_integration.py tests/test_bootstrap_admin.py tests/test_initial_admin_bootstrap.py tests/test_auth_login_api.py tests/test_render_free_deployment_configuration.py
```

This command will verify initial creation, repeated no-op behavior, concurrent one-admin protection, email-conflict non-overwrite behavior, login, adapter validation, startup behavior, and the advisory-lock correction. It must run only against the documented guarded isolated PostgreSQL environment.

## Final GO / NO-GO

**GO for guarded isolated integration verification after an operator securely supplies the documented existing test-only session configuration.**

**NO-GO for database test execution in the current process** because the required fail-closed test environment variables and secrets are absent.
