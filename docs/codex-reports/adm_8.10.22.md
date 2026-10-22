# ADIM 8.10.22 — Diagnose Four User Record Number Collisions

## 1. Step name and objective

Diagnose duplicate `users.record_number` failures without changing application data, schemas, tests, migrations, or database objects.

## 2. Root cause and evidence

The failures are caused by sequence drift in the persistent isolated test database: `public.users_record_number_seq` is behind at least one already retained `users.record_number` suffix.

Evidence:

1. `User.record_number` is `VARCHAR(32)`, `NOT NULL`, unique, and declared with `server_default=FetchedValue()` in `backend/app/models/user.py`. Application code does not assign it.
2. Migration `c7a8d9e0f1b2_add_readable_record_numbers_and_creators.py` creates `uq_users_record_number`, `users_record_number_seq`, and a `BEFORE INSERT` trigger. The trigger rejects a supplied record number and assigns `USR-` plus `nextval(users_record_number_seq)`.
3. Migration `d4e5f6a7b8c9_harden_record_number_trigger_functions.py` preserves that assignment behavior using the schema-qualified `public.users_record_number_seq`.
4. Each failing test inserts a real `User` through `SessionLocal` with a unique UUID-derived email and no `record_number` field:
   - `test_record_identity_api_integration.py` creates a reviewer.
   - `test_user_story_approval_api.py` uses `prepare_story(role=...)` and `prepare_editor()`.
   - `test_user_story_approval_audit.py` reuses both helpers and, in one test, creates an audit-reader administrator.
5. Repository inspection found no ordinary-test code that resets the users sequence, truncates `users`, calls `setval`, or supplies a user record number. Normal fixture cleanup deletes temporary rows but correctly does not rewind PostgreSQL sequences.
6. A duplicate assigned by `nextval` can occur only when a row with the generated value already exists while the sequence has not advanced beyond that suffix. The reported collisions (`USR-101`, `USR-110`, and `USR-111`) therefore prove a sequence-to-table mismatch in the test database state.

The migration design correctly synchronizes the sequence during its own backfill. It does not and cannot protect against later state changes such as restoring/copying table rows without the matching sequence state, or resetting the sequence while retained users remain. The repository's legacy validator defines the intended invariant as: the next sequence value must be greater than every assigned suffix.

## 3. Classification

- Application logic: **not defective**. User inserts rely on the intended PostgreSQL trigger.
- Test fixtures: **not the source of the duplicate identifier**. They use unique emails and do not control record numbers; deleting temporary users without resetting sequences is correct.
- Migration design: **correct at migration time**. It aligns the sequence to the backfilled maximum.
- Isolated test database state: **defective/stale**. Its durable volume contains at least one user number not reflected by the sequence position.

## 4. Files inspected

- `backend/app/models/user.py`
- `backend/app/test_database_safety.py`
- `backend/migrations/versions/c7a8d9e0f1b2_add_readable_record_numbers_and_creators.py`
- `backend/migrations/versions/d4e5f6a7b8c9_harden_record_number_trigger_functions.py`
- `backend/scripts/validate_legacy_record_number_migration.py`
- `backend/tests/conftest.py`
- `backend/tests/test_record_identity_api_integration.py`
- `backend/tests/test_user_story_approval_api.py`
- `backend/tests/test_user_story_approval_audit.py`
- `docs/isolated-test-database.md`
- `compose.test.yaml`
- `docker/compose-test.variables`

Modified:

- `docs/codex-reports/adm_8.10.22.md`

## 5. Commands executed and results

- Read-only repository searches for `record_number`, `users_record_number_seq`, `setval`, `nextval`, `TRUNCATE`, `RESTART IDENTITY`, and user fixture creation — confirmed the trigger-based mechanism and found no ordinary-test sequence reset or direct record-number assignment.
- Read-only inspection of the model, both record-number migrations, the sequence-validation helper, the four failing test paths, the test safety guard, and isolated database documentation — confirmed the evidence above.
- Presence-only environment inspection — required guarded isolated-database variables and the test-password variable are unset in this process. No password or secret value was displayed.

No database connection was made because isolation could not be proven from the current process.

## 6. Safe read-only database diagnostic procedure

After configuring the existing guarded isolated-test environment documented in `docs/isolated-test-database.md`, the operator may run this read-only metadata query. It returns only sequence state and numeric record-number metadata; it does not return user emails, names, password hashes, or other sensitive data.

```powershell
$env:PGPASSWORD = $env:AI_BAP_TEST_POSTGRES_PASSWORD
psql --host 127.0.0.1 --port 55432 --username ai_bap_test_user --dbname ai_bap_test --set ON_ERROR_STOP=1 --command "BEGIN TRANSACTION READ ONLY; SELECT last_value, is_called FROM public.users_record_number_seq; SELECT COALESCE(MAX((substring(record_number FROM '^USR-([0-9]+)$'))::bigint), 0) AS max_assigned_suffix FROM public.users; SELECT record_number FROM public.users WHERE record_number IN ('USR-101', 'USR-110', 'USR-111') ORDER BY record_number; COMMIT;"
Remove-Item Env:PGPASSWORD
```

Expected confirmation of this diagnosis: `last_value + (is_called ? 1 : 0)` is less than or equal to `max_assigned_suffix`, or one of the reported values is retained while the next sequence value can generate it.

## 7. Smallest safe correction

No application or test-source change is warranted. A separately approved, test-only database repair is required to re-align `public.users_record_number_seq` with the highest retained `users.record_number` suffix. It must be performed only after all pytest processes using the isolated database have stopped.

The approved repair should reuse the migration's alignment semantics:

```sql
SELECT setval(
    'public.users_record_number_seq',
    COALESCE(MAX(SUBSTRING(record_number FROM 5)::bigint), 1),
    COUNT(*) > 0
)
FROM public.users;
```

This repair changes only the isolated test sequence. It does not delete or alter user rows, does not affect development or production, and requires explicit approval because it writes database state.

## 8. Test results and recommended next step

- Tests: **NOT RUN**. This diagnostic step prohibited test execution, and the required guarded environment was unavailable.
- Ruff: **NOT RUN**. Not required for this read-only diagnostic step; the prior step recorded a passing result.

Recommended sequence after approval:

1. Configure the documented isolated-test environment and run the read-only query above.
2. If it confirms sequence drift, approve and apply the one-statement test-only sequence repair.
3. Run the four failing tests:

```powershell
Set-Location backend
uv run --no-sync pytest -q --tb=short tests/test_record_identity_api_integration.py::test_approval_rejection_and_audit_preserve_creator_and_actor_snapshots tests/test_user_story_approval_api.py::test_user_story_can_be_rejected_after_review tests/test_user_story_approval_audit.py::test_rejection_persists_audit_identity_snapshots tests/test_user_story_approval_audit.py::test_audit_history_survives_story_and_actor_deletion
```

4. If focused tests pass, run the full backend suite in the same confirmed isolated environment.
