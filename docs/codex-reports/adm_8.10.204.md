# ADIM 8.10.204 — Static Validation & Fail-Closed Safety Verification

## 1. Step Name and Objective

I performed limited static validation of the ADIM 8.10.203 disposable PostgreSQL guard and configuration. The protected populated `ai_bap_test` database was not contacted. The new disposable environment was not provisioned.

## 2. Human Product Owner Authorization

This work stayed within the authorization for syntax, Ruff check-only, one database-independent guard test module, PowerShell parser validation, local YAML parsing, read-only Git review, and this single report. No application/configuration source was edited. No PostgreSQL, SQL, Alembic, Docker daemon/resource, GitHub, cloud, or deployment operation was performed.

## 3. Baseline Git State

Read-only baseline observed:

- Branch: `docs/ci-pr-evidence`.
- HEAD: `f6fff10898fc9a7c3d56a303fba7f50a1b1715e2`.
- Index: empty.
- The report path did not exist before this step.
- Existing pending work was already present, including tracked changes in backend auth/config/tests, documentation, Render configuration, frontend package files, and `scripts/test-all.ps1`; untracked work included `compose.regression-test.yaml`, numerous earlier Codex reports, and frontend E2E files. These were preserved.

The historical branch and HEAD expectations matched at baseline.

## 4. Python Syntax Results

Using the existing backend virtual-environment interpreter with `-B`, I parsed the source text with Python `ast.parse`; modules were not imported for this check and no bytecode was written.

Command shape: `backend/.venv/Scripts/python.exe -B -c "... ast.parse(Path(path).read_text(...)) ..."`

| File | Result |
|---|---|
| `backend/app/test_database_safety.py` | PASS |
| `backend/tests/conftest.py` | PASS |
| `backend/tests/test_test_database_safety.py` | PASS |

Command exit code: `0`.

## 5. Ruff Check Results

Command from `backend/`:

```text
./.venv/Scripts/ruff.exe check --no-cache app/test_database_safety.py tests/conftest.py tests/test_test_database_safety.py
```

Exit code: `1`. Ruff reported four findings:

- `BLE001` broad `except Exception` in `app/test_database_safety.py` at lines 262 and 280.
- `BLE001` broad `except Exception` in `tests/conftest.py` at line 26.
- `I001` import ordering in `tests/test_test_database_safety.py` at line 3; Ruff noted it as fixable, but no automatic fix was run.

No lint changes were made. These are static quality findings, not evidence of a runtime failure.

## 6. Guard Unit Test Preflight

I inspected `backend/tests/test_test_database_safety.py` and `backend/tests/conftest.py` before execution. The selected test module imports pytest, SQLAlchemy URL parsing, and the pure guard module. It does not import `SessionLocal`, `app.database`, an engine, or database-backed fixtures. The repository pytest configuration declares no automatic third-party plugin list; invocation disabled plugin autoload and pytest's cache provider.

The conftest guard runs first, then loads `Settings` and validates the effective URL. It does not initialize an engine or connect. For this process only, I supplied synthetic target values and a syntactically valid URL for the exact proposed loopback tuple; no password was required by URL tuple validation. A synthetic JWT setting was supplied so Pydantic settings could initialize. `PYTHONDONTWRITEBYTECODE=1`, Python `-B`, and `-p no:cacheprovider` prevented Python bytecode and pytest cache artifacts. Target-conflicting inherited selectors/credentials were removed only in the command process.

No actual database connection was attempted. No real credential was supplied.

## 7. Guard Unit Test Execution Results

Exact invocation (from `backend/`; all settings were process-scoped synthetic validation values):

```text
PYTHONDONTWRITEBYTECODE=1
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
backend/.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider tests/test_test_database_safety.py
```

Result: **44 passed**, 0 failed, 0 skipped, in 0.07 seconds. Exit code: `0`. No PostgreSQL connection occurred. The environment values were not recorded in this report.

## 8. Fail-Closed Scenario Coverage

Static source and executed unit tests confirm exact allowlisted regular, legacy, and disposable tuples; exact disposable selector and acknowledgment; `AI_BAP_TEST_MODE=true`; password non-empty/match checks; host/port/database/user mismatch rejection; unknown selector rejection; mixed-target rejection; conflicting and malformed `DATABASE_URL` rejection; effective Settings URL comparison; and secret-free guard errors. Regular and legacy compatibility tests passed in the selected suite. `configure_pytest_test_database_environment()` has no fallback from an unknown selector (guard source lines 186–202).

Coverage caveat: the suite tests a false test-mode value, not a missing `AI_BAP_TEST_MODE` key, and tests an empty password value rather than deleting the password key. The implementation uses `.get()` and rejects both missing and wrong/empty cases, but those exact absent-key paths are not directly asserted. Thus negative behavior is statically supported, while those two specific test cases are not independently exercised.

## 9. PowerShell Parser Results

The PowerShell language parser parsed `scripts/test-all.ps1` without executing or dot-sourcing it. Parser errors: `0`; result PASS; command exit code `0`. No environment values were printed. The script was not invoked.

## 10. Compose YAML Validation Results

The local PyYAML parser loaded `compose.regression-test.yaml` in memory; no Docker command or daemon was used. YAML parse and static assertions passed (exit code `0`): Compose project name and `db` service, `postgres:16`, expected container/database, `127.0.0.1:55434:5432`, secret-file reference rather than a plaintext password, explicit healthcheck and `restart: "no"`, no service/top-level declared data volumes, no privileged/host-network setting, and `PGDATA=/var/lib/postgresql/regression-data`.

This is local YAML/static configuration evidence only. Compose's full schema validation and actual container behavior were not verified.

## 11. Compose Isolation and Volume Risk

`compose.regression-test.yaml` lines 1–19 define the distinct project/container, PostgreSQL 16, loopback port, secret-file reference, and non-default `PGDATA`. Lines 20–31 define healthcheck and external local secret-file path. The YAML itself has no named or bind volume declaration, and its configured `PGDATA` is outside the image's conventional data directory.

**Important unresolved risk:** the official `postgres:16` image may declare a Docker `VOLUME` at its default data path. If so, Docker can create an anonymous volume from image metadata even though Compose declares no volume; moving `PGDATA` may leave that volume unused, but it does not prove that no anonymous mount is created. This cannot be verified without inspecting the image/container, which was prohibited. Therefore actual no-volume runtime behavior is **NOT VERIFIED**. Do not provision until the image metadata/runtime mount behavior is confirmed and the Compose design is adjusted or explicitly accepted under separate authorization.

The proposed resources remain unprovisioned; the proposed port's availability was not checked.

## 12. Guard Import-Order and URL Safety

`backend/tests/conftest.py` lines 5–22 selects/validates the test tuple before importing settings and validates the effective `Settings.database_url` before test modules can import database code. `backend/app/config.py` supports `DATABASE_URL` precedence; the conftest-level validation covers the Settings result (including dotenv settings) before engine use. `backend/scripts/run_isolated_test_alembic.py` validates the selected target and effective URL before importing Alembic (lines 8–23). No production Settings default was changed by the inspected ADIM 203 diff.

Static ordering is fail-closed for pytest and the guarded Alembic wrapper. This does not prevent someone from bypassing the wrapper and invoking Alembic directly; operational use must remain restricted to the documented wrapper. Runtime import behavior beyond the selected guard test is not separately verified here.

## 13. Git Diff Review

Reviewed the requested diffs for `backend/app/test_database_safety.py`, `backend/tests/conftest.py`, `backend/tests/test_test_database_safety.py`, `scripts/test-all.ps1`, and `docs/isolated-test-database.md`; read the untracked Compose YAML directly. `git diff --check` exited `0` and reported no whitespace errors. Git emitted line-ending conversion warnings (“LF will be replaced by CRLF”) for existing modified files; these are warnings, not whitespace errors, and no line endings were normalized.

The diff review confirmed the new allowlisted target is local-only and its guard does not modify production defaults. It also exposed the Ruff findings above and the Compose image-volume uncertainty. No file was changed as part of validation.

## 14. Acceptance Criteria Matrix

| Criterion | Status | Evidence / limitation |
|---|---|---|
| AC-01 Python syntax valid | PASS | Three requested files AST-parsed; exit 0. |
| AC-02 Ruff check-only passes | FAIL | Four findings; exit 1. |
| AC-03 Selected DB-independent guard tests pass | PASS | 44 passed; exit 0. |
| AC-04 No PostgreSQL connection occurs | PASS | Imports and test behavior reviewed; no DB/engine module; no DB command. |
| AC-05 No real database credentials required | PASS | Only synthetic process-local values; none recorded. |
| AC-06 Fail-closed negative cases verified | PARTIAL | Tested/implemented mismatch paths; missing mode-key and missing password-key cases not directly tested. |
| AC-07 Regular target behavior preserved | PASS | Regular compatibility tests passed. |
| AC-08 Legacy target behavior preserved | PASS | Legacy compatibility tests passed. |
| AC-09 No silent disposable-to-regular fallback | PASS | Selector dispatch raises on unknown selector; valid disposable selection is explicit. |
| AC-10 Effective `DATABASE_URL` protection verified | PASS | Conflicting/malformed and Settings mismatch tests passed; pytest conftest validates Settings before DB imports. |
| AC-11 PowerShell parser passes | PASS | Parser errors 0; script not executed. |
| AC-12 Compose YAML parser passes | PASS | PyYAML parse and static assertion script exit 0. |
| AC-13 Compose isolation statically verified | PARTIAL | YAML settings isolate target; actual image-declared anonymous volume behavior is not verified. |
| AC-14 No Docker daemon/resource operations | PASS | None performed. |
| AC-15 No migrations or DB-backed tests | PASS | Only guard unit module run; no SQL/Alembic/database test. |
| AC-16 No application/configuration source changes | PASS | No source was edited during this step. |
| AC-17 No unauthorized files created | PASS | Only this authorized report was created. |
| AC-18 No Git/GitHub/cloud mutation | PASS | No Git mutation, GitHub, or cloud action. |
| AC-19 Existing 50-record DB preserved | PASS (not contacted) | No connection or Docker operation; preservation follows from no access, not a fresh row-count query. |
| AC-20 Exactly one Markdown report created | PASS | `docs/codex-reports/adm_8.10.204.md`. |

## 15. Residual Risks and Blockers

1. **Ruff failure:** three `BLE001` findings and one import-order finding remain; no fixes were authorized.
2. **Missing-key test coverage:** missing test-mode and missing password variables are rejected by implementation logic but not tested as absent keys in this test module.
3. **Anonymous volume behavior:** YAML does not declare a volume, but Docker image metadata/runtime mounts were intentionally not inspected. No-volume behavior is not established.
4. **No runtime Compose schema/engine validation:** no Docker command was run and the disposable target is not provisioned.
5. **No database regression evidence:** database-backed tests, migrations, and actual identity checks remain unperformed.

## 16. Git and Resource Preservation

Final read-only checks confirmed branch `docs/ci-pr-evidence`, HEAD `f6fff10898fc9a7c3d56a303fba7f50a1b1715e2`, and an empty index. Existing modified and untracked work remained present; the only new path is this report. No database or Docker resource was contacted or changed. No SQL, migration, GitHub, cloud, deployment, or paid-service operation occurred.

## 17. Recommended SINGLE Next Step

Obtain a narrowly scoped follow-up authorization to address the four Ruff findings, add explicit absent-key guard tests, and resolve the PostgreSQL image anonymous-volume design before any Compose provisioning or database-backed test execution.
