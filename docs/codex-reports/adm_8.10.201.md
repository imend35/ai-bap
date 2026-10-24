# ADIM 8.10.201 — Final Read-Only Test Fixture Safety Analysis

## 1. Step Name and Objective

Assess, without executing tests or connecting to PostgreSQL, whether the existing database-backed regression tests can safely run against the populated `ai_bap_test` database while preserving its existing records.

## 2. Human Product Owner Authorization

This was a read-only source and test-fixture analysis. Authorized actions included repository inspection, read-only Git checks, and this one report. No test, database connection/query, Docker operation, application/configuration edit, Git/GitHub mutation, or deployment was authorized or performed.

## 3. Verified Host-Side Evidence

The following host facts were supplied as verified by the Human Product Owner. They were not re-queried in this step:

| Item | Reported value |
|---|---|
| Container / Compose project / service | `ai-bap-test-db-test-1` / `ai-bap-test` / `db-test` |
| Container health | Running and healthy |
| PostgreSQL | 16.13 |
| Bound host endpoint | `127.0.0.1:55432` |
| Database / user | `ai_bap_test` / `ai_bap_test_user` |
| Persistent volume | `ai-bap-test_ai_bap_test_data` |
| Connection identity | `current_database() = ai_bap_test`; current user is `ai_bap_test_user` |
| Existing row counts | users 2; projects 1; requirements 1; user stories 2; approval audits 43; sprints 0; tasks 0; Alembic version rows 1 (50 total) |

The counts came from SELECTs in a read-only transaction, but the session itself was not configured read-only. No record is presumed synthetic or disposable. The test password was previously exposed in conversation and is treated as compromised; its value is intentionally omitted.

## 4. Files and Test Modules Inspected

Inspected repository instructions and the prior ADIM 8.10.197–200 reports, plus `compose.test.yaml`, `docs/isolated-test-database.md`, `docs/testing-strategy.md`, `backend/app/test_database_safety.py`, `backend/tests/conftest.py`, `backend/pyproject.toml`, and the requested test modules:

- `backend/tests/test_auth_registration_api.py`
- `backend/tests/test_auth_login_api.py`
- `backend/tests/test_current_user_security.py`
- `backend/tests/test_role_permissions.py`
- `backend/tests/test_projects_api.py`
- `backend/tests/test_admin_users_api.py`
- `backend/tests/test_database.py`
- `backend/tests/test_test_database_safety.py`
- `backend/tests/test_render_free_deployment_configuration.py`

Because the project/audit fixture dependency chain can create approval history, also inspected `backend/tests/test_user_story_approval_api.py` and `backend/tests/test_user_story_approval_audit.py`. No PostgreSQL connection, SQL execution, or test execution was made. References below point to the inspected files and function names; exact line numbers can shift with local edits.

## 5. Fixture Dependency Map

| Fixture/helper | Scope and data path | Lifecycle and isolation |
|---|---|---|
| `configure_test_database_environment()` in `backend/tests/conftest.py` (module import) | Calls `backend/app/test_database_safety.py` guard; requires explicit test-mode confirmation and password variables, then sets the fixed test target and enables registration for the test process. | Environment guard only. It does not validate database contents, start a transaction around each test, or provide rollback isolation. |
| `registration_enabled`, `registration_email` in `test_auth_registration_api.py` | Function-level pytest fixtures; generated registration emails use UUIDs. | The email cleanup queries that exact email, deletes only the matching row if present, and commits. Successful registration cases commit before teardown. No enclosing rollback; a failed setup/teardown can leave synthetic rows. |
| `registered_user` in `test_auth_login_api.py` and `test_current_user_security.py` | Function-level helper/fixture creates an account through the API using a unique email. | Cleanup selects/deletes the exact generated user and commits. Inactive-user coverage updates the generated user and commits before cleanup. No suite-wide transaction rollback. |
| `authenticated_as`, `temporary_project`, `temporary_project_workflow` in `test_projects_api.py` | Function-level context managers insert synthetic users/projects and, for workflow cases, requirements, stories, tasks and/or sprints. IDs/emails are generally generated. | Setup commits; teardown selects generated IDs and commits targeted deletion, usually deleting the root project and relying on relationship/FK cascades for children. No rollback wrapper. Some test cases use fixed UUID identifiers, so collision with extant records is possible. |
| `create_user`, `authenticated_as`, `temporary_users` in `test_admin_users_api.py` | Helpers create users and mutate roles/activation for those test users. | Helpers commit and delete captured generated IDs, but several last-admin/concurrent-admin cases assert global active-admin state. Existing user roles and state can therefore change expected outcomes. |
| `prepare_story`, `prepare_editor` in `test_user_story_approval_api.py` | Context managers create project → requirement → story and optional user; editor helper creates BA. | Setup and teardown each commit. Teardown deletes the test project and user by captured IDs. Cascades remove project children, but audit FK behavior preserves audit rows with nullable live FKs and snapshot IDs. |
| Database connection fixtures/helpers in the API modules | Direct `SessionLocal` sessions are opened by fixtures, helpers, and tests. | Independent sessions and explicit commits mean an outer test transaction cannot automatically roll all changes back. No common transaction fixture was found in the inspected setup. |
| `test_database.py` | Direct database connectivity/identity checks. | Read-only queries, but it opens a real connection to the configured target. It is not safe to classify as database-independent. |
| `test_role_permissions.py`, `test_test_database_safety.py`, `test_render_free_deployment_configuration.py` | Pure role/helper, in-memory guard, and static YAML/source tests respectively. | No PostgreSQL fixture required. The Render test mocks process execution. These are the safest existing modules to execute without touching the populated database, although execution was not authorized here. |

The guard in `backend/app/test_database_safety.py` protects against accidental use of a non-approved configured endpoint, but its fixed target is the existing `127.0.0.1:55432 / ai_bap_test / ai_bap_test_user`. It is not proof that the target is empty, disposable, or isolated from records already in that database.

## 6. Database Write and Cleanup Inventory

| Operation | Location / behavior | Assessment |
|---|---|---|
| `SessionLocal.add()` / `commit()` for synthetic auth users | Registration, login/current-user, admin helpers. Generated emails or IDs are normally unique; successful cases persist before cleanup. | **Conditionally safe**: cleanup is selective, but commits are durable and failures may leave rows. Not rollback-isolated. |
| Exact-email or exact-ID `delete()` plus `commit()` | Auth/admin fixture cleanup. | **Conditionally safe**: predicates target fixture-created identities; identity uniqueness and cleanup completion are assumptions that should be checked. No broad delete was identified in these fixtures. |
| Project/requirement/story/task/sprint inserts and commits | `temporary_project*` in project tests and `prepare_story` in approval tests. | **Conditionally safe**: synthetic records are created, but persistent commits occur and some test IDs are fixed. Existing data is not globally cleared. |
| Root project deletion with cascades | Project/approval fixture teardown. ORM relationships use delete-orphan/cascade; project and requirement/story FKs cascade to child records. | **Conditionally safe** for the captured synthetic root ID, but unsafe if an ID collision causes a fixture to select an existing project. Cascades can delete that project's children. |
| Approval endpoint audit insertion | Approval/rejection tests create `user_story_approval_audits` rows. Model FKs use `ON DELETE SET NULL` for story/actor references and snapshot fields preserve the historical IDs. | **Conditionally safe for test correctness; persistent side effect by design**. Audit rows survive fixture cleanup, increasing the durable audit count. They are not removed by the fixture. |
| Fixed UUID-based project/story fixtures | Portions of `test_projects_api.py` use literal UUIDs for traceability cases. | **Conditionally safe / collision risk**: a pre-existing row with the same identifier can cause constraint failures or make a test act on the wrong record, depending on the test path. No collision check is a general guarantee. |
| `create_all` / `drop_all`, TRUNCATE, broad DELETE, DROP schema/database | No such broad operation was identified in the inspected requested test/fixture paths. | **Not verified absent from every transitive runtime path**; importantly, no suite-wide rollback strategy was found. No Alembic migration is invoked by these selected fixtures. |
| Alembic guard helpers | `backend/app/test_database_safety.py` includes guarded environment setup for migration validation. | Static helper only in the reviewed test-safety module; do not run a migration test against this populated DB as part of a first preservation-sensitive pass. |

Approval audit evidence is especially important: `test_audit_snapshots_survive_user_and_story_deletion` and `test_audit_history_survives_story_and_actor_deletion` explicitly assert that history remains after temporary records are deleted. Their tests create committed audit rows that survive cleanup. Consequently, running these tests against the supplied DB would intentionally change its 43-row audit history even when the tests pass.

## 7. Existing 50-Record Preservation Analysis

| Existing data | Risk from running relevant integration tests unchanged |
|---|---|
| 2 users | Most helpers use unique generated emails and target their own IDs for cleanup. However, admin tests inspect or mutate global administrator counts/state; unknown existing roles can cause failures or alter assumptions. A fixture ID/email collision is low-probability, not impossible. |
| 1 project | Project and approval test list/read paths can observe shared rows. Teardown deletes by captured ID and may cascade; fixed-ID collision could expose the existing project to fixture cleanup. No test-level transaction protects the row. |
| 1 requirement | Project/story fixture cascade can remove child requirements if a root project collision occurs. Otherwise generated fixtures are targeted. |
| 2 user stories | Story fixtures generally create generated rows; cascade cleanup under project deletion could remove stories belonging to a colliding existing project. |
| 43 approval audits | Audit tests add persistent rows by design; deleting story/user sets live FK references null but retains audit snapshots. Baseline count is therefore expected to increase if those tests run. No fixture cleanup deletes the new audit rows. |
| Alembic version row | Reviewed fixture setup does not run migrations. Migration validation would alter migration state only if the schema is behind or migration is explicitly invoked; that is outside this run's safe subset. |
| 0 sprints / 0 tasks | Project-workflow fixtures may insert and cascade-delete synthetic rows. A root project collision could make cascades affect existing children; otherwise exact captured parent cleanup is intended. |

The code uses direct commits, not transaction rollback. It therefore does not establish a proof that pre-existing rows are untouched under every failure/collision path. The database name and host-side counts do not establish that the contents are disposable. Whole-suite execution against this database is **NO-GO** under a requirement to preserve unknown existing records. Approval/audit tests are specifically unsuitable because persistent audit rows are part of their expected behavior.

## 8. Test Safety Matrix

| Module | DB dependency | Writes / cleanup | Existing-data risk | Safe to run unchanged? | Recommendation |
|---|---|---|---|---|---|
| `test_auth_registration_api.py` | Yes for integration cases; some cases use fake DB. | Registration persists users; exact-email cleanup commits. | Residual rows on interruption; fixed emails are limited to mock cases; DB integration assumes guarded target. | **Conditionally safe** | Not against this unknown populated DB until isolated target/cleanup behavior is approved. Mock-only subset may be DB-free if precisely selected. |
| `test_auth_login_api.py` | Yes | Unique user create/update/delete with commits. | May leave a user on teardown failure; touches account state only by generated identity. | **Conditionally safe** | Prefer fresh isolated DB; not proven zero-impact on current database. |
| `test_current_user_security.py` | Yes | Same unique-user lifecycle; inactive state update commits. | Residual fixture user on failure. | **Conditionally safe** | Fresh isolated DB preferred. |
| `test_role_permissions.py` | No DB fixture in module | In-memory role objects / permission functions. | None identified. | **Safe** | Can run independently without PostgreSQL, subject to separate execution authorization. |
| `test_projects_api.py` | Yes | Inserts/commits projects and related resources; selective cascade cleanup; fixed UUID cases exist. | ID collision, project-list visibility, cascade effects, residue on failure. | **Conditionally safe (elevated risk)** | Do not run against current DB. Run only on fresh isolated DB or a carefully approved, uniquely isolated schema/database. |
| `test_admin_users_api.py` | Yes | Synthetic users with commits; role/activation changes; exact-ID cleanup. | Global last-active-admin/concurrency assertions depend on existing users; unexpected role changes may alter behavior. | **Conditionally safe (elevated risk)** | Do not run on current DB without understanding user roles/state; use fresh isolated DB. |
| `test_database.py` | Yes, read-only | Connection and identity SELECTs. | No intended row writes, but connects to configured DB. | **Conditionally safe** | Only after endpoint guard verification; does not mutate data as written, but no connection was made here. |
| `test_test_database_safety.py` | No DB connection | In-memory environment dictionaries and fake settings. | None identified. | **Safe** | Appropriate DB-independent test candidate. |
| `test_render_free_deployment_configuration.py` | No DB connection | YAML/source parsing; subprocess/exec mocked. | None identified. | **Safe** | Appropriate DB-independent test candidate. |

The registration/login/current-user/project/admin modules are not covered by a shared rollback fixture. “Conditionally safe” does not mean safe to run against this particular populated database; it means their intended record cleanup is scoped but not a full data-preservation guarantee.

## 9. Credential Exposure and Rotation Considerations

The test connection obtains its password through `AI_BAP_TEST_POSTGRES_PASSWORD`; `compose.test.yaml` requires that variable when initially creating the test service, and `docs/isolated-test-database.md` describes setting it in the current PowerShell process. The safety guard checks that required test variables exist and match its expected test configuration; the actual secret value is not reproduced here. The test configuration must be supplied through process environment, not committed files.

The previously exposed test password is compromised and must not be reused as a secret. Rotation can interrupt test access if the database role password, existing container configuration, and future client-process environment are not coordinated. No rotation was performed. A separately authorized rotation plan should: generate a new unique test-only password; update the PostgreSQL role and the authorized local secret source/process environment in a coordinated maintenance window; verify only against the isolated test endpoint; and ensure the old value is no longer used. Whether changing the role password also requires recreating/reconfiguring the container environment depends on the exact chosen method; do not recreate the persistent volume as part of rotation. Confirm the recovery path before proceeding.

## 10. Alternative Execution Strategies

| Option | Safety and risk to the existing 50 records | Changes / constraints | Assessment |
|---|---|---|---|
| **A — Run against current `ai_bap_test`** | Highest risk: existing rows are unknown; fixture commits are durable; audit history intentionally persists; admin global-state tests and fixed UUID cases can interact with baseline. | No source change, but selective test choice cannot remove every residual/collision risk. Requires a known baseline and explicit acceptance of persistent synthetic audit rows. | **NO-GO for database-backed regression suite** under the stated preserve-existing-records requirement. Pure DB-free modules are separable. |
| **B — Separate fresh disposable database/schema and credentials** | Best isolation; no pre-existing records to damage, provided target is uniquely provisioned and verified. | Current safety guard appears fixed to port 55432/database `ai_bap_test`, already occupied by a persistent-volume container. A new endpoint/schema likely requires separately approved guard/test-harness support or a separately controlled environment. Fresh schema on same server is not automatically safe unless credentials and target checks prevent crossing schemas. | **Recommended** after a separate authorization for isolated topology and any minimal guard support. |
| **C — Transaction-level isolation on current database** | In theory rollback can protect inserted/updated test rows, but current helpers open independent `SessionLocal` sessions and commit directly; audit behavior is designed to persist. | Would require a shared externally bound transaction/session fixture and changing helper/test behavior, which is not authorized here and is not established by current fixture design. | **Not available as-is; not recommended** for current DB. |

## 11. Acceptance Criteria Matrix

| Criterion | Status | Evidence / note |
|---|---|---|
| AC-01 All relevant fixture dependencies inspected | PASS | Requested modules plus approval API/audit dependency inspected statically. |
| AC-02 Database write and cleanup operations mapped | PASS | Commit, targeted delete, cascade and persistent audit behavior summarized above. |
| AC-03 Risks to existing 50 records evaluated | PASS | Supplied counts considered; contents not presumed disposable. |
| AC-04 Authentication/JWT test safety assessed | PASS | Auth/login/current-user fixtures create and commit generated users; no common rollback. |
| AC-05 RBAC test safety assessed | PASS | Role permission unit module is DB-free; admin API tests are DB-backed and globally state-sensitive. |
| AC-06 Project persistence test safety assessed | PASS | Project fixtures commit; selective cascade cleanup and fixed-ID risk identified. |
| AC-07 Admin authorization test safety assessed | PASS | Generated-user cleanup and global admin-state assertions identified. |
| AC-08 Pure configuration tests distinguished | PASS | Test DB guard and Render config modules are static/in-memory and DB-free. |
| AC-09 Credential exposure documented without revealing password | PASS | Compromise and rotation implications stated; no value printed. |
| AC-10 Safest next execution strategy identified | PASS | Fresh isolated target recommended; current DB not approved for suite. |
| AC-11 No tests executed | PASS | No pytest or other test command run. |
| AC-12 No PostgreSQL connection or SQL execution | PASS | No DB client, application connection, or SQL query used. |
| AC-13 No application/test/config source changed | PASS | Only this authorized report created. |
| AC-14 No Docker resource changed | PASS | No Docker command or resource operation performed. |
| AC-15 No Git/GitHub/cloud mutation | PASS | Read-only Git status only; no remote/cloud action. |

## 12. Residual Risks

- Existing rows’ identity, ownership, role, and intended retention are unknown; the supplied aggregate counts cannot establish synthetic status.
- Test fixtures use durable commits and cleanup code; process interruption, assertion failure before teardown, or cleanup failure may leave synthetic rows.
- Approval audit records are intentionally durable. Running those tests changes the persistent audit count even when all fixtures clean up correctly.
- Fixed UUID test data may collide with existing records.
- Admin “last active admin” tests may produce false failures or affect role state depending on the two existing users.
- A database-level uniqueness/foreign-key collision or unexpected cascade could fail mid-test; no rollback wrapper guarantees restoration.
- The test password is compromised; no rotation was performed or verified.
- This is static source analysis plus supplied host evidence. Runtime behavior, exact existing row content, and current resource state were not independently revalidated.

## 13. Git and Resource Preservation Verification

Read-only Git baseline and final checks observed:

- Remote: `origin` points to `https://github.com/imend35/ai-bap.git`.
- Branch: `docs/ci-pr-evidence`.
- HEAD: `f6fff10898fc9a7c3d56a303fba7f50a1b1715e2`.
- Index: empty.
- Existing modified and untracked paths were preserved; no prior path was edited by this step.
- `docs/codex-reports/adm_8.10.201.md` was absent before this step and is the only path created by this step.
- No test, DB/SQL, Docker, Git mutation, GitHub mutation, cloud provisioning, or deployment was performed.

The host-side database counts and container health are accepted from the Human Product Owner’s supplied evidence; this audit did not independently inspect the container or records.

## 14. GO / NO-GO Decision

**NO-GO** for running the database-backed regression suite against the current populated `ai_bap_test` database while preserving all existing records. The fixtures commit changes directly, no common rollback boundary exists, approval-audit rows intentionally survive cleanup, and existing IDs/user state are not known. The targeted cleanup patterns reduce ordinary overlap risk but do not provide a sufficient preservation guarantee for these 50 records.

**GO for a separately authorized future plan** to run against a fresh, independently verified disposable database with unique credentials and a guard that demonstrably targets only that disposable database. Pure DB-free role, test-safety, and Render configuration tests are statically identified as candidates, but none were executed here.

## 15. Recommended SINGLE Next Step

Request separate Human Product Owner approval for a fresh isolated test-database execution plan that avoids the existing 50-record volume and first resolves the test guard’s fixed-target constraint; include credential rotation for the exposed test password in that approval plan before any database-backed test run.
