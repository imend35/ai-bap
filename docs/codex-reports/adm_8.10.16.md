# ADIM 8.10.16 — Resolve Seven Remaining Backend Test Failures

## 1. Step name and objective

**Step:** ADIM 8.10.16 — Resolve Seven Remaining Backend Test Failures

**Objective:** Diagnose and minimally correct the seven remaining backend test failures without altering application behavior, persistence rules, authorization, or database safety controls.

## 2. Root-cause analysis

### Creator eager-loading wiring failures: project list and detail

`ProjectResponse` now includes both `created_by` and `archived_by`. The project list and shared project-detail loader intentionally eager-load both `Project.created_by` and `Project.archived_by` before response serialization. The two failing AST tests still required only `Project.created_by` and were outdated.

### Project mutation creator-loading wiring failure

`update_project` intentionally delegates both its locked lookup and its response reload to `get_project_with_relationships`. That helper eager-loads both response actor relationships. The failing AST test incorrectly required the route function itself to contain a direct `selectinload(Project.created_by)` call. The implementation preserves eager loading through the shared helper; the test assumption was outdated.

### ProjectResponse fixture-validation failures

`ProjectResponse` correctly requires `archived_at` and `archived_by`, matching the existing archive-capable API response contract. Three test-only `SimpleNamespace` project fixtures predated those fields and failed validation. The response schema is correct; the fixtures required explicit unarchived values of `None`.

### Archive lifecycle persistence failure

The archive route commits archive metadata and returns a response that exposes non-null archive data. The failure was not an ORM identity-map issue or a persistence defect. The test made archive and repeated-archive requests, then immediately made restore and repeated-restore requests before opening the session that asserted archive persistence. By that point, the database had correctly been restored and `archived_at` was `None`.

The corrected test now verifies the API archive responses and persisted archive fields from a fresh `SessionLocal` session before it calls restore. It then separately verifies restored null metadata. This also proves status preservation and idempotency at the appropriate lifecycle points.

## 3. Files modified

- `backend/tests/test_creator_loading_wiring.py`
  - Updated Project list/detail expected eager-load relationships to include `created_by` and `archived_by`.
- `backend/tests/test_mutation_creator_loading_wiring.py`
  - Replaced the outdated direct-loader assumption for `update_project` with assertions that it uses the shared relationship loader twice and that the helper eager-loads both actor relationships.
  - Added explicit `archived_at=None` and `archived_by=None` values to the ProjectResponse test fixture.
- `backend/tests/test_response_identity_schemas.py`
  - Added explicit unarchived metadata to authored and historical ProjectResponse fixtures.
- `backend/tests/test_projects_api.py`
  - Reordered archive lifecycle assertions to inspect persisted archive metadata before restore.
- `docs/codex-reports/adm_8.10.16.md`
  - Added this report.

No production application, schema, migration, database configuration, or OpenAPI contract behavior was changed for this step.

## 4. Verification and commands executed

Read-only inspections covered the exact failing tests, project router, project schema, project model, and record-creator schema.

No pytest, Ruff, database operation, migration, Docker command, build, formatter, or Git mutation was executed. The current process does not contain the required isolated-test environment values or test-only password.

## 5. Test results

- Affected pytest tests: **NOT RUN**.
- Project API archive lifecycle regression test: **NOT RUN**.
- Ruff: **NOT RUN**.

The supplied prior suite result was 497 passed and 7 failed. This step did not re-run the suite.

## 6. Outstanding risks

- Runtime verification is required in the configured isolated PostgreSQL test environment.
- The isolated test database must be at the approved archive-metadata revision before archive integration tests can run successfully.
- No remaining source-level defect was found in the seven reported failure areas; however, this conclusion requires test execution confirmation.

## 7. Recommended next commands

After the isolated-test environment is configured and the approved archive migration has completed, run the affected tests from `backend`:

```powershell
uv run --no-sync pytest tests/test_creator_loading_wiring.py tests/test_mutation_creator_loading_wiring.py tests/test_response_identity_schemas.py tests/test_projects_api.py
```

Then run the directly affected lint checks:

```powershell
uv run --no-sync ruff check tests/test_creator_loading_wiring.py tests/test_mutation_creator_loading_wiring.py tests/test_response_identity_schemas.py tests/test_projects_api.py
```

If those pass, run the full backend pytest suite and the full backend Ruff check in a separately approved verification step. No commit or push was created.
