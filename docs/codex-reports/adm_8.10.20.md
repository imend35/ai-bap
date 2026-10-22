# ADIM 8.10.20 — Controlled Ruff Quality Cleanup

## 1. Step name and objective

Resolve all backend Ruff violations with minimal, behavior-preserving cleanup before final submission.

## 2. Summary of work completed

The initial Ruff inspection found 71 violations. They were classified and resolved as follows:

| Rule | Count | Resolution |
| --- | ---: | --- |
| `I001` | 27 | Sorted and grouped imports only. |
| `UP017` | 22 | Replaced `timezone.utc` with the equivalent `datetime.UTC` alias. |
| `SIM117` | 17 | Combined equivalent nested context managers while retaining left-to-right acquisition and reverse cleanup order. |
| `F401` | 1 | Removed the unused `Sprint` test import. |
| `F821` | 4 | Added type-only model imports for existing string SQLAlchemy relationship annotations in `User`. |

The `F821` findings were not auto-fixable. The added `TYPE_CHECKING` imports match the existing relationship-annotation pattern used by the other model modules and do not change runtime imports or database behavior.

The long project API context-manager cases were reviewed individually. Only adjacent temporary-project contexts were combined; the existing session context, its scope, and cleanup sequence remain unchanged.

## 3. Files inspected or modified

Modified application files:

- `backend/app/config.py`
- `backend/app/jwt_service.py`
- `backend/app/main.py`
- `backend/app/models/__init__.py`
- `backend/app/models/task.py`
- `backend/app/models/user.py`
- `backend/app/password_service.py`
- `backend/app/role_permissions.py`
- `backend/app/routers/auth.py`
- `backend/app/routers/projects.py`
- `backend/app/routers/requirements.py`
- `backend/app/routers/sprints.py`
- `backend/app/routers/tasks.py`
- `backend/app/security.py`
- `backend/app/services/ai/user_story_prompt.py`
- `backend/app/services/project_archive.py`
- `backend/app/test_database_safety.py`

Modified test files:

- `backend/tests/conftest.py`
- `backend/tests/role_permissions.py`
- `backend/tests/test_ai_user_story_api.py`
- `backend/tests/test_cors.py`
- `backend/tests/test_current_user_security.py`
- `backend/tests/test_jwt_service.py`
- `backend/tests/test_projects_api.py`
- `backend/tests/test_record_identity_schema.py`
- `backend/tests/test_security.py`
- `backend/tests/test_sprint_schemas.py`
- `backend/tests/test_sprints_api.py`
- `backend/tests/test_task_sprint_integration.py`
- `backend/tests/test_tasks_api.py`
- `backend/tests/test_test_database_safety.py`
- `backend/tests/test_user_story_approval_api.py`
- `backend/tests/test_user_story_approval_audit.py`

Created:

- `docs/codex-reports/adm_8.10.20.md`

## 4. Commands executed and results

- `uv run --no-sync ruff check app tests --output-format concise` — initial sandboxed attempt could not access the local uv cache; the subsequent approved run completed and reported 71 findings.
- `uv run --no-sync ruff check ... --select SIM117 --fix --diff` — reviewed non-writing proposed context-manager changes.
- `uv run --no-sync ruff check tests/test_projects_api.py --select SIM117` — confirmed the manually reviewed project API context-manager cleanup passed.
- `uv run --no-sync ruff check app tests --fix --select I001,UP017,F401` — applied only the reviewed mechanical cleanup categories.
- `uv run --no-sync ruff check tests/test_current_user_security.py tests/test_security.py tests/test_user_story_approval_api.py tests/test_user_story_approval_audit.py --fix --select SIM117` — applied the reviewed equivalent context-manager rewrites.
- `uv run --no-sync ruff check app tests` — **PASS**, all checks passed.
- `git diff --check` — **PASS**, no whitespace errors. Git emitted line-ending conversion warnings only.
- `git diff --name-only` and `git status --short` — reviewed changed-file list; no Git mutation was performed.

## 5. Test results

- Ruff: **PASS** — `uv run --no-sync ruff check app tests` completed with `All checks passed!`.
- Full backend pytest: **NOT RUN** — the guarded isolated PostgreSQL environment was not configured in this process. Presence-only inspection showed all required guard, connection, and test-password environment variables were unset; no values were displayed.

## 6. Issues and remaining tasks

No Ruff violations remain. No test assertions, coverage, API behavior, authorization, database logic, migrations, dependencies, or architecture were changed.

The full backend test suite remains outstanding until the operator configures the documented isolated test environment in the active PowerShell process.

## 7. Recommended next step

After configuring the guarded isolated PostgreSQL test environment using the documented procedure, run:

```powershell
Set-Location backend
uv run --no-sync pytest -q --tb=short
```

If the suite passes, perform the final submission review without committing or pushing unless separately approved.
