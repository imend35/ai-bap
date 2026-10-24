# ADIM 8.10.203 — Implement Minimal Fail-Closed Disposable Test Guard & Compose Configuration

## 1. Step Name and Objective

Implement test-only support for the explicitly named disposable PostgreSQL regression target while preserving the regular and legacy allowlists. Add a separate Compose definition and host workflow documentation. No database or Docker resources were provisioned.

## 2. Human Product Owner Authorization

The implementation followed the limited authorization for six named implementation files plus this report. No tests, Ruff, database connections/SQL, Alembic, Docker/Compose, credentials, Git/GitHub, cloud, or deployment operation was run. Existing production defaults and unrelated working-tree changes were out of scope and preserved.

## 3. Baseline Git State

Before edits, read-only inspection recorded:

- Branch: `docs/ci-pr-evidence`.
- HEAD: `f6fff10898fc9a7c3d56a303fba7f50a1b1715e2`.
- Index: empty.
- `docs/codex-reports/adm_8.10.203.md` did not exist.
- `compose.regression-test.yaml` did not exist.
- `backend/tests/conftest.py` already had an unstaged ADIM 8.10.197 modification enabling registration within the test process. That behavior was retained and reordered only so effective settings validation sees the same test setting.
- Other pre-existing modified/untracked paths were inventoried by Git status and not edited by this step.

## 4. Files Changed

Six authorized implementation paths were changed/created, plus exactly this report:

1. `backend/app/test_database_safety.py` — central exact target allowlist, selector dispatch, URL validation.
2. `backend/tests/conftest.py` — target selection and effective Settings validation before test modules can initialize/use an engine; existing test-only registration opt-in retained.
3. `backend/tests/test_test_database_safety.py` — in-memory guard and effective URL cases added/updated.
4. `scripts/test-all.ps1` — explicit `-Target isolated-test|disposable-regression` preflight selection.
5. `compose.regression-test.yaml` — new isolated PostgreSQL 16 definition with secret-file input and no data volume.
6. `docs/isolated-test-database.md` — protected database invariant and future disposable workflow.
7. `docs/codex-reports/adm_8.10.203.md` — this execution report.

No additional path was intentionally changed. Pre-existing edits to other files remain outside this step.

## 5. Disposable Target Implementation

`backend/app/test_database_safety.py` now adds the exact named target `disposable-regression` with host `127.0.0.1`, port `55434`, database `ai_bap_regression_20261024`, and runtime role `ai_bap_regression_user_20261024`. It requires `AI_BAP_TEST_MODE=true`, `AI_BAP_TEST_TARGET=disposable-regression`, the exact non-secret acknowledgment `disposable-regression-postgresql-acknowledged`, a non-empty `AI_BAP_DISPOSABLE_TEST_POSTGRES_PASSWORD`, and equality with `POSTGRES_PASSWORD`.

The default regular target remains `isolated-test` when the selector is absent, and the legacy migration target remains explicitly selected through its existing Alembic selector and separate confirmation. All three targets remain exact allowlist tuples. Partial, unknown, cross-target secret/confirmation, and mixed pytest/Alembic selectors raise generic safety errors; no arbitrary host/database target is accepted. Password values are not included in errors.

## 6. Fail-Closed Guard Behavior

The central validator rejects missing test-mode opt-in, missing/wrong confirmation, missing/mismatched password, non-loopback or wrong host, wrong port/database/user, unknown selector, and incompatible target-selector combinations. The disposable selector does not fall back to regular `ai_bap_test`. The existing regular and legacy confirmation strings and tuples remain intact.

`configure_pytest_test_database_environment()` dispatches only to the selected allowlisted tuple. `configure_guarded_alembic_database_environment()` also recognizes the disposable target only when both target selectors agree. The existing specialized legacy migration tools were not broadened to accept the new target.

## 7. Effective DATABASE_URL Validation

`validate_effective_test_database_target()` parses and checks SQLAlchemy URL backend, host, port, database, and username against the selected target, without opening a connection. Malformed or mismatching URLs produce secret-free errors. If process `DATABASE_URL` is present, the central guard validates it; pytest then also instantiates effective application settings and validates the resulting URL, which accounts for a `.env`-derived override. This occurs before test modules import database engine/session modules. The existing Alembic wrapper already validates effective Settings before invoking Alembic; the central target dispatcher now supports the new explicit target without changing production Settings defaults.

The PowerShell runner rejects a process `DATABASE_URL`; pytest’s direct startup path permits only a URL whose effective target tuple matches the selected allowlist. No connection is initialized by these validations. Runtime behavior, including behavior with the actual local `.env`, remains unverified because execution was prohibited.

## 8. Pytest Startup Guard

`backend/tests/conftest.py` now selects the target, preserves test-only `PUBLIC_REGISTRATION_ENABLED=true`, clears the Settings cache, and validates effective Settings before test modules can use `SessionLocal` or an engine. Unknown or mixed selectors stop import with a generic safety exception. The guard imports configuration only; it does not create a database connection.

## 9. Guard Unit Tests Added

`backend/tests/test_test_database_safety.py` now statically defines cases for a complete disposable tuple; missing mode, confirmation, or password; wrong confirmation/password/host/port/database/role; unknown and mixed targets; conflicting and malformed `DATABASE_URL`; effective Settings URL mismatch; secret-free diagnostics; and exact effective disposable URL matching. Existing regular and legacy target cases remain. These are test definitions only: **they were not executed**.

## 10. PowerShell Runner Changes

`scripts/test-all.ps1` retains the regular target as its default and accepts an explicit validated target parameter. The disposable branch requires the exact selector, confirmation, endpoint tuple, dedicated runtime secret variable, and matching `POSTGRES_PASSWORD`; conflicts fail closed. No password is printed. The script does not provision Docker resources, run migrations, or clean up resources. The runner itself was not executed.

## 11. Docker Compose Configuration

`compose.regression-test.yaml` declares PostgreSQL 16 under project `ai-bap-regression-disposable-20261024-a202`, service `db`, and expected container `ai-bap-regression-disposable-20261024-a202-db-1`. It publishes only `127.0.0.1:55434:5432`, sets the required database, uses `POSTGRES_PASSWORD_FILE` backed by a separately supplied host secret file, includes a health check, and sets restart policy to `no`. It has no named or bind-mounted data volume and sets `PGDATA` to `/var/lib/postgresql/regression-data`, outside the official image's default data-volume path, so the intended data lifecycle is the container writable layer. It has no privileged mode, host networking, public binding, hard-coded password, or reference to existing Compose resources.

The Compose initialization identity is a distinct bootstrap superuser. The non-superuser runtime role required by the guard must be created in a separately approved interactive bootstrap, with ownership/privileges restricted to this database. No SQL/bootstrap script or secret file was created. The data is in the container writable layer and is lost if that exact container is removed; removal itself remains separately approval-gated.

## 12. Documentation Changes

`docs/isolated-test-database.md` now states that the existing populated `ai_bap_test` database and persistent volume are protected and its exposed password must not be reused. It documents the proposed resources, exact selector/tuple/acknowledgment, process-only runtime secret, bootstrap/runtime role split, `DATABASE_URL` precedence protection, no-volume lifecycle, preflight, guarded migration path, test phases, persistent audit rows, explicit cleanup authorization, and separate credential-rotation task. It does not claim the new service exists or has been tested.

## 13. Static Review Results

- Static source review confirms the new target tuple and acknowledgment match the proposed values.
- Existing regular and legacy target constants and separate legacy selector remain present.
- URL validation checks the effective SQLAlchemy target before pytest or guarded Alembic execution; no connection is opened by the validation functions.
- The Compose file contains no database data mount and binds only to loopback; password input is a secret-file path, not a password value.
- The existing production settings file was not changed by this step; no production defaults were altered.
- `git diff --check` produced no whitespace-error output. Git emitted a working-copy LF/CRLF conversion warning for the already-modified `backend/tests/conftest.py`; line endings were not normalized.
- No YAML parser, PowerShell parser, pytest, Ruff, Alembic, PostgreSQL client, Docker, or Compose command was run. Therefore syntax/runtime correctness and test outcomes are **NOT VERIFIED**.

## 14. Acceptance Criteria Matrix

| Criterion | Status | Evidence |
|---|---|---|
| AC-01 Only six authorized implementation files changed | PASS | Six authorized paths listed above; report is the separately authorized seventh path. |
| AC-02 Exactly one report created | PASS | This report only; target was absent at baseline. |
| AC-03 Existing regular target preserved | PASS | Original regular tuple/confirmation remain in central allowlist. |
| AC-04 Existing legacy target preserved | PASS | Original legacy tuple/selector/confirmation remain. |
| AC-05 Disposable target allowlisted | PASS | Exact tuple and explicit selector added. |
| AC-06 Exact confirmation required | PASS | Exact dedicated acknowledgment is validated. |
| AC-07 Unique runtime secret required | PASS | Dedicated non-empty variable must equal `POSTGRES_PASSWORD`; no value logged. |
| AC-08 DATABASE_URL mismatch rejected | PASS | Process URL and effective Settings URL are checked before engine use. |
| AC-09 Pytest startup guard fail-closed | PASS | Target dispatch and effective Settings check happen in conftest before test-module imports. |
| AC-10 Guard unit tests added | PASS | In-memory tests cover required cases; execution is not claimed. |
| AC-11 PowerShell selection added | PASS | Explicit validated target parameter and matching environment checks added. |
| AC-12 Separate Compose definition added | PASS | New authorized YAML path created. |
| AC-13 No PostgreSQL data volume configured | PASS | Compose definition has no volume mount. |
| AC-14 Loopback-only port configured | PASS | Mapping is `127.0.0.1:55434:5432`. |
| AC-15 Documentation updated | PASS | Protected target and future workflow documented. |
| AC-16 No tests executed | PASS | No test command run. |
| AC-17 No PostgreSQL connection or SQL | PASS | None performed. |
| AC-18 No Docker resource operation | PASS | No Docker/Compose command run. |
| AC-19 No production-default modification | PASS | Production configuration was not edited by this step. |
| AC-20 No Git/GitHub/cloud mutation | PASS | Read-only Git inspection only; index remains empty. |

Static implementation criteria are marked PASS where source content was inspected. Runtime correctness, actual Compose parsing, target availability, and test behavior remain NOT VERIFIED.

## 15. Residual Risks and Blockers

- The target is not provisioned; port/name availability, container health, and database identity remain unverified.
- Compose starts with a bootstrap superuser. A separately approved manual role/database ownership bootstrap is required before tests; no SQL helper was added.
- The bootstrap secret file must be securely created outside the repository by the authorized host operator. No secret was generated.
- The test guard only checks configured/effective URL before connection. The future host-side identity preflight must verify actual server/database/user before DDL and tests.
- The fixed target tuple is intentionally run-specific; future reuse needs a separately reviewed allowlist update rather than arbitrary overrides.
- PowerShell, Compose/YAML, conftest import order, dotenv override, and unit-test behavior were not executed or parsed; runtime correctness is not established.
- The existing `ai_bap_test` password remains compromised until its separate rotation is approved and completed. The existing 50 records and volume were not accessed.

## 16. Git and Resource Preservation

Final read-only checks observed branch `docs/ci-pr-evidence`, HEAD `f6fff10898fc9a7c3d56a303fba7f50a1b1715e2`, and an empty index. The six authorized implementation paths plus this report are the only paths changed/created by this step. All pre-existing unrelated modifications and untracked files remain present. No tests, database/SQL, Docker, Git/GitHub, cloud, or deployment operation occurred. The existing container, volume, and database were not contacted or modified.

## 17. Recommended SINGLE Next Step

Request a separate Human Product Owner approval for a host-side preflight and provisioning of this exact disposable Compose target, including protected bootstrap-secret delivery and an interactive least-privileged runtime-role bootstrap. Do not migrate or run tests until that preflight proves the new target identity and the guard implementation receives runtime validation.
