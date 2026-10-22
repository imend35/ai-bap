# ADIM 8.10.26 — Investigate Persistent User Record Number Collisions

## 1. Step name and objective

Determine why focused integration tests receive `USR-111` or `USR-112` despite the reported high value of `public.users_record_number_seq`, without changing source files or database state.

## 2. Confirmed facts

The following are confirmed by the supplied execution evidence and repository inspection:

1. The reported test connection target is the guarded isolated PostgreSQL database: `ai_bap_test` at `127.0.0.1:55432`, using `ai_bap_test_user`.
2. `public.users_record_number_seq` was observed at `last_value = 1121`, `is_called = true`; its next `nextval` result is therefore `1122`.
3. The highest retained numeric suffix in `public.users.record_number` was reported as `256`.
4. The failing `INSERT` statements omit `record_number`.
5. The observed sequence advanced from `1113` to `1121` during the investigation, while failures still reported duplicate `USR-111` or `USR-112`.
6. The expected hardened migration function, `public.assign_users_record_number()`, assigns `NEW.record_number` from the schema-qualified regclass `public.users_record_number_seq`:

```sql
'USR-' || pg_catalog.lpad(
    pg_catalog.nextval('public.users_record_number_seq'::pg_catalog.regclass)::text,
    3,
    '0'
)
```

7. With that exact function as the only effective record-number writer, a sequence at 1121 cannot produce `USR-111` or `USR-112`. It would produce `USR-1122` on the next insert.
8. `backend/app/database.py` defines one module-level SQLAlchemy engine and one `SessionLocal`, both using `get_settings().database_url`. The integration guard runs before application database imports and re-applies the fixed isolated host, port, database, and user values.
9. Inspection found no test override of `get_db`, no alternate test engine, no `schema_translate_map`, and no application/test-side record-number generator for users. Authentication dependency overrides change only the current user, not database sessions.
10. The four failures share the same database-backed user creation behavior:
    - `test_record_identity_api_integration.py` inserts a reviewer.
    - `test_user_story_approval_api.py` inserts a reviewer through `prepare_story` and an editor through `prepare_editor`.
    - `test_user_story_approval_audit.py` reuses those helpers and, in one case, inserts an audit-reader administrator.
    Every insertion leaves `record_number` unspecified.

## 3. What is not yet confirmed

Live PostgreSQL catalog inspection was not performed in this process. All required guarded-test environment variables and the test-password variable are unset here, so connecting would not satisfy the safety requirement.

Consequently, the following must remain hypotheses until the operator runs the read-only catalog query in section 6:

1. `public.users` has an extra enabled non-internal trigger that runs after the expected assignment trigger and overwrites `NEW.record_number`.
2. `trg_assign_users_record_number` references a drifted/replaced function whose body differs from migration `d4e5f6a7b8c9` and uses another sequence or stale generation source.
3. A separate trigger function advances `public.users_record_number_seq` but a later trigger supplies `USR-111` or `USR-112`. This best explains why the public sequence advances while the collision value remains low.
4. Less likely: the individual failing process is connected to a different database or schema than the inspected session. Source inspection does not support an alternate engine or schema, but a live per-session identity query is required to eliminate this possibility.

An ordinary `search_path` difference cannot explain the behavior if the live function matches the hardened migration, because its sequence reference is explicitly `public.users_record_number_seq` as a `regclass`.

## 4. Migration comparison

Expected migration objects:

- `c7a8d9e0f1b2_add_readable_record_numbers_and_creators.py` creates `users_record_number_seq`, `uq_users_record_number`, `trg_assign_users_record_number`, and the original assignment function.
- `d4e5f6a7b8c9_harden_record_number_trigger_functions.py` replaces the function with a schema-qualified `public.users_record_number_seq` reference and function-level `SET search_path = pg_catalog`.
- `e8f1a2b3c4d5_add_project_archive_metadata.py` follows the hardening revision and does not alter user record-number machinery.

The live trigger definition, trigger set, function OID, function source, function configuration, and all user-related sequences must be compared to these definitions before identifying a corrective database action.

## 5. Files inspected

- `backend/app/config.py`
- `backend/app/database.py`
- `backend/app/test_database_safety.py`
- `backend/migrations/versions/c7a8d9e0f1b2_add_readable_record_numbers_and_creators.py`
- `backend/migrations/versions/d4e5f6a7b8c9_harden_record_number_trigger_functions.py`
- `backend/migrations/versions/e8f1a2b3c4d5_add_project_archive_metadata.py`
- `backend/tests/conftest.py`
- `backend/tests/test_record_identity_api_integration.py`
- `backend/tests/test_user_story_approval_api.py`
- `backend/tests/test_user_story_approval_audit.py`
- `docs/isolated-test-database.md`

Modified:

- `docs/codex-reports/adm_8.10.26.md`

## 6. Exact read-only live diagnostics for the operator

After configuring the documented guarded isolated-test environment, run the following command from a shell with `psql` available. It starts a read-only transaction, returns only database/catalog metadata and record-number values, and does not expose credentials or user profile data.

```powershell
$env:PGPASSWORD = $env:AI_BAP_TEST_POSTGRES_PASSWORD
psql --host 127.0.0.1 --port 55432 --username ai_bap_test_user --dbname ai_bap_test --set ON_ERROR_STOP=1 --command "BEGIN TRANSACTION READ ONLY; SELECT current_database() AS database_name, current_user AS database_user, inet_server_port() AS server_port, current_schema() AS current_schema, current_setting('search_path') AS search_path; SELECT t.tgname, t.tgenabled, t.tgisinternal, t.tgtype, p.oid::pg_catalog.regprocedure AS trigger_function, p.proconfig AS function_configuration, pg_catalog.pg_get_triggerdef(t.oid) AS trigger_definition, pg_catalog.pg_get_functiondef(p.oid) AS function_definition FROM pg_catalog.pg_trigger AS t JOIN pg_catalog.pg_proc AS p ON p.oid = t.tgfoid WHERE t.tgrelid = 'public.users'::pg_catalog.regclass ORDER BY t.tgname; SELECT conname, contype, pg_catalog.pg_get_constraintdef(oid) AS definition FROM pg_catalog.pg_constraint WHERE conrelid = 'public.users'::pg_catalog.regclass ORDER BY conname; SELECT schemaname, sequencename, start_value, min_value, max_value, increment_by, cycle, last_value FROM pg_catalog.pg_sequences WHERE schemaname = 'public' AND (sequencename ILIKE '%user%' OR sequencename ILIKE '%record_number%') ORDER BY sequencename; SELECT last_value, is_called FROM public.users_record_number_seq; SELECT record_number FROM public.users WHERE record_number IN ('USR-111', 'USR-112') ORDER BY record_number; COMMIT;"
Remove-Item Env:PGPASSWORD
```

Interpretation:

- Exactly one enabled, non-internal assignment trigger should exist for `public.users` and it should call `public.assign_users_record_number()`.
- The function source must contain `nextval('public.users_record_number_seq'::pg_catalog.regclass)` and its configuration must include `search_path=pg_catalog`.
- Any second enabled non-internal `BEFORE INSERT` trigger is material evidence, especially if it can write `NEW.record_number`.
- The `USR-111` and `USR-112` lookup identifies whether those values are retained collision targets without exposing user emails or names.

## 7. Smallest safe correction

Do not alter application or test source, and do not reset the healthy public sequence.

The smallest correction depends on catalog evidence:

- If an extra trigger is present, remove or disable only that drifted test-database trigger after explicit approval.
- If the expected trigger points to a drifted function, restore only `public.assign_users_record_number()` to the already-reviewed migration definition after explicit approval.
- If a different function/sequence is found, repair only that identified database object after explicit approval.
- Only if the live catalog query proves a different connection target should application/test configuration be reconsidered; current source inspection does not support that hypothesis.

No sequence reset is recommended from the present evidence. The reported public sequence is already above every known user suffix and is not the direct source of `USR-111` or `USR-112` under the expected function.

## 8. Commands executed and results

- Presence-only inspection of guarded environment variables — all required values were unset; no secrets were displayed.
- Read-only inspection of the application engine/session configuration, safety guard, relevant test fixtures, migration chain, and searches for alternate engines, database overrides, sequence manipulation, and schema routing — completed.
- Database catalog queries: **NOT RUN**, because the guarded environment was unavailable in this process.

## 9. Recommended verification sequence

1. Run the read-only catalog command in section 6.
2. Compare the returned trigger/function source with migration `d4e5f6a7b8c9`.
3. Obtain approval for the minimal object-specific test-database repair indicated by that comparison.
4. Re-run the four focused failing tests, then the full backend suite, in the same confirmed isolated environment.
