# ADIM 8.10.33 — Fix PostgreSQL Record Number Truncation

## 1. Step name and objective

Prepare a forward-only Alembic correction for PostgreSQL record-number truncation without resetting sequences or changing existing records.

## 2. Root cause

The existing four record-number trigger functions use `lpad(nextval(...)::text, 3, '0')`. PostgreSQL `lpad` truncates a string when the requested length is shorter than the input. Consequently, a sequence value such as `1122` becomes `112`, producing `USR-112` and colliding with an existing identifier.

The same fixed-width expression existed in all four generator functions, so the defect affected users, projects, requirements, and user stories.

## 3. Implementation summary

Created forward-only migration revision `b6c7d8e9f0a1`, following current head `e8f1a2b3c4d5`.

The migration replaces only these existing functions:

- `public.assign_users_record_number()`
- `public.assign_projects_record_number()`
- `public.assign_requirements_record_number()`
- `public.assign_user_stories_record_number()`

Each function now:

1. Captures `nextval` once as `number_text`.
2. Pads to a minimum width of three digits using `pg_catalog.greatest(pg_catalog.length(number_text), 3)`.
3. Preserves all digits above three characters.
4. Retains the schema-qualified sequence regclass reference, immutable input guard, and `SET search_path = pg_catalog` protection.

No sequence is reset, no existing record number is rewritten, and no trigger, constraint, or table is dropped or changed.

Added static regression coverage for the expected values `9`, `112`, `999`, `1000`, and `1122`. The tests validate the minimum-width formatting contract and migration source without database access or sequence mutation.

Removed only the temporary ADIM 8.10.30 same-session diagnostic import, SQL query, and print statement from `prepare_editor()`; its original `db.add(editor)` and `db.commit()` behavior remains unchanged.

## 4. Files modified

- `backend/migrations/versions/b6c7d8e9f0a1_fix_record_number_width.py`
- `backend/tests/test_record_number_width_migration.py`
- `backend/tests/test_user_story_approval_api.py`
- `docs/codex-reports/adm_8.10.33.md`

## 5. Commands executed and results

- `uv run --no-sync ruff check migrations/versions/b6c7d8e9f0a1_fix_record_number_width.py tests/test_record_number_width_migration.py tests/test_user_story_approval_api.py` — **PASS**: `All checks passed!`.
- `git diff --check` — **PASS**: no whitespace errors. Git printed line-ending conversion warnings for existing working-tree files only.

No pytest, migration, database-writing integration test, Docker, or Git mutation command was executed.

## 6. Test results

- Focused static regression pytest: **NOT RUN**, per the instruction to run only Ruff and `git diff --check`.
- Ruff: **PASS**.
- `git diff --check`: **PASS**.

## 7. Rollback considerations

The new migration intentionally refuses downgrade. Restoring the previous function bodies would reintroduce deterministic identifier truncation and collisions. This revision is safe to apply forward because it changes only future trigger-generated values; it does not mutate sequences or historical rows.

## 8. Recommended next step

After explicit approval and in the confirmed isolated test environment:

1. Apply the guarded Alembic migration to revision `b6c7d8e9f0a1`.
2. Run the new static regression test and the previously failing focused approval test.
3. Run the full backend pytest suite and Ruff.

Suggested verification commands after approved migration:

```powershell
Set-Location backend
uv run --no-sync pytest -q --tb=short tests/test_record_number_width_migration.py tests/test_user_story_approval_api.py::test_user_story_can_be_rejected_after_review
uv run --no-sync pytest -q --tb=short
uv run --no-sync ruff check app tests migrations/versions
```
