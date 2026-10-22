# ADIM 8.10.12 — Minimal OpenAPI Contract Alignment

## 1. Step name and objective

**Step:** ADIM 8.10.12 — Minimal OpenAPI Contract Alignment

**Objective:** Correct the two verified OpenAPI contract-alignment failures without changing API routes, request or response payload behavior, authorization, business logic, database state, or dependencies.

## 2. Summary of work completed

I made two metadata-only alignments:

- Renamed the checked-in Task response component to `TaskResponse` and updated all direct Task response references. This matches the runtime component generated from the existing Pydantic `TaskResponse` class.
- Added explicit FastAPI operation IDs `archiveProject` and `restoreProject` to the existing archive and restore route decorators. These now match the stable operation IDs already declared in `openapi.yaml`.

The existing focused contract test was updated only where it asserted the old Task component name. No endpoint behavior changed.

## 3. Files modified

- `openapi.yaml`
  - Changed Task create, get, update, and paginated-list response references from `Task` to `TaskResponse`.
  - Renamed the `Task` component to `TaskResponse` without changing its schema structure.
- `backend/app/routers/projects.py`
  - Added `operation_id="archiveProject"` to the archive route.
  - Added `operation_id="restoreProject"` to the restore route.
- `backend/tests/test_openapi_contract_alignment.py`
  - Updated direct Task response component assertions from `Task` to `TaskResponse`.
- `docs/codex-reports/adm_8.10.12.md`
  - Added this report.

## 4. Verification performed

Read-only reference inspection confirmed:

- No remaining direct `#/components/schemas/Task` references or `Task` component declaration remain in the affected contract/test files.
- All affected Task response references now target `#/components/schemas/TaskResponse`.
- Both project archive decorators now have the intended explicit operation IDs.

## 5. Commands executed and results

Read-only repository inspection commands were used to locate affected references, inspect the environment configuration state without exposing values, and review the resulting diff.

No database operations, migrations, Docker commands, Git mutations, pytest, or Ruff commands were executed.

## 6. Test results

**NOT RUN** — the current process does not have the required isolated-test environment variables or test-only password configured. Per instruction, no test command was run.

## 7. Remaining mismatches and issues

No remaining mismatches were found within the two requested alignment areas by static inspection.

Runtime verification is still required after the isolated test environment is configured. The isolated test database also remains behind the archive metadata migration, as documented in ADIM 8.10.10; that migration must be approved and completed before archive-related API tests can pass.

## 8. Recommended next actions

1. In an approved isolated-test PowerShell session, set the documented test-only environment variables and password securely.
2. With separate explicit approval, run the guarded migration upgrade to `e8f1a2b3c4d5` against `ai_bap_test` only.
3. Run the focused contract test:

```powershell
Set-Location backend
uv run --no-sync pytest tests/test_openapi_contract_alignment.py
```

4. Run Ruff for the changed backend files:

```powershell
Set-Location backend
uv run --no-sync ruff check app/routers/projects.py tests/test_openapi_contract_alignment.py
```

No commit or push was created.
