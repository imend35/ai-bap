# ADIM 8.10.41 — Resolve Legacy Alembic Ruff Warnings

## Step name and objective

Resolve the legacy Alembic Ruff diagnostics reported by `uv run --no-sync ruff check app tests migrations/versions`, limited to import ordering (`I001`) and typing modernization (`UP007`, `UP035`), without changing migration behavior.

## Summary of work completed

- Inspected all 32 initial Ruff diagnostics across eight legacy migration files.
- Replaced `typing.Sequence` with `collections.abc.Sequence` where required (`UP035`).
- Replaced legacy `Union[str, Sequence[str], None]` annotations with `str | Sequence[str] | None` (`UP007`).
- Sorted import blocks (`I001`) and removed the resulting unused `Union` imports.
- Reviewed the migration-only diff. Revision IDs, `down_revision` values, `upgrade()` and `downgrade()` operations, SQL statements, and runtime behavior remain unchanged.

## Files inspected or modified

Modified:

- `backend/migrations/versions/32937c1c1b14_add_user_story_approval_audit_trail.py`
- `backend/migrations/versions/4f2b109b0624_add_sprints_table.py`
- `backend/migrations/versions/921eeafe8be6_add_immutable_audit_identity_snapshots.py`
- `backend/migrations/versions/9440f236ffd6_add_tasks_table.py`
- `backend/migrations/versions/c7a8d9e0f1b2_add_readable_record_numbers_and_creators.py`
- `backend/migrations/versions/e8f1a2b3c4d5_add_project_archive_metadata.py`
- `backend/migrations/versions/f3174e415283_add_users_table_with_role_based_access.py`
- `backend/migrations/versions/f96458181c12_add_sprint_id_to_tasks.py`

Created:

- `docs/codex-reports/adm_8.10.41.md`

## Commands executed and results

1. `uv run --no-sync ruff check app tests migrations/versions`
   - Initial result: 32 diagnostics: `I001`, `UP007`, and `UP035` in the eight files listed above.
2. `uv run --no-sync ruff check migrations/versions/f3174e415283_add_users_table_with_role_based_access.py --diff`
   - Result: identified one remaining extra blank line in the import block; corrected it.
3. `uv run --no-sync ruff check app tests migrations/versions`
   - Result: PASS — `All checks passed!`
4. `git diff --check`
   - Result: PASS — no whitespace errors. Git emitted existing line-ending warnings only.
5. `git diff -- backend/migrations/versions`
   - Result: reviewed; only imports and revision-variable type annotations changed.

## Test results

- Ruff: PASS
- `git diff --check`: PASS
- Pytest: NOT RUN (not requested; no tests were executed)
- Migrations/database operations: NOT RUN (prohibited by this step)

## Issues and remaining tasks

No unresolved Ruff diagnostics remain for `app`, `tests`, or `migrations/versions`.

## Recommended next step

Proceed with the normal, separately approved verification workflow for the pending migration and backend changes. Do not apply migrations or alter database state as part of this lint-only step.
