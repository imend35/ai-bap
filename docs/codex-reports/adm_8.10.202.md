# ADIM 8.10.202 — Fresh Isolated PostgreSQL Test Environment: Design & Safety Plan

## 1. Step Name and Objective

Design a separately authorized, disposable PostgreSQL environment for the AI BAP database-backed regression suite. The design preserves the existing populated `ai_bap_test` database and its volume and prevents test execution from selecting that database accidentally.

## 2. Human Product Owner Authorization

Authorization for this step was read-only analysis and one design report only. No test, SQL, database connection, migration, Docker operation, credential operation, code/configuration edit, Git/GitHub mutation, or deployment was authorized or performed.

## 3. Verified Existing Environment

The following values are supplied as Human Product Owner-verified host evidence and were not rechecked in this step:

| Resource | Existing value / state |
|---|---|
| Compose project / service / container | `ai-bap-test` / `db-test` / `ai-bap-test-db-test-1` |
| PostgreSQL | 16.13, running and healthy |
| Host binding | `127.0.0.1:55432` |
| Database / role | `ai_bap_test` / `ai_bap_test_user` |
| Persistent volume | `ai-bap-test_ai_bap_test_data` |
| Rows reported | 2 users; 1 project; 1 requirement; 2 stories; 43 approval audits; 0 sprints; 0 tasks; 1 Alembic row; 50 total |

These 50 rows are protected as an invariant. They are not assumed to be synthetic or disposable. No connection was made to the existing database.

## 4. Repository and Guard Findings

Read `AGENTS.md`, prior reports `adm_8.10.197.md` through `adm_8.10.201.md`, and the requested test, database-safety, Compose, documentation, and settings files. Relevant additional reuse points inspected were `scripts/test-all.ps1`, `backend/scripts/run_isolated_test_alembic.py`, `backend/scripts/validate_legacy_record_number_migration.py`, `backend/scripts/seed_legacy_record_number_fixture.py`, and `backend/migrations/env.py`.

The current guard in `backend/app/test_database_safety.py` defines hard-coded tuples for the regular test target (`127.0.0.1:55432`, `ai_bap_test`, `ai_bap_test_user`) and the separately named legacy target (`127.0.0.1:55433`, `ai_bap_legacy_test`, `ai_bap_legacy_test_user`). It requires `AI_BAP_TEST_MODE=true`, a target-specific confirmation, a matching secret process variable and `POSTGRES_PASSWORD`, then reapplies the tuple to the process environment. It does not accept arbitrary host/database overrides.

`backend/tests/conftest.py` invokes the regular guard at import before test modules, then enables registration for that process. The current tuple is therefore used by pytest. `backend/scripts/run_isolated_test_alembic.py` calls `configure_guarded_alembic_database_environment()`, loads effective settings, validates the effective SQLAlchemy URL, and only then invokes Alembic. The legacy migration validator/seeder also consume the legacy tuple/selector. `scripts/test-all.ps1` separately duplicates the regular fixed tuple for its integration-test gate. `backend/migrations/env.py` itself builds its URL from settings and is not independently guarded; only the approved wrapper should be used for test migrations.

Settings in `backend/app/config.py` derive the normal URL from `POSTGRES_*`, but a `DATABASE_URL` environment/config override takes precedence. The Alembic wrapper validates its effective URL; pytest’s import-time guard currently validates/reapplies the tuple but does not independently validate an effective `DATABASE_URL`-derived engine URL. The proposed pytest extension must fail closed on an override or validate the effective URL before any database engine can be used. Production settings must remain unchanged.

## 5. Proposed Isolation Architecture

Use a new, dedicated Compose project and PostgreSQL 16 container for this test run, with a distinct database, role, password, and loopback-only port. Prefer a **container-writable-layer-only database with no named or bind-mounted data volume** for this disposable run. This makes the data lifetime explicit: it exists only in the uniquely named container and is discarded only after a separately approved, identity-checked removal. Do not reference, mount, rename, stop, or otherwise operate on the existing Compose project or volume.

The host test process and the container must both use a new allowlisted target tuple. Before any connection, a guard must verify the configured target and then verify the actual connected server identity (`current_database`, `current_user`, and loopback endpoint) against that tuple. Fail on missing, malformed, partial, or conflicting configuration. Keep `AI_BAP_TEST_MODE` opt-in and require a separate exact confirmation value for this new disposable target.

## 6. Proposed Resource Names and Boundaries

Proposed names below are design values only; they do not currently exist and were not created:

| Resource | Proposed value |
|---|---|
| Compose project | `ai-bap-regression-disposable-20261024-a202` |
| Compose service | `db` |
| Expected Compose container | `ai-bap-regression-disposable-20261024-a202-db-1` |
| Database | `ai_bap_regression_20261024` |
| Runtime test role | `ai_bap_regression_user_20261024` |
| Host publish | `127.0.0.1:55434` → container `5432` |
| Data volume | None; disposable container layer only |
| Image | PostgreSQL 16, pinned to a verified tag/digest at implementation time |

Before provisioning, check that the exact proposed project/container names and host port are unused. If any is occupied or the identity is ambiguous, stop and choose a new unique suffix under separate approval. Compose labels must identify the project and service. No Compose file may refer to `ai-bap-test_ai_bap_test_data` or the existing container. A no-volume design means a container replacement loses its DB; this is intentional and must be documented before tests.

## 7. Fail-Closed Guard Extension Design

The smallest coherent extension is to add one named disposable-test target to the central guard allowlist, not to permit arbitrary environment-supplied endpoints.

Proposed selectors/configuration:

- `AI_BAP_TEST_MODE=true` — existing explicit test-only opt-in remains mandatory.
- `AI_BAP_TEST_TARGET=disposable-regression` — new exact target selector; no default to the new target.
- `AI_BAP_DISPOSABLE_TEST_DATABASE_CONFIRMATION=<new fixed acknowledgement>` — distinct explicit confirmation, never shared with the existing target.
- `AI_BAP_DISPOSABLE_TEST_POSTGRES_PASSWORD` — unique secret supplied in the current process only; `POSTGRES_PASSWORD` must match it for application settings.
- `POSTGRES_HOST=127.0.0.1`, `POSTGRES_PORT=55434`, `POSTGRES_DB=ai_bap_regression_20261024`, `POSTGRES_USER=ai_bap_regression_user_20261024` — exact target tuple in a centralized allowlist.
- `DATABASE_URL` — reject if set for pytest, or construct/validate the effective Settings URL before the engine is imported; never let it silently override the allowlisted tuple. Also check for a `.env`-sourced override by validating the effective settings object.

Validation rules:

1. Accept only the exact selector and exact acknowledgment; reject missing, unknown, partial, mixed legacy/current, or conflicting values.
2. Require host exactly `127.0.0.1`; reject hostnames (including `localhost`), IPv6/remote hosts, wildcards, and non-allowlisted ports.
3. Require database and username to equal the allowlisted tuple; explicitly reject `ai_bap`, `ai_bap_test`, `ai_bap_legacy_test`, their production roles, and every other unapproved tuple.
4. Require non-empty, unique test-only secret input and matching application password variable without logging it. Do not echo secrets in exceptions.
5. Validate both the selected tuple and effective SQLAlchemy URL before pytest can initialize `SessionLocal` or Alembic can run. For Alembic use the existing guarded wrapper; never call raw `alembic upgrade` for this environment.
6. Once connected, verify database/user/server identity before any schema inspection or write. Any mismatch aborts before test code.
7. Never change `Settings` defaults or production guards to accommodate tests.

The central target mapping and target-aware configuration would be in `backend/app/test_database_safety.py`; pytest startup/effective-URL validation in `backend/tests/conftest.py`; guard unit cases in `backend/tests/test_test_database_safety.py`; and the duplicate tuple/selector check in `scripts/test-all.ps1`. The existing Alembic wrapper should route the new selector through the same central allowlist and effective URL validator. Review legacy migration validator/seeder behavior to ensure the new selector cannot accidentally widen their target; do not make those specialized scripts accept the disposable target unless explicitly required. No changes to `backend/app/config.py` production defaults are intended.

Required new guard tests include: accept the exact complete disposable tuple; reject missing selector/confirmation; reject partial/mixed values; reject wrong host, port, database, username, role, and password mismatch; reject existing application/legacy tuples under the new selector; reject `DATABASE_URL` override from process or settings file; reject unknown selector; and verify effective URL identity for regular, legacy, and new targets. Errors must be generic and secret-free.

## 8. Credential Isolation and Secret Handling

Generate a new high-entropy password only in a separately approved provisioning step. Never reuse the compromised existing test password. Do not put secrets in Git, Markdown, command-line arguments, public URLs, browser bundles, or logged Compose output.

For the PostgreSQL container, use the official image’s `POSTGRES_PASSWORD_FILE` mechanism backed by a temporary, owner-restricted secret file outside the repository (or an equivalently protected local secret source). The Compose configuration contains only the secret-file path, not the password. Keep file ACLs restrictive and the file available only for the lifetime needed by the container; removal is an explicit, identity-checked action. The host pytest process receives the new runtime-role password as a process-scoped environment value (and matching `POSTGRES_PASSWORD`) entered without echo or command-history persistence. Do not print environment values or pass the password as a CLI argument. Any unavoidable process-memory exposure is limited to the authorized local user/process and should be acknowledged.

Use a one-time bootstrap identity only to initialize the isolated container. Prefer creating a distinct non-superuser runtime test role that owns only the disposable database/schema, then run migrations and tests as that role. Store bootstrap and runtime secrets separately. The bootstrap role must not be used by pytest. Revoke unnecessary database access from `PUBLIC`, grant only target DB/schema privileges needed for Alembic and tests, and keep both credentials local-only. No secrets were generated or accessed in this design step.

## 9. Existing Credential Rotation Plan

The exposed password for `ai_bap_test_user` remains compromised and was not rotated. Rotation is **a separate security task**, not a prerequisite for creating a wholly separate disposable environment with a new unique role/password; however, the compromised credential should not be used for the new environment and should be rotated before the existing test database is used again.

Separately authorized rotation sequence:

1. Inventory which local client processes/configuration need the existing database role; do not expose values in logs or reports.
2. Confirm an owner-approved recovery path and maintenance window. Preserve the existing named volume and take no destructive action.
3. Generate a new unique secret through a secure channel; coordinate the PostgreSQL role password change with the authorized local secret/process configuration. Do not place it in a tracked file or command argument.
4. Update any persistent container/client secret configuration using a method that does not delete or recreate the volume. The image’s initialization password environment/file is not automatically a live role-password rotation mechanism for an already initialized cluster; changing the database role and updating client configuration must be handled deliberately.
5. Verify new authentication against only `127.0.0.1:55432/ai_bap_test` using the intended role without querying or exposing application rows; then verify the old credential no longer authenticates without printing either value.
6. If new authentication fails, use the approved administrative recovery identity and restore client configuration safely. Do not delete the volume, reset the database, or recreate the container as a shortcut.
7. Revoke/remove old secret copies from authorized process stores and ensure future documentation does not repeat them.

## 10. Migration and Schema Initialization Plan

Only the new empty database is eligible for schema initialization:

1. Confirm exact container labels/name, loopback mapping, DB, role, and isolated Compose project before connecting.
2. Wait for PostgreSQL health/readiness; do not treat container `running` alone as ready.
3. Verify server-side identity (`current_database`, `current_user`, server address/port) against the new allowlist before DDL.
4. Confirm the database is empty of application tables and has no pre-existing Alembic version row. If not empty or identity differs, stop; never drop objects to make it fit.
5. Run only the guarded `backend/scripts/run_isolated_test_alembic.py upgrade head` path after target approval. The wrapper must validate the effective URL and exact target before invoking Alembic.
6. Verify `alembic_version` is at the expected head and required tables exist; collect only schema/table/revision metadata.
7. A repeated `upgrade head` may be considered only after confirming the same disposable target identity and normal Alembic idempotent-upgrade behavior. Never downgrade or use unguarded Alembic.
8. On migration failure, stop tests and preserve the container/logs for diagnosis. Do not drop/reinitialize automatically.

## 11. Ordered Regression Test Strategy

All phases are design only. At each phase, any target-identity mismatch, unexpected non-test data, schema drift, fixture collision, cleanup failure, or unexplained count increase stops the run. Capture command, exit code, test counts, target identity (no credentials), and before/after aggregate counts. Never capture secret values or application row contents.

| Phase | Preconditions and execution | Expected effects / evidence | Stop condition |
|---|---|---|---|
| **A — DB-independent guard/config tests** | Fresh process; run `test_test_database_safety.py`, role unit tests, Render/static config tests without importing DB-backed suites unnecessarily. | No DB connection; record per-module counts and exit codes. | Any unexpected database fixture/import or environment mutation beyond process scope. |
| **B — New target identity/connectivity** | Provisioned container approved; verify exact name/labels/loopback port and test tuple; run the narrow identity check. | Connection only to new empty DB; record database/user/server identity, schema/table inventory, zero app rows before migrations. | Any mismatch, pre-existing application rows, or connection not loopback. |
| **C — Authentication and JWT** | Migration complete; identity reverified; unique synthetic identities. Run registration, login, current-user/JWT modules. | User inserts/updates and selective cleanup; capture pass counts and before/after user counts. | Existing test identity collision, cleanup failure, residual unexpected users, token/security assertion failure. |
| **D — RBAC and admin** | Fresh DB and known seed/admin fixture state. Run role helper and admin authorization modules. | Synthetic users and role state; admin global-state assertions begin from controlled empty/explicit seed. | Unknown account state, unexpected admin count, concurrent-state inconsistency. |
| **E — Project persistence/workflows** | Fresh DB, unique identifiers, migrations verified. Run project API/persistence modules. | Projects and child resources inserted and selectively removed; audit table may grow where workflow creates events. Capture table counts, not row contents. | Fixed-ID collision, unexpected cascade, failed cleanup, or new fixture affecting existing data. |
| **F — Story approval/audit** | Fresh DB; explicitly accept audit persistence; capture pre-test audit count. | Approval/rejection audit rows intentionally remain; verify snapshots/FK-null behavior. Record exact count delta and confirm all rows are synthetic by test-run provenance, not content dumps. | Count delta unexplained, missing snapshots, or any unrelated target identity. Do not clean audit records individually. |
| **G — Full relevant regression suite** | Only after A–F pass and suite target is centrally guarded; keep same disposable target for this run. | Aggregate result and final schema/count summary; preserve logs until owner decides resource lifecycle. | Any failure, skipped safety gate, unexpected state, or absent evidence. No automatic rerun or cleanup. |

## 12. Audit Persistence and Cleanup Strategy

Approval tests create audit rows that intentionally outlive temporary story/user records. Existing audit rows should remain; the new disposable database starts at zero, so baseline and post-phase audit counts can be compared without touching the 43 rows in the existing database. FK `ON DELETE SET NULL` removes live actor/story references while immutable snapshot IDs remain. This is expected test behavior, not a cleanup defect.

Do not manually delete audit rows or alter audit semantics to force a zero count. Repeatability comes from a fresh run-specific container/database, not from truncating a shared test database. Keep the container and its no-volume data until test output, identity, aggregate counts, and failure diagnostics have been reviewed. Removal of the exact new container is optional, separately authorized, and only after evidence capture; no broad Compose/Docker cleanup. If any records are unexpectedly left in a persistent test setup, stop and investigate rather than assuming they are safe to clear.

## 13. Windows Host Execution Strategy

The repository environment is Windows 11, PowerShell, Docker Desktop/WSL2, Python 3.13. Prior reports describe Docker named-pipe access being denied from the Codex sandbox while Docker Desktop was healthy in the authorized host context. Do not assume Codex can inspect or control Docker.

Recommended split:

1. Codex, under separately approved implementation scope, proposes/edits only the guard, tests, Compose definition, and docs; local static tests that do not reach PostgreSQL are separately authorized.
2. Human Product Owner reviews the exact diff and separately approves host-side Docker provisioning and secret handling.
3. Human runs approved PowerShell/Docker commands in the host context, checks labels/port/health, and sends sanitized output (no secrets, connection strings, or row data) back to Codex.
4. Human separately approves target identity check, migration, each database-backed test phase, and any cleanup. Codex does not elevate sandbox access or switch contexts.

No step authorizes a cloud service or paid resource.

## 14. Alternatives and Trade-Offs

| Option | Isolation / risk to existing 50 rows | Guard compatibility / effort | Cleanup and Windows practicality | Assessment |
|---|---|---|---|---|
| **A — New Compose project, dedicated PostgreSQL container, no data volume** | Strongest local boundary; separate server, port, DB, role; no mount path to existing volume. Existing 50 rows are not targeted. | Requires a new allowlisted target plus Compose/service/doc/test-script wiring. Moderate effort (M, roughly 1–3 hours, estimate only). | Host PowerShell needed for Docker named-pipe access; disposable container lifecycle is clear; exact identity checks required before removal. | **Recommended.** Safest and feasible before the deadline subject to host access and separate approvals. |
| **B — New database on existing PostgreSQL server** | Separate DB/role reduces ordinary cross-database access, but shares server, administrator, port, and operational context. Mis-targeting or privileged credentials could reach existing data. | Guard can add another tuple, but a new DB/role must be provisioned on the existing persistent container; higher blast radius and more complex ownership. | No new Docker container; cleanup is database-destructive and requires a separate approved lifecycle. | **Not preferred** while the existing server and database must remain untouched. |
| **C — Isolated schema in existing database** | Weakest boundary: same database and cluster; schema/search-path/privilege mistakes may expose existing objects; migration/application code expects its own schema behavior. | Likely needs schema-aware URL/session/migration support beyond the existing tuple guard; higher implementation/testing complexity. | No new port/container, but schema deletion/cleanup risks shared DB and audit objects. | **Reject for this use case.** It does not provide an adequate operational separation. |

## 15. Proposed Implementation Sequence

1. **Design approval** — approve Option A, the no-volume disposable lifecycle, target names, and guard rules. No files/resources yet.
2. **Minimal source/config implementation** — separately authorize changes to `backend/app/test_database_safety.py`, `backend/tests/conftest.py`, `backend/tests/test_test_database_safety.py`, `scripts/test-all.ps1`, a new `compose.regression-test.yaml`, and `docs/isolated-test-database.md`. Keep production defaults and migration files unchanged. Add the target selector/effective-URL checks and negative tests.
3. **Static validation** — separately authorize pure guard/config tests and lint; verify no DB connections occur in those commands. Review diff and output before host work.
4. **Credential plan** — separately authorize generation/storage of unique bootstrap/runtime secrets outside Git. Existing password rotation remains a separate security task; no secret reuse.
5. **Host Docker provisioning** — Human-only, separately authorized. Verify project, container, port, absence of volume mounts, image, labels, and health; stop if name/port conflict.
6. **New target identity verification** — separately authorize one connection to the new DB, read-only identity/schema checks only; stop on any mismatch/nonempty unexpected schema.
7. **New database migration** — separately authorize guarded Alembic upgrade to head against the new target only; verify revision and required tables.
8. **Controlled test execution** — separately approve each ordered phase A–G, capture counts and output, stop on unexpected residuals. No running against existing `ai_bap_test`.
9. **Evidence collection** — review sanitized outputs, command/exit/test counts, and before/after aggregate counts. Keep resource live until owner review.
10. **Optional resource cleanup** — separately authorize removal of only the exact new no-volume container/project after verifying identity and preserving evidence. Never remove or operate on the existing project/volume.
11. **Existing credential rotation** — separate security authorization and maintenance plan for the compromised `ai_bap_test_user` password; coordinate role/client changes while preserving the existing volume. This is not part of the new container provisioning authorization.

Stop conditions at every step: unexpected working-tree changes; target names/port already used; volume or mount overlap; non-loopback exposure; selector/confirmation mismatch; `DATABASE_URL` override mismatch; unexpected preexisting DB objects; migration target mismatch; test writes outside synthetic generated fixtures; unexplained audit/count changes; or any request requiring paid/cloud infrastructure.

## 16. Acceptance Criteria Matrix

| Criterion | Status | Evidence |
|---|---|---|
| AC-01 Existing 50-record DB preservation is invariant | PASS | Explicitly excluded from all proposed resource actions. |
| AC-02 New container/project/volume separation specified | PASS | Unique project/container; no named or bind volume proposed. |
| AC-03 New database and role specified | PASS | Distinct proposed DB and runtime role. |
| AC-04 Loopback-only port specified | PASS | Proposed `127.0.0.1:55434`. |
| AC-05 Fail-closed guard extension specified | PASS | Exact selector/allowlist/confirmation/effective URL/connected identity rules specified. |
| AC-06 Production safety not weakened | PASS | Production settings remain unchanged; test-only guard path only. |
| AC-07 Credential delivery/storage designed | PASS | Unique secrets, secret-file for initialization, process-only host secret, no logs/Git/args. |
| AC-08 Exposed password rotation plan documented | PASS | Separate coordinated role/client rotation with volume-preserving recovery. |
| AC-09 Safe migration strategy documented | PASS | Identity first, empty schema preflight, guarded wrapper, head/table verification. |
| AC-10 Ordered regression strategy documented | PASS | Phases A–G and stop/evidence conditions provided. |
| AC-11 Persistent audit side effects addressed | PASS | Audit rows expected to persist; no manual deletion; fresh DB per run. |
| AC-12 Resource cleanup boundaries documented | PASS | Exact-resource identity checks; no broad cleanup; owner approval required. |
| AC-13 Windows/PowerShell/Docker constraints addressed | PASS | Host-side owner execution and sanitized output split documented. |
| AC-14 Alternatives compared and recommendation given | PASS | A/B/C comparison; Option A recommended. |
| AC-15 No tests executed | PASS | None executed. |
| AC-16 No DB connection or SQL executed | PASS | None performed. |
| AC-17 No Docker resources created or modified | PASS | No Docker operation performed. |
| AC-18 No source/configuration files changed | PASS | Only this report created. |
| AC-19 No Git/GitHub/cloud mutation | PASS | Read-only Git inspection only. |
| AC-20 Only authorized Markdown report created | PASS | `docs/codex-reports/adm_8.10.202.md` only. |

## 17. Residual Risks and Stop Conditions

- Names and port in this report are proposed, not provisioned or confirmed free; host-side collision checks are mandatory.
- The current pytest guard’s fixed target and the duplicate tuple in `scripts/test-all.ps1` must both be updated consistently. A partial update would either block tests or create target ambiguity.
- `DATABASE_URL` overrides `POSTGRES_*` in application settings. Effective URL validation before engine creation is required for pytest as well as the existing Alembic wrapper.
- The existing `backend/migrations/env.py` can be invoked without the guarded wrapper; only the guarded wrapper is acceptable for this test target.
- Container-layer-only data is intentionally ephemeral. Preserve test logs/output before any separately authorized container removal.
- Approval tests intentionally add durable synthetic audit rows. This is acceptable only inside the run-specific disposable database.
- The exposed existing test password remains compromised until a separately authorized rotation is completed. New credentials must be unrelated.
- Docker Desktop/WSL host access may not be available from the Codex sandbox; do not bypass the boundary with privilege escalation or context changes.
- No tests, migrations, connection checks, port checks, Docker inspection, or credential operation were performed here; all runtime suitability remains unverified.

## 18. Git and Resource Preservation Verification

Read-only checks observed branch `docs/ci-pr-evidence`, HEAD `f6fff10898fc9a7c3d56a303fba7f50a1b1715e2`, and an empty index. Existing modifications and untracked paths were preserved. The report target did not exist before this step and is the only file created. No test, SQL/database, Docker, Git/GitHub, cloud, or deployment operation occurred. Host resource identity remains based on supplied evidence; it was not independently rechecked.

## 19. Recommended SINGLE Next Step

Request Human Product Owner approval for **Option A’s minimal test-only guard/Compose design**, including the exact disposable target, `DATABASE_URL` fail-closed validation, and separate secret handling. Do not provision or run tests until that design-specific implementation approval is granted.
