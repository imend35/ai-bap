# ADIM 8.10.29 — Diagnose Single-Test User Record Number Collision

## 1. Step name and objective

Investigate why `test_user_story_can_be_rejected_after_review` fails during `prepare_editor()` with duplicate `USR-112`, without modifying source or database state.

## 2. Confirmed execution path

`test_user_story_can_be_rejected_after_review` enters context managers left to right:

1. `prepare_story(role="reviewer")` opens one `SessionLocal` session, inserts a project, requirement, user story, and reviewer user, then commits and closes that session.
2. `prepare_editor()` opens a new `SessionLocal` session, creates an editor `User` without a `record_number`, adds it, and commits. The collision occurs on this commit.
3. If both contexts succeed, the test uses the editor JWT to submit the story for review and the reviewer JWT to reject it.

Neither helper supplies or derives `record_number`; their cleanup deletes temporary rows only after their context has successfully yielded.

## 3. Confirmed repository facts

- `tests/conftest.py` only invokes `configure_test_database_environment()` before application imports. It does not create transaction fixtures, nested transactions, database resets, or lifecycle hooks.
- `app.database` has one module-level `create_engine` and one `SessionLocal` bound to it. The configuration has normal pooling with `pool_pre_ping=True`; it does not set `search_path`, schema translation, sequence cache settings, or transaction-local connection options.
- The test safety guard requires the exact isolated host, port, database, and user values before imports and reapplies them after validation.
- Searches found no `SessionLocal` monkeypatch/reassignment, `get_db` database dependency override, alternate ordinary-test engine, `schema_translate_map`, `begin_nested`, `SAVEPOINT`, `setval`, `ALTER SEQUENCE`, `currval`, test-time `nextval`, sequence cache change, `TRUNCATE`, or test database lifecycle hook in the inspected application/test paths.
- The migration creates `users_record_number_seq` with no explicit cache clause; PostgreSQL's default is `CACHE 1`. The expected live assignment function uses the schema-qualified `public.users_record_number_seq` regclass.
- The supplied evidence says the live `public.users` trigger uses that sequence, the public sequence is at `last_value = 1121`, and no committed `USR-111` or `USR-112` rows existed when separately checked.

## 4. Sequence and transaction analysis

### Confirmed

- PostgreSQL `nextval` is not transactional. A rollback, savepoint rollback, or failed insert does not rewind a sequence. Therefore normal test rollback behavior cannot cause reuse of `USR-112`.
- The test does use separate sessions for its two setup contexts. Separate sessions alone are normal and cannot duplicate a sequence value.
- With the expected function and a sequence whose next value is 1122, an insert cannot receive `USR-112`.

### Sequence-cache hypothesis

A value lower than a globally observed `last_value` can be possible only when a connection holds a previously allocated cache range. However:

1. The migration’s expected sequence cache is the PostgreSQL default of 1, which leaves no unused multi-value backend cache range.
2. Even when cache is greater than 1, PostgreSQL allocates disjoint ranges; caching alone should create gaps, not duplicate values.
3. A cache could contribute to a duplicate only if the sequence had subsequently been reset/rewound or replaced while a connection retained an old cache. No repository code performs that action, and no direct evidence currently shows it occurred in the live database.

Therefore sequence caching is **not a confirmed explanation** and is unlikely unless live catalog metadata shows non-default cache settings or a concurrent external database operation.

## 5. Root-cause status

No root cause is confirmed yet.

The current evidence is internally inconsistent with the expected single-trigger function and the reported sequence state. The remaining hypotheses are:

1. The connection executing `prepare_editor()` differs from the connection/database/schema inspected separately.
2. The live database has an additional trigger/function or other database object that affects `NEW.record_number` after the expected trigger.
3. The live sequence cache or trigger/function definition differs from the migration, possibly combined with an external sequence rewind/reset.
4. An external concurrent process is changing database objects or sequence state. No repository code supports this, but source inspection cannot rule out external actors.

## 6. Minimal same-connection instrumentation

The most decisive next diagnostic is a temporary, test-local read-only probe in `prepare_editor()` immediately before `db.add(editor)`. It must use the existing `db` session, because executing the probe starts a transaction and pins the exact database connection that the following flush/commit uses.

Do not apply this change without separate approval. The temporary probe should import `text` from SQLAlchemy, execute the following read-only SQL through `db.execute`, and log only the returned metadata (never connection URLs, passwords, emails, or names):

```python
diagnostic = db.execute(
    text(
        """
        SELECT
            current_database() AS database_name,
            current_user AS database_user,
            inet_server_addr()::text AS server_address,
            inet_server_port() AS server_port,
            pg_backend_pid() AS backend_pid,
            current_schema() AS current_schema,
            current_setting('search_path') AS search_path,
            sequence_state.last_value,
            sequence_state.is_called,
            sequence_settings.cache_size,
            array_agg(
                format('%s:%s:%s', trigger.tgname, trigger.tgenabled,
                    trigger.tgfoid::pg_catalog.regprocedure)
                ORDER BY trigger.tgname
            ) AS user_triggers
        FROM public.users_record_number_seq AS sequence_state
        CROSS JOIN pg_catalog.pg_sequences AS sequence_settings
        JOIN pg_catalog.pg_trigger AS trigger
            ON trigger.tgrelid = 'public.users'::pg_catalog.regclass
        WHERE sequence_settings.schemaname = 'public'
          AND sequence_settings.sequencename = 'users_record_number_seq'
          AND NOT trigger.tgisinternal
        GROUP BY sequence_state.last_value, sequence_state.is_called,
                 sequence_settings.cache_size
        """
    )
).mappings().one()
print({"prepare_editor_database_diagnostic": dict(diagnostic)})
```

Immediately after this probe, retain the current `db.add(editor); db.commit()` unchanged. On failure, capture the PostgreSQL error value and the printed metadata. The backend PID proves whether the diagnostic and insert used the same server connection; the sequence state and cache size test the cache hypothesis; the trigger list identifies unexpected writers.

If trigger identity requires deeper comparison, add this same-session read-only follow-up before the insert:

```python
function_source = db.execute(
    text(
        """
        SELECT pg_catalog.pg_get_functiondef(
            'public.assign_users_record_number()'::pg_catalog.regprocedure
        ) AS function_definition
        """
    )
).scalar_one()
print({"assign_users_record_number_definition": function_source})
```

The returned definition contains database code only, not credentials or personal data. Remove all temporary instrumentation after diagnosis.

## 7. Files inspected

- `backend/tests/test_user_story_approval_api.py`
- `backend/tests/conftest.py`
- `backend/app/database.py`
- `backend/app/config.py`
- `backend/app/test_database_safety.py`
- `backend/migrations/versions/c7a8d9e0f1b2_add_readable_record_numbers_and_creators.py`
- `backend/migrations/versions/d4e5f6a7b8c9_harden_record_number_trigger_functions.py`
- Repository-wide application/test searches for database engines, sessions, transaction scopes, sequence operations, and database overrides.

Modified:

- `docs/codex-reports/adm_8.10.29.md`

## 8. Commands executed and results

- Read-only file inspection of the full failing test module, safety guard, engine/session configuration, and migrations — completed.
- Read-only repository searches for session replacement, database dependency overrides, alternate engines, nested transactions, sequence manipulation, cache settings, and lifecycle hooks — no relevant ordinary-test mechanism found.
- Presence-only guarded environment inspection — required values are unset in this process; no secret values were displayed.
- Database queries and tests: **NOT RUN**, as required by the diagnostic constraints and unavailable guarded environment.

## 9. Recommended next step

Obtain approval to add the temporary same-session probe described in section 6, configure the guarded isolated environment, and run only:

```powershell
Set-Location backend
uv run --no-sync pytest -q --tb=short tests/test_user_story_approval_api.py::test_user_story_can_be_rejected_after_review
```

Use the resulting same-connection PID, sequence state, cache size, and trigger list to identify the actual writer before proposing any database or source correction.
