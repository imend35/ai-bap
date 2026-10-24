# ADIM 8.10.134 — Secure Migration Error Handling

## Objective and security finding


This step hardens the deployment migration entrypoint so configuration, database-driver, advisory-lock, Alembic, and unexpected runtime failures do not relay exception details to application-controlled stdout or stderr.

The risk recorded in ADIM 8.10.130 was that `docker/backend/migrate_production.py` constructed a usable managed-database connection string and invoked Alembic with inherited output streams. An Alembic or database exception could therefore reach platform logs with sensitive configuration metadata.

## Initial repository state

- Branch: `docs/ci-pr-evidence`.
- Initial `HEAD`: `f66d4a33dc35ba0f1cea486c7eb6f0d838aeeb84`.
- Git index: empty.
- Existing modified and untracked Codex reports, including `adm_8.10.76.md` and ADIM 8.10.102–8.10.132 reports, were present before this task and were preserved.
- No Docker operation, database connection, migration execution, provisioning, deployment, staging, commit, push, merge, or GitHub configuration change was performed.

## Root-cause analysis

Before this change, `migrate_production.py`:

1. rendered the connection URL for Psycopg;
2. acquired the PostgreSQL advisory lock; and
3. invoked `subprocess.run(["alembic", "upgrade", "head"], check=True)` with inherited standard streams.

There was no outer exception boundary. Therefore configuration errors, Psycopg exceptions, advisory-lock failures, `CalledProcessError` details, and unexpected exceptions could terminate the script with interpreter output. In particular, Alembic output was not captured before being inherited by the deployment log stream.

## Exact files changed

- Modified `docker/backend/migrate_production.py`.
- Added `backend/tests/test_migrate_production.py`.
- Modified `backend/tests/test_render_free_deployment_configuration.py`.
- Added this report: `docs/codex-reports/adm_8.10.134.md`.

## Implementation details

`migrate_production.py` now:

- wraps settings resolution, database connection, advisory locking, Alembic execution, and unlock processing in one fail-closed `Exception` boundary;
- captures Alembic stdout and stderr using `capture_output=True` instead of inheriting those streams;
- returns `1` on every handled failure and emits only the fixed stderr message: `Database migration failed; the API will not start.`;
- emits a fixed success line only after both Alembic and advisory unlock complete successfully;
- retains the same advisory-lock key, `alembic upgrade head` command, unlock-in-`finally` semantics, and successful `0` exit code.

The narrow `BLE001` exemption is intentional and documented inline: this is the top-level deployment error boundary and must handle unexpected ordinary exceptions fail-closed. It does not catch `BaseException`, so interpreter termination and process signals retain their normal behavior.

## Error and output redaction boundaries

The focused tests inject a synthetic secret-like marker into each failure source and assert that it, a database URL prefix, and traceback text are absent from captured stdout and stderr.

Covered failure sources are:

- invalid configuration while resolving settings;
- database connection failure;
- advisory-lock acquisition failure;
- Alembic `CalledProcessError` with synthetic stdout/stderr details; and
- an unexpected runtime exception during migration execution.

The existing Free startup-wrapper behavior remains fail-closed: a nonzero migration child result prevents API startup. Additional coverage confirms that the wrapper does not relay `CalledProcessError` output fields when reporting the failed migration.

## Validation and test results

| Command or check | Actual result |
| --- | --- |
| Read-only inspection of `AGENTS.md`, migration script, API/Free startup callers, deployment tests, Alembic configuration, and test guard | PASS |
| `uv run --no-sync pytest -q tests/test_migrate_production.py tests/test_render_free_deployment_configuration.py` | NOT RUN: pytest collection stopped before tests because the current process lacks every required guarded isolated-test environment variable, including the test-only password. The guard was not bypassed and no database connection was attempted. |
| Presence-only check of required guarded test variables | BLOCKED: all required variables were absent; no values were printed. |
| `uv run --no-sync ruff check tests/test_migrate_production.py tests/test_render_free_deployment_configuration.py ../docker/backend/migrate_production.py ../docker/backend/start_api_free.py` | PASS — `All checks passed!` |
| `uv run --no-sync python -m py_compile ../docker/backend/migrate_production.py tests/test_migrate_production.py tests/test_render_free_deployment_configuration.py` | PASS |
| `git diff --check` | PASS; Git emitted only LF-to-CRLF working-copy warnings for modified pre-existing text files. |

The first local `uv` invocation was blocked by sandbox access to the existing local `uv` cache. The same non-destructive commands were retried with approved cache access. The subsequent pytest attempt reached the repository's fail-closed test guard and was blocked before executing tests.

## Remaining limitations and risks

- The new unit tests are present but were not executable in this Codex process because the repository applies its integration-test guard during pytest collection. The documented operator-side command, after setting the verified isolated-test environment in the same shell, is:

  ```powershell
  cd backend
  uv run --no-sync pytest -q tests/test_migrate_production.py tests/test_render_free_deployment_configuration.py
  ```

- This boundary controls normal Python execution inside `main()` and Alembic subprocess streams. It cannot suppress output emitted before the script imports or starts, process-signal termination, or unrelated platform/container runtime logs. No such leak was demonstrated here.
- Public deployment remains blocked by the outstanding CORS and temporary-bootstrap-secret operator verification requirements recorded in ADIM 8.10.132. No Render resource has been inspected or created.

## Working-tree preservation

Only the migration script, focused migration/security tests, the Free-wrapper test, and this new report were changed by this task. All pre-existing modified and untracked files remain unstaged and untouched.

## Recommended single next action

Use the documented, already verified isolated PostgreSQL environment in an operator-controlled shell to execute the focused pytest command above. Record the actual result before authorizing a scoped review or commit.

## GO / NO-GO

- **GO (conditional):** for a separately authorized operator-side guarded test run and subsequent scoped review if it passes.
- **NO-GO:** for public Render deployment. No platform resource, CORS configuration, managed-database migration, or bootstrap-secret lifecycle has been verified in a public environment.
