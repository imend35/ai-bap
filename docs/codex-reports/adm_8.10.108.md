# ADIM 8.10.108 — Bootstrap Error Handling Hardening

## Step name and objective

Resolve the two bootstrap error-handling findings from ADIM 8.10.107 without
weakening validation, password handling, advisory locking, database isolation,
or startup fail-closed behavior.

## Verified facts and changes

### Integrity-error classification

The users-table migration defines the unique email index as `ix_users_email`.
The bootstrap module now returns `EMAIL_EXISTS` only when PostgreSQL reports
both the unique-violation SQLSTATE (`23505`) and that exact index name through
the driver diagnostic metadata. All other `IntegrityError` cases roll back and
return the generic safe `FAILED` result.

This preserves the shared transaction-scoped advisory lock, existing email
protection, active-administrator no-op behavior, and no-overwrite semantics.
No schema or migration was changed.

### Unexpected startup exceptions

The Free bootstrap launcher now catches `Exception` at its process boundary.
It returns a nonzero result and prints only the existing generic failure text.
It does not catch `BaseException`, so interpreter-control exceptions such as
`KeyboardInterrupt` and `SystemExit` retain normal semantics. Existing expected
result handling remains unchanged: disabled, created, and active-admin-exists
outcomes return zero; email conflicts and failures prevent API startup.

## Files modified

- `backend/app/initial_admin_bootstrap.py`
- `backend/tests/test_bootstrap_admin.py`
- `backend/tests/test_initial_admin_bootstrap.py`
- `docker/backend/bootstrap_initial_admin_from_environment.py`
- `docs/codex-reports/adm_8.10.108.md`

## Regression coverage added or adjusted

- A known PostgreSQL email-index unique violation returns `EMAIL_EXISTS`.
- An unrelated PostgreSQL unique violation returns `FAILED` after rollback.
- An unexpected generic exception containing synthetic secret-like text produces
  a nonzero launcher result and the generic message only; the test asserts that
  the synthetic value is absent from both stdout and stderr.

## Commands executed and actual results

| Command | Result |
| --- | --- |
| `uv run --no-sync ruff check app/initial_admin_bootstrap.py tests/test_bootstrap_admin.py tests/test_initial_admin_bootstrap.py` | PASS — all checks passed. |
| `uv run --no-sync python -m py_compile ...` for the modified application, tests, and launcher | PASS. |
| `uv run --no-sync pytest -q --noconftest tests/test_bootstrap_admin.py tests/test_initial_admin_bootstrap.py` with process-local synthetic configuration | PASS — 38 passed in 1.57s. These unit tests use fake sessions and made no database connection. |
| `git diff --check` | PASS — no whitespace errors. Git reported only pre-existing LF-to-CRLF conversion warnings. |

The first local Ruff/syntax attempt was blocked by sandbox access to the shared
uv cache. It was rerun with approved cache access; Ruff passed. A first syntax
command contained an incorrect relative launcher path; the corrected command
passed.

## Isolated PostgreSQL integration tests

NOT RUN. The invoking process lacked all required fail-closed isolated-test
environment variables, including test-mode confirmation, the exact isolated
target tuple, test password confirmation, and JWT configuration. No credentials
were generated, retrieved, or guessed, and no database connection was made.

When a Human Product Owner has restored the documented isolated test environment,
the operator-side verification command is:

```powershell
Set-Location backend
uv run --no-sync pytest -q tests/test_initial_admin_bootstrap_integration.py tests/test_bootstrap_admin.py tests/test_initial_admin_bootstrap.py
```

The existing `tests/conftest.py` guard must remain enabled for that command.

## Security checks

- No API route, authorization rule, password hashing behavior, Render Blueprint,
  database schema, migration, or test safety guard was changed.
- No password, token, database URL, error detail, or personal data is emitted by
  the new launcher error boundary.
- The new integrity classifier reads only error metadata and does not expose it
  to production output.
- No Git staging, commit, push, deployment, provisioning, or database operation
  occurred.

## Issues and remaining tasks

The PostgreSQL behavior is covered by source-level regression tests but still
requires the guarded isolated integration run before release confidence is
complete. Render runtime log redaction, CORS setup, managed database behavior,
and public deployment remain outside this local task.

## Recommended next step and status

**Conditional GO** for a guarded isolated PostgreSQL integration verification
once its documented environment is available. **NO-GO** for public deployment
until that verification and a separately approved disposable Render runtime
smoke test are complete.
