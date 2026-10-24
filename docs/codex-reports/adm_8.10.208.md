# ADIM 8.10.208 — Disposable PostgreSQL Port Configuration Update

## 1. Step Name and Objective

I changed the allowlisted disposable-regression PostgreSQL host port from `55434` to `55435`, retained internal port `5432`, and verified the guard rejects the prior port. No environment was provisioned.

## 2. Human Product Owner Authorization

Work was limited to the authorized disposable-port implementation, tests, documentation, runner, and this report. The regular, legacy, rubric, and production targets were not changed. No database, SQL, migration, Docker daemon/resource, secret, Git/GitHub, cloud, or deployment operation occurred.

## 3. Baseline Git State

Read-only baseline before edits:

- Branch: `docs/ci-pr-evidence`.
- HEAD: `f6fff10898fc9a7c3d56a303fba7f50a1b1715e2`.
- Index: empty.
- Report path was absent.
- Numerous pending tracked modifications and untracked reports/E2E files were present and preserved.

## 4. Port Reference Discovery

Search command (historical reports, Git internals, virtual environments, dependencies, caches, and generated build directories excluded):

```text
rg -n '55434|55435|disposable-regression|ai-bap-regression-disposable-20261024-a202|ai_bap_regression_20261024' --glob '!docs/codex-reports/**' --glob '!**/.venv/**' --glob '!**/node_modules/**' --glob '!**/__pycache__/**' --glob '!**/.pytest_cache/**' --glob '!**/dist/**' --glob '!**/build/**' --glob '!.git/**' .
```

Active matches were classified as:

- **Active disposable configuration:** `compose.regression-test.yaml` host mapping.
- **Guard implementation:** `backend/app/test_database_safety.py` disposable tuple.
- **Guard tests:** `backend/tests/test_test_database_safety.py` accepted tuple/URL and new negative old-port case.
- **Runner:** `scripts/test-all.ps1` disposable-only `POSTGRES_PORT` value.
- **Documentation:** `docs/isolated-test-database.md` disposable endpoint and host preflight.
- **Historical evidence:** excluded from the active-source search and left unchanged.
- **Unrelated target references:** regular `55432`, legacy `55433`, rubric `55434`, and production-like `5433` remain unchanged. The documentation intentionally names `55434` as the port occupied by `ai-bap-rubric-test-db-1`; the new negative test intentionally uses `55434` to prove rejection.

`backend/tests/conftest.py` and `backend/scripts/run_isolated_test_alembic.py` contain no disposable port literal and were not changed. Exact files changed for this step: the four active references above plus `docs/isolated-test-database.md`; this report is the only new file.

## 5. Files Changed

- `compose.regression-test.yaml`
- `backend/app/test_database_safety.py`
- `backend/tests/test_test_database_safety.py`
- `scripts/test-all.ps1`
- `docs/isolated-test-database.md`
- `docs/codex-reports/adm_8.10.208.md`

No other path was intentionally changed. Earlier local changes in these files remain in the working tree; their cumulative diffs include earlier authorized work.

## 6. Compose Port Update

`compose.regression-test.yaml:19` now maps `127.0.0.1:55435:5432`. Project/service/container identity, `postgres:16`, database, secret-file reference, healthcheck, restart policy, `PGDATA`, and volume configuration were retained. No new volume or mount was introduced.

## 7. Guard Allowlist Update

`backend/app/test_database_safety.py:27` now sets the disposable tuple's `POSTGRES_PORT` to `55435`. The regular target remains `55432`; the legacy target remains `55433`. The target selector, effective `DATABASE_URL` validation, and fail-closed behavior were not otherwise changed. No production default changed.

## 8. Guard Unit Test Update

`backend/tests/test_test_database_safety.py:212` asserts the valid disposable port is `55435`; the accepted disposable URL fixture at approximately line 355 also uses `55435`. Added `test_disposable_guard_rejects_previous_rubric_test_port` (approximately lines 257–263), which supplies `55434` in the in-memory disposable target and expects `IntegrationDatabaseSafetyError`. Test values are synthetic; no DB connection is used.

## 9. Supporting File Review

`backend/tests/conftest.py` and `backend/scripts/run_isolated_test_alembic.py` were inspected and have no host-port literal to update. `scripts/test-all.ps1:46` now expects `55435` only in the explicit `disposable-regression` branch. The regular branch at lines 59–63 continues to require `55432`. The script was parsed only; it was not run.

## 10. Documentation Update

`docs/isolated-test-database.md:64–72` now documents `127.0.0.1:55435`, explains that `55434` belongs to `ai-bap-rubric-test-db-1`, and states that `55435` is not reserved and its availability is not verified by this change. The provisioning preflight at approximately line 134 now rechecks `55435`. The anonymous-volume warning remains: local image metadata had previously been supplied as declaring `/var/lib/postgresql/data`, while `PGDATA` is `/var/lib/postgresql/regression-data`; runtime mounts remain **NOT VERIFIED** and cleanup remains separately approval-gated.

## 11. Python Syntax Results

Command: existing backend Python interpreter using `-B` and in-memory `ast.parse` for the guard, conftest, and guard test source text.

```text
backend/.venv/Scripts/python.exe -B -c "import ast,pathlib; ps=['backend/app/test_database_safety.py','backend/tests/conftest.py','backend/tests/test_test_database_safety.py']; [ast.parse(pathlib.Path(p).read_text(encoding='utf-8'),filename=p) for p in ps]; print('AST_PASS: all 3 files')"
```

All three files parsed; exit code `0`.

## 12. Ruff Check Results

From `backend/`:

```text
./.venv/Scripts/ruff.exe check --no-cache app/test_database_safety.py tests/conftest.py tests/test_test_database_safety.py
```

Output: `All checks passed!`; exit code `0`.

## 13. Guard Unit Test Results

Preflight confirmed the selected module exercises in-memory guard/URL logic and imports no engine/session fixture; conftest validates settings without initializing a DB connection. The process used synthetic disposable-target values, `PYTHONDONTWRITEBYTECODE=1`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, Python `-B`, and no pytest cache.

Exact pytest command from `backend/`:

```text
backend/.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider tests/test_test_database_safety.py
```

Result: **47 passed, 0 failed, 0 skipped**, in 0.11 seconds; exit code `0`. The new test explicitly verifies old port `55434` rejection, while accepted disposable configuration and URL checks use `55435`. No PostgreSQL connection or SQL occurred.

## 14. YAML Validation

PyYAML `safe_load` parsed `compose.regression-test.yaml` in memory. Static assertions passed (exit code `0`): exact project/service/container, image, new mapping `127.0.0.1:55435:5432`, absence of the old mapping `127.0.0.1:55434:5432`, expected database/secret-file reference, no plaintext password, no declared data volumes, no protected-volume reference, no privileged or host-network mode, healthcheck, restart policy, and unchanged `PGDATA`.

No Docker Compose command or daemon/resource operation was used. Actual runtime mounts remain unverified.

## 15. PowerShell Parser Validation

Used `[System.Management.Automation.Language.Parser]::ParseFile(...)` on `scripts/test-all.ps1` without executing or dot-sourcing it. Parse errors: `0`; exit code `0`.

## 16. Security Regression Review

- Disposable target selection remains explicit and exact port `55435` is allowlisted.
- The dedicated negative test proves `55434` is rejected for the disposable target.
- Regular (`55432`) and legacy (`55433`) targets remain unchanged; the rubric configuration/container was not edited.
- No fallback behavior, URL validation, effective Settings validation, or production default was changed.
- No secrets were read or logged. No database connection, SQL, Docker resource operation, migration, or test runner script execution occurred.
- Port `55435` availability was not checked in this step and is not reserved. A host-side check is required immediately before future provisioning.
- The supplied `postgres:16` image metadata says it declares `/var/lib/postgresql/data`; custom `PGDATA` does not establish absence of an anonymous volume. Actual disposable container mounts remain **NOT VERIFIED** because it is unprovisioned.

## 17. Acceptance Criteria Matrix

| Criterion | Status | Evidence |
|---|---|---|
| AC-01 Only authorized files changed | PASS | Five authorized implementation/documentation paths updated; report separately authorized. |
| AC-02 Exactly one report created | PASS | This report only; absent at baseline. |
| AC-03 Active disposable refs use 55435 | PASS | Compose, guard, test, runner, and setup guide updated; negative rejection case deliberately retains 55434. |
| AC-04 Historical reports preserved | PASS | Not edited. |
| AC-05 Rubric port 55434 unchanged | PASS | No rubric configuration changed; documentation identifies its existing container. |
| AC-06 Regular port 55432 unchanged | PASS | Guard and runner regular target unchanged; tests passed. |
| AC-07 Legacy port 55433 unchanged | PASS | Guard legacy tuple unchanged; tests passed. |
| AC-08 Compose mapping correct | PASS | YAML assertion confirms `127.0.0.1:55435:5432`. |
| AC-09 Guard accepts disposable 55435 | PASS | Valid target test and suite pass. |
| AC-10 Guard rejects disposable 55434 | PASS | Dedicated negative test included in passing suite. |
| AC-11 Guard unit tests pass | PASS | 47 passed, exit 0. |
| AC-12 Ruff check-only passes | PASS | Exit 0. |
| AC-13 Python syntax passes | PASS | Three AST parses, exit 0. |
| AC-14 YAML parser passes | PASS | In-memory PyYAML/static checks, exit 0. |
| AC-15 PowerShell parser passes | PASS | Zero parse errors, exit 0. |
| AC-16 No DB connection or SQL | PASS | None occurred. |
| AC-17 No Docker daemon/resource operation | PASS | None occurred. |
| AC-18 No migration or DB-backed tests | PASS | Only pure guard tests ran. |
| AC-19 No credential exposure | PASS | No credentials accessed or recorded. |
| AC-20 No Git/GitHub/cloud mutation | PASS | Read-only Git inspections only. |
| AC-21 Existing protected database preserved | PASS (not contacted) | No database/volume access. |
| AC-22 Anonymous-volume risk documented | PASS (runtime unverified) | Documentation retains risk and exact mount inspection requirement. |
| AC-23 Provisioning decision remains unauthorized | PASS | No provisioning performed or authorized by this step. |

## 18. Residual Risks and Blockers

1. `55435` is not reserved and its current availability is unverified; recheck before provisioning.
2. Runtime anonymous-volume/mount behavior remains **NOT VERIFIED**; inspect exact image/container metadata and mounts in a separately authorized host step.
3. The disposable database remains unprovisioned; database identity, health, and runtime-role setup are not verified.
4. Historical reports intentionally retain the prior port as historical evidence and were not rewritten.

## 19. Git and Resource Preservation

Final read-only checks confirmed branch `docs/ci-pr-evidence`, HEAD `f6fff10898fc9a7c3d56a303fba7f50a1b1715e2`, and an empty index. Existing pending work was preserved. Only the authorized five implementation/documentation files were changed for this step, and this report was the only new file. `git diff --check` exited `0` (Git also printed existing LF-to-CRLF working-copy warnings). No PostgreSQL/Docker/GitHub/cloud/deployment operation occurred.

## 20. Recommended SINGLE Next Step

Request separate authorization for a host-side read-only preflight that rechecks port `55435` and verifies the exact disposable project/container/image metadata and mounts, including any anonymous volume, before any provisioning decision.
