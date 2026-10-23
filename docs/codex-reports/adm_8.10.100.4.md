# ADIM 8.10.100.4 — PostgreSQL Bootstrap Root Cause Investigation

## Step Name and Objective

Reassess the two isolated initial-administrator bootstrap integration failures after the prior advisory-lock `BIGINT` cast did not resolve them. The objective is to obtain safe, actionable diagnostic evidence without weakening database isolation, exposing sensitive details, or applying a speculative production fix.

## Investigated Execution Paths

The following path was reviewed end to end:

1. `bootstrap_initial_admin_from_environment()` requires the exact enable flag, rejects incomplete values, and delegates to the existing bootstrap operation.
2. `bootstrap_initial_admin()` validates data using `UserRegister`, opens `SessionLocal`, acquires a transaction-scoped PostgreSQL advisory lock, checks the requested email, checks for an existing active administrator, hashes with Argon2id, creates the user, and commits.
3. `IntegrityError` is mapped to the existing generic email-conflict result; other `SQLAlchemyError` instances are rolled back and mapped to the generic failed result.
4. The Free startup child retains generic public output and does not receive or print the new test diagnostic callback.
5. The integration tests establish their preconditions using the guarded `SessionLocal`, call the environment adapter, then exercise login and concurrency behavior.

The global pytest fixture and `app.test_database_safety` still require the documented isolated target and matching test-only password before importing application database modules.

## Diagnostic Evidence and Root-Cause Status

The operator-reported run executed 46 tests: 44 passed and the two integration tests failed with `EnvironmentBootstrapResult.FAILED`.

That generic result confirms only that the bootstrap operation caught a non-integrity `SQLAlchemyError`; it does **not** confirm whether the underlying cause is advisory locking, permissions, schema state, transaction state, or another SQL execution failure. The previously added `BIGINT` cast did not change the outcome and was therefore reverted. It must not be treated as a confirmed root cause or retained as a speculative production change.

**Confirmed root cause: unresolved pending safe integration diagnostics.**

## Changes Made

### Safe diagnostic mechanism

- Added an optional `diagnostic_reporter` callback to the internal bootstrap operation and environment adapter.
- The callback is optional and absent for production startup callers.
- On a caught SQLAlchemy error it receives only a fixed execution phase (`advisory_lock`, `email_lookup`, `active_admin_lookup`, or `create_admin`) and one whitelisted classification (`integrity_error`, `operational_error`, `programming_error`, or `sqlalchemy_error`).
- It never receives exception text, SQL, parameters, database URLs, credentials, personal data, or password hashes.
- The integration tests pass this callback and include its sanitized list only as a pytest assertion message when an assertion fails.

### Regression protection

- Added a non-database unit test verifying that an advisory-lock programming error reports only `advisory_lock:programming_error` and not the simulated exception text.
- Reverted the unproven explicit advisory-lock `BIGINT` cast and its source assertion. The transaction-scoped lock helper has no final source change; its key and existing behavior are unchanged.

## Files Inspected or Modified

### Inspected

- `AGENTS.md`
- `backend/app/initial_admin_bootstrap.py`
- `backend/app/admin_user_lifecycle.py`
- `backend/app/database.py`
- `backend/app/config.py`
- `backend/app/models/user.py`
- `backend/scripts/bootstrap_admin.py`
- `backend/tests/test_bootstrap_admin.py`
- `backend/tests/test_initial_admin_bootstrap.py`
- `backend/tests/test_initial_admin_bootstrap_integration.py`
- `backend/tests/test_auth_login_api.py`
- `backend/tests/test_render_free_deployment_configuration.py`
- `backend/migrations/env.py`
- Record-number migration and regression-test sources
- `docker/backend/bootstrap_initial_admin_from_environment.py`
- `docker/backend/start_api_free.py`

### Modified

- `backend/app/initial_admin_bootstrap.py`
- `backend/tests/test_bootstrap_admin.py`
- `backend/tests/test_initial_admin_bootstrap_integration.py`
- `docs/codex-reports/adm_8.10.100.4.md`

All pre-existing working-tree changes were preserved.

## Commands Executed and Results

| Command or check | Result |
| --- | --- |
| Source inspection of bootstrap adapter, lock SQL, session factory, engine settings, user schema, migrations, integration setup, and authentication path | PASS — execution boundaries and generic error conversion identified. |
| Presence-only check for all required guarded test variables | BLOCKED — all nine required variables were absent in this Codex process; no values were read or displayed. |
| `uv run --no-sync ruff check app/admin_user_lifecycle.py app/initial_admin_bootstrap.py scripts/bootstrap_admin.py tests/test_bootstrap_admin.py tests/test_initial_admin_bootstrap.py tests/test_initial_admin_bootstrap_integration.py tests/test_render_free_deployment_configuration.py ../docker/backend/bootstrap_initial_admin_from_environment.py ../docker/backend/start_api_free.py` | PASS — `All checks passed!` |
| `python -m py_compile` for the modified bootstrap and focused test modules | PASS — completed successfully with no output. |
| Focused pytest | NOT RUN — the global fail-closed guard cannot initialize without the existing isolated-test configuration and credentials. |
| `git diff --check` before creating this report | PASS — no whitespace errors; only pre-existing line-ending warnings were emitted. |

## Security and Isolation Checks

- The database safety guard was not modified or bypassed.
- No database connection, migration, cleanup, reset, Docker lifecycle action, cloud operation, Git commit, or push occurred.
- Production failure handling remains generic and fail-closed.
- The diagnostic callback is test-scoped by usage and transmits only safe fixed strings.
- No password, token, URL, SQL parameter, exception message, hash, or personal data was displayed or added to source or test output.

## Blockers and Uncertainties

The documented isolated test environment and its test-only credentials are not available in this invoking process. Consequently, the new safe diagnostic assertions could not be executed here. The database's live schema, privileges, migration revision, trigger behavior, and server error category remain unverified locally.

No cost-bearing resource was created or changed. The work is local source and static validation only.

## Recommended Next Step

After the human operator restores the documented existing isolated-test session (without pasting any secret into chat), run from `backend`:

```powershell
uv run --no-sync pytest -q tests/test_initial_admin_bootstrap_integration.py tests/test_bootstrap_admin.py tests/test_initial_admin_bootstrap.py tests/test_auth_login_api.py tests/test_render_free_deployment_configuration.py
```

If either integration assertion fails again, its pytest assertion output will contain only the safe phase/category pair. Use that pair to make a targeted follow-up diagnosis; do not expose the underlying database exception text or alter the safety guard.

## Final GO / NO-GO

**GO for one guarded operator-side integration run to collect the safe diagnostic category.**

**NO-GO for a production fix** until that run establishes the failing phase and category with evidence.
