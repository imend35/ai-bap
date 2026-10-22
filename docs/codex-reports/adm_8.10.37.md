# ADIM 8.10.37 — Correct PostgreSQL GREATEST Syntax

## 1. Step name and objective

Correct the invalid schema-qualified `pg_catalog.greatest(...)` expression through a forward-only Alembic migration, without changing applied revisions, historical records, or sequence state.

## 2. Root cause

Migration `b6c7d8e9f0a1` correctly addressed fixed-width `LPAD` truncation but used `pg_catalog.greatest(...)`. PostgreSQL treats `GREATEST` as a SQL expression, not as a schema-qualified callable function. The resulting function definitions fail when the migration attempts to create them.

## 3. Implementation summary

Created successor revision `c8d9e0f1a2b3`, with `down_revision = "b6c7d8e9f0a1"`.

The new migration replaces the same four assignment functions:

- `public.assign_users_record_number()`
- `public.assign_projects_record_number()`
- `public.assign_requirements_record_number()`
- `public.assign_user_stories_record_number()`

Every function now uses:

```sql
GREATEST(pg_catalog.length(number_text), 3)
```

This retains minimum-three-digit formatting while preserving values with four or more digits. The migration also retains:

- schema-qualified sequence regclass references;
- the immutable record-number input rejection;
- `SET search_path = pg_catalog`;
- `SET LOCAL lock_timeout = '5s'`.

No historical rows, sequence values, triggers, constraints, or tables are changed.

Updated the static regression test to target the successor migration and assert that unqualified `GREATEST(...)` is present while `pg_catalog.greatest(` is absent.

## 4. Read-only SQL validation query

After the approved migration has been applied to the isolated test database, the following read-only query demonstrates the expected formatting without invoking or advancing a sequence:

```sql
SELECT
    value,
    pg_catalog.lpad(
        value::text,
        GREATEST(pg_catalog.length(value::text), 3),
        '0'
    ) AS formatted_number
FROM (VALUES (9), (112), (999), (1000), (1122)) AS samples(value);
```

Expected `formatted_number` values: `009`, `112`, `999`, `1000`, and `1122`.

## 5. Files modified

- `backend/migrations/versions/c8d9e0f1a2b3_correct_record_number_greatest_syntax.py`
- `backend/tests/test_record_number_width_migration.py`
- `docs/codex-reports/adm_8.10.37.md`

## 6. Commands executed and results

- `uv run --no-sync ruff check migrations/versions/c8d9e0f1a2b3_correct_record_number_greatest_syntax.py tests/test_record_number_width_migration.py` — **PASS**: `All checks passed!`.
- `git diff --check` — **PASS**: no whitespace errors. Git emitted only existing line-ending conversion warnings.

No migration, integration test, Docker command, database operation, Git mutation, commit, or push was executed.

## 7. Test results

- Focused pytest: **NOT RUN**, per the instruction to run only Ruff and `git diff --check`.
- Ruff: **PASS**.
- `git diff --check`: **PASS**.

## 8. Rollback considerations

The successor migration intentionally refuses downgrade because returning to the predecessor would restore invalid PostgreSQL SQL. This is forward-only and safe: it changes only future trigger function definitions; no user, project, requirement, or user-story record number is rewritten.

## 9. Recommended next step

After explicit approval, apply the guarded migration through revision `c8d9e0f1a2b3` in the isolated test environment. Then run the read-only validation query, the focused regression tests, the four previously failing integration tests, and the full backend suite.
