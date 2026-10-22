# ADIM 8.10.10 — Test Schema Migration Safety and OpenAPI Failure Diagnosis

## 1. Step name and objective

**Step:** ADIM 8.10.10 — Test Schema Migration Safety and OpenAPI Failure Diagnosis

**Objective:** Diagnose the isolated test-database schema drift and OpenAPI contract failures, and define the smallest safe corrective actions without changing code or database state.

## 2. Summary of findings

The focused test failures have two independent causes:

1. The confirmed isolated database is behind the archive-metadata migration. Its `projects` table has neither `archived_at` nor `archived_by_id`, which directly explains the shared archive-related failures.
2. The checked-in OpenAPI contract is not aligned with FastAPI’s generated schema names and generated operation IDs for two areas:
   - Task endpoint responses reference `Task` in `openapi.yaml`, while the runtime response model is the Pydantic class `TaskResponse`, which FastAPI publishes as `TaskResponse`.
   - The archive and restore route decorators omit explicit `operation_id` values. FastAPI therefore generates IDs from each function/path/method, while `openapi.yaml` declares the intended stable IDs `archiveProject` and `restoreProject`.

No migration, test, formatter, build, Git operation, database mutation, or source change was performed in this step.

## 3. Files inspected or modified

### Inspected

- `docs/isolated-test-database.md`
- `backend/scripts/run_isolated_test_alembic.py`
- `backend/migrations/versions/c7a8d9e0f1b2_add_readable_record_numbers_and_creators.py`
- `backend/migrations/versions/d4e5f6a7b8c9_harden_record_number_trigger_functions.py`
- `backend/migrations/versions/e8f1a2b3c4d5_add_project_archive_metadata.py`
- `backend/app/models/project.py`
- `backend/app/routers/projects.py`
- `backend/app/routers/tasks.py`
- `backend/app/schemas/task.py`
- `backend/app/main.py`
- `openapi.yaml`
- `backend/tests/test_openapi_contract_alignment.py`

### Created

- `docs/codex-reports/adm_8.10.10.md`

## 4. Isolated database metadata evidence

A read-only metadata query was run only against the confirmed dedicated target `ai_bap_test` at loopback `127.0.0.1:55432`, inside a `READ ONLY` transaction.

### Actual Alembic revision

`c7a8d9e0f1b2`

### Actual `projects` columns

- `id`
- `name`
- `description`
- `status`
- `created_at`
- `updated_at`
- `record_number`
- `created_by_id`

### Missing archive database objects

The database does not yet contain any of the objects introduced by the project archive metadata migration:

- Nullable `projects.archived_at` timestamp column.
- Nullable `projects.archived_by_id` UUID column.
- `fk_projects_archived_by_id_users` foreign key to `users.id` with `ON DELETE RESTRICT`.
- `ck_projects_archive_metadata_paired` check constraint.
- `ix_projects_archived_at` index.
- `ix_projects_archived_by_id` index.

The existing `projects` indexes and constraints contain only the primary key, readable record-number uniqueness, and the `created_by_id` foreign key. This confirms schema drift rather than an application-code defect.

## 5. Required Alembic migration path

The required chain from the current isolated-test revision to the repository head is:

```text
c7a8d9e0f1b2
  -> d4e5f6a7b8c9  harden record-number trigger functions
  -> e8f1a2b3c4d5  add project archive metadata
```

`e8f1a2b3c4d5` is the migration that adds the missing archive fields and database guarantees. Its immediate predecessor is `d4e5f6a7b8c9`, so an upgrade to `e8f1a2b3c4d5` correctly applies both pending revisions in order.

## 6. Guarded isolated-test migration procedure

The repository provides `backend/scripts/run_isolated_test_alembic.py`. It first invokes the fail-closed test-environment guard, then validates that the effective SQLAlchemy target is exactly the approved isolated database tuple before passing arguments to Alembic.

After the operator has securely supplied the existing test-only password and set the documented normal-test environment variables, use the following commands from `backend` only after explicit approval to migrate the isolated test database:

```powershell
$env:AI_BAP_ALEMBIC_TARGET = "isolated-test"
uv run --no-sync python scripts/run_isolated_test_alembic.py current
```

```powershell
uv run --no-sync python scripts/run_isolated_test_alembic.py upgrade e8f1a2b3c4d5
```

Do not run `alembic upgrade` directly, do not use a development or production connection, and do not downgrade or remove the test volume. The password remains only in the operator’s session; it must not be printed or written to files.

## 7. OpenAPI root-cause analysis

### Task versus TaskResponse

`backend/app/routers/tasks.py` declares `TaskResponse` as the response model for task create, read, and update routes. `backend/app/schemas/task.py` defines the response Pydantic model with the class name `TaskResponse`. FastAPI therefore generates the runtime component reference `#/components/schemas/TaskResponse`.

`openapi.yaml` instead declares and references `#/components/schemas/Task`. The response shape is conceptually the same, but the component name differs. The failure is a contract naming drift, not a runtime task behavior defect.

**Smallest safe correction:** update the checked-in OpenAPI component references and component name from `Task` to `TaskResponse`, then update the focused contract assertions to require the aligned name. This changes documentation/contract metadata only and preserves endpoint payload behavior.

### Archive and restore operation IDs

`openapi.yaml` declares stable IDs `archiveProject` and `restoreProject`. In `backend/app/routers/projects.py`, the archive and restore decorators define only `response_model`; they do not declare `operation_id`. FastAPI consequently emits generated IDs based on Python function/path/method names, which do not equal the checked-in contract IDs.

**Smallest safe correction:** add `operation_id="archiveProject"` to the archive route decorator and `operation_id="restoreProject"` to the restore route decorator. This changes generated OpenAPI metadata only; it does not change routing, authorization, persistence, or response behavior.

## 8. Recommended verification sequence

1. In the approved isolated-test PowerShell session, set the normal test environment variables and secure password as documented in ADIM 8.10.9 v2.
2. Run the guarded `current` command and confirm the reported revision is `c7a8d9e0f1b2`.
3. With explicit migration approval, run the guarded upgrade to `e8f1a2b3c4d5`.
4. Run a read-only metadata check confirming both archive columns, both indexes, the foreign key, and the check constraint exist.
5. Apply the two minimal OpenAPI-alignment source changes in a separately approved code-change step.
6. Run focused contract and project API tests, then the full backend pytest suite and Ruff.
7. Record exact PASS/FAIL counts and any remaining failures in the next step report.

## 9. Test results

No tests were executed in this diagnostic step. The supplied prior result was: 69 focused tests, 25 passed, and 44 failed; 42 failures were associated with the missing archive schema, with two separate OpenAPI alignment failures.

## 10. Blockers and next action

The isolated database upgrade requires explicit operator approval because it performs DDL, even though the guarded script verifies the dedicated test target first. The OpenAPI corrections require a separate explicit approval to modify source and contract files.

No further action was taken.
