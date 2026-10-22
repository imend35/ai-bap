# ADIM 8.10.14 — TaskUpdate.status OpenAPI Contract Alignment

## 1. Step name and objective

**Step:** ADIM 8.10.14 — TaskUpdate.status OpenAPI Contract Alignment

**Objective:** Resolve the `TaskUpdate.status` OpenAPI contract-test mismatch while preserving the API’s intended rejection of explicitly supplied `null` values.

## 2. Findings

`TaskUpdate.status` is declared in the Pydantic model as `TaskStatus | None = None`. This is needed so a PATCH request may omit `status`. Pydantic’s generated OpenAPI schema therefore exposes an `anyOf` that includes `null`.

However, the `TaskUpdate.validate_update_fields` model validator rejects an explicitly supplied `null` for every field except `sprint_id`. The PATCH endpoint validates `TaskUpdate` before its handler runs, and existing task API coverage verifies that `{ "status": null }` receives HTTP 422.

Therefore, `null` is not an accepted API payload value for `TaskUpdate.status`. The checked-in OpenAPI contract was already correct in documenting `status` as only `TaskStatus`; changing it to allow `null` would conceal a contract defect.

## 3. Changes made

### Modified

- `backend/tests/test_openapi_contract_alignment.py`
  - Kept the checked-in `TaskUpdate.status` assertion non-nullable.
  - Added an explicit assertion that the FastAPI-generated runtime schema contains the nullable `anyOf` artifact.
  - Added direct model-validation coverage proving an explicitly supplied `status: null` raises `ValidationError`.
  - Kept the existing Task response component alignment assertions from ADIM 8.10.12.
- `docs/codex-reports/adm_8.10.14.md`
  - Added this report.

### Not modified

- `openapi.yaml`: no change was necessary; it already documents the accepted request behavior correctly.
- `backend/app/schemas/task.py`: no application behavior change was necessary.
- No database model, migration, dependency, or endpoint behavior was changed.

## 4. Commands executed and results

Read-only inspections reviewed:

- `backend/app/schemas/task.py`
- Relevant `TaskUpdate` section in `openapi.yaml`
- The focused OpenAPI contract assertion
- Existing task API validation coverage

No migrations, Docker commands, database operations, Git mutations, pytest, or Ruff commands were executed.

## 5. Test results

**NOT RUN** — the current process does not have the required isolated-test environment variables or test-only password configured. The supplied prior result was 11 passed and 1 failed in `tests/test_openapi_contract_alignment.py`; this step did not re-run that test.

## 6. Remaining issues

- Runtime verification remains required after the isolated test environment is configured.
- The isolated database still requires the separately approved archive metadata migration before archive-related integration tests can pass.

## 7. Recommended next actions

After the isolated test environment is configured and the required database migration is approved/completed, run:

```powershell
Set-Location backend
uv run --no-sync pytest tests/test_openapi_contract_alignment.py
```

Then run the focused lint check:

```powershell
Set-Location backend
uv run --no-sync ruff check tests/test_openapi_contract_alignment.py
```

No commit or push was created.
