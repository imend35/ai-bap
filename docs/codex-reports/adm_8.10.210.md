# ADIM 8.10.210 — Disposable PostgreSQL Provisioning Safety Plan

## 1. Step Name and Objective

This is a read-only, security-first plan for a future isolated PostgreSQL regression environment. It does not authorize or perform secret creation, Docker provisioning, database access, SQL, migrations, tests, cleanup, or deployment.

## 2. Human Product Owner Authorization

Authorization for this step is limited to repository/source review and creation of this plan. Each future state-changing phase remains separately approval-gated. No Docker daemon, PostgreSQL, credential, test, migration, Git/GitHub, or cloud operation was performed for this plan.

## 3. Repository and Git Baseline

The repository remote is `https://github.com/imend35/ai-bap.git`; branch is `docs/ci-pr-evidence`; HEAD is `f6fff10898fc9a7c3d56a303fba7f50a1b1715e2`. The Git index was empty. The initial working tree already contained 18 modified tracked paths, including the database guard, pytest setup, test module, `docs/isolated-test-database.md`, `scripts/test-all.ps1`, and other unrelated files. It also contained pre-existing untracked Codex reports, `compose.regression-test.yaml`, `frontend/e2e/`, and `frontend/playwright.config.ts`. These are preserved; this report is the only path created by this step.

`git diff --check` reported no whitespace errors. It emitted existing LF-to-CRLF conversion warnings for modified files; no line endings were changed.

## 4. Protected Existing Resources

Treat the following owner-identified resources as protected and out of scope: project `ai-bap-test`, container `ai-bap-test-db-test-1`, loopback port `55432`, database `ai_bap_test`, role `ai_bap_test_user`, volume `ai-bap-test_ai_bap_test_data` and the historical 50 records. Also protect the legacy target at `127.0.0.1:55433`, rubric container `ai-bap-rubric-test-db-1` at `127.0.0.1:55434`, and `ai-bap-db-1` at `127.0.0.1:5433`. No database, Docker resource, or credential was accessed.

## 5. Disposable Environment Identity

The proposed target, not provisioned or runtime-verified, is:

| Property | Exact proposed identity |
|---|---|
| Compose file / project | `compose.regression-test.yaml` / `ai-bap-regression-disposable-20261024-a202` |
| Service / expected container | `db` / `ai-bap-regression-disposable-20261024-a202-db-1` |
| Image | `postgres:16` |
| Host binding / container port | `127.0.0.1:55435` / `5432` |
| Database | `ai_bap_regression_20261024` |
| Bootstrap role | `ai_bap_regression_bootstrap_20261024` |
| Intended runtime role | `ai_bap_regression_user_20261024` |
| PGDATA | `/var/lib/postgresql/regression-data` |
| Bootstrap secret file in container | `/run/secrets/regression_bootstrap_password` |

Use both the explicit Compose file and project selector in any future authorized command, e.g. `docker compose --project-name ai-bap-regression-disposable-20261024-a202 --file compose.regression-test.yaml ...`. The project name in YAML is useful, but explicitly selecting it in every command reduces ambiguity. Do not rely on the current directory, implicit project naming, or another Compose file.

## 6. Static Compose Isolation Review

Static source inspection of `compose.regression-test.yaml` (lines 1–31) shows a distinct project name, service and fixed container name, `postgres:16`, restart policy `no`, target labels, the dedicated database/bootstrap role, secret-file reference, `PGDATA`, loopback-only `127.0.0.1:55435:5432` mapping, and `pg_isready` health check. No Compose `volumes:` entry, privileged mode, host networking, production fallback, or reference to the protected named volume is present.

This is configuration evidence only. It does not establish that the name or port is currently free, that Compose interpolation resolves safely on the host, that the container starts, or what mounts Docker creates. Before any future provisioning, repeat a read-only collision preflight for the exact project label, container name, port binding, networks and volumes. Stop on any collision; do not take ownership of or remove an existing object.

## 7. Bootstrap Secret Safety Plan

No secret was generated, read, or stored. For a separately approved Gate A, generate at least 256 bits from a cryptographically secure local random-number generator on the authorized Windows host. Encode as a PostgreSQL-compatible single-line ASCII value (for example, Base64URL without padding), with no quotes, whitespace, or line breaks. Write it without a BOM or appended newline to an owner-restricted file outside the repository, under a dedicated per-user local application-data directory. Do not place the value in a command argument, shell history, environment dump, transcript, screenshot, report, Git, README, URL, or frontend build.

Apply a restrictive Windows ACL so only the designated owner and necessary local system principals can read the file. Do not weaken ACLs for convenience. A future non-secret verification may confirm path existence, file ACL, expected nonzero size, and that the path resolves outside the repository without displaying file contents. Compose should receive only the file path through the process-scoped `AI_BAP_REGRESSION_BOOTSTRAP_SECRET_FILE`; the secret itself is consumed through `POSTGRES_PASSWORD_FILE`. Review shell transcription/logging settings before handling it. Gate A approves only creation and protection of the bootstrap secret—not container startup or role setup.

The runtime-role password must be distinct and independently generated/delivered under the later role-bootstrap/test approvals. Never reuse the previously exposed regular-test credential. The existing docs and test runner expect process-scoped runtime secret variables; do not persist them in `.env` or print them.

## 8. Anonymous Volume Analysis

The supplied historical host-side observation says local image metadata for `postgres:16` declared `VOLUME /var/lib/postgresql/data`, with image ID `sha256:71e27bf60b70bded003791b5573f8b808365613f341df20ffcf0c1ed7bc13ddf`. This step did not inspect Docker. There is an evidence discrepancy: `adm_8.10.206.md` records that daemon access was denied and image `Config.Volumes` was unavailable, whereas the current request provides later host-side observations. Accordingly, the image metadata is treated here as owner-supplied historical evidence, not independently reverified in this step; reconcile it with a new approved read-only host inspection before provisioning.

Image-declared `VOLUME` metadata is distinct from Compose's volume declarations. Docker may create an anonymous volume for an image-declared path even when Compose has no `volumes:` mapping. `PGDATA=/var/lib/postgresql/regression-data` is outside `/var/lib/postgresql/data`; setting it does not cancel the image declaration. Depending on the image entrypoint/runtime, the anonymous mount may be unused for database files, but that is not established by YAML. Actual mounts and their data use remain **NOT VERIFIED** until an authorized container exists and its exact mount metadata is read.

After Gate B and before Gate D/E, Gate C should capture the exact container ID and verify its Compose project/service/target labels, state, image ID, port bindings, and every mount. Read-only inspection should record each mount's `Type`, `Name`, `Source`, `Destination`, `Driver`, read/write status, and available volume labels (using exact volume identity only). An anonymous volume without ownership labels must not be attributed by its generated name alone; establish association from the exact inspected container mount. Stop on any unexpected mount or protected-volume reference. No such inspection occurred in this step.

## 9. Runtime Role and Privilege Plan

The Compose `POSTGRES_USER` initializes the bootstrap account and should be treated as privileged (the official image's initialization convention makes this account a superuser). It must never be the application/test account. The current Compose file provisions no runtime role, password, ownership, or grants; `docs/isolated-test-database.md` explicitly describes a future manual bootstrap, but executable least-privilege setup is a remaining implementation/procedure gap.

Under Gate D, use the bootstrap identity once, through an approved interactive/local method that does not put credentials in command history, to create the distinct runtime login. Make it non-superuser, non-CREATEDB, non-CREATEROLE, non-replication, and without bypass-RLS privileges. Scope database CONNECT and schema/table/sequence privileges to the disposable application database and required schema only. Give only the ownership/DDL rights needed by the approved migration/test workflow; do not grant cluster-wide administrative privileges. Keep bootstrap credentials out of normal app/test variables and remove them from the active session after bootstrap.

The strongest boundary here is a separate PostgreSQL container/cluster, not grants alone: PostgreSQL roles are cluster-scoped and ordinary `CONNECT` privileges can be granted to `PUBLIC`. Do not claim that a database role by itself cannot reach other databases on a shared server. The intended separate container and endpoint must be verified; tests must use only the runtime role and exact disposable target. No SQL or grants are specified/executed in this plan.

## 10. Migration Isolation Plan

Only after Gate C proves container/database identity and Gate D verifies the runtime role, Gate E may separately authorize migration. Require process-scoped `AI_BAP_TEST_MODE=true`, `AI_BAP_ALEMBIC_TARGET=disposable-regression`, `AI_BAP_TEST_TARGET=disposable-regression`, the exact disposable confirmation marker, exact host `127.0.0.1`, port `55435`, database and runtime username, and matching nonempty runtime password variables. Require no conflicting target selectors. Any `DATABASE_URL` or settings/dotenv-derived effective URL must parse and match the exact target tuple; reject malformed, mismatching, or ambiguous values before engine/Alembic use. Do not fall back to regular or legacy targets.

`backend/app/test_database_safety.py` contains the allowlisted regular, disposable and legacy tuples and URL validation (notably around lines 15–52 and 100–166, 240–295). `backend/scripts/run_isolated_test_alembic.py` validates target and effective settings before importing Alembic (lines 7–25). `backend/tests/conftest.py` applies the test guard and settings URL check before test-module imports (lines 1–32). Future migration must use only this wrapper, never raw Alembic. First perform an approved read-only identity/schema preflight; then migrate to head through the wrapper and verify the expected Alembic revision/tables. Stop before DDL on any identity discrepancy. No migration or database connection occurred now.

## 11. Regression Test Safety Plan

Gate F follows successful Gates B–E and a separately approved runtime identity/health/schema check. Supply only process-scoped settings for the exact disposable target, including `AI_BAP_TEST_MODE=true`, `AI_BAP_TEST_TARGET=disposable-regression`, its exact confirmation, the target tuple, and the runtime password duplicated only into the required matching variable. Ensure effective settings cannot redirect to another URL. The current `scripts/test-all.ps1` has a `disposable-regression` selection and validates the tuple/password (lines 1–4, 38–55, 78–87); it also runs frontend tests before backend target validation. Therefore, do not invoke it as a substitute for the preflight; complete all preconditions first and obtain approval for its full behavior, or authorize a narrowly scoped backend test command.

Run in phases: (1) database-independent guard/configuration checks; (2) read-only target identity/connectivity; (3) auth registration/login/JWT; (4) RBAC/admin authorization; (5) project list/create/retrieve/persistence; (6) story approval/audit; (7) only then the relevant combined regression suite. Capture command, exit code, counts, selected target identity (no credentials), migration revision, and aggregate before/after table counts. Stop on any mismatch, unexplained row change, guard rejection, health failure, test failure, or evidence of access to another target. Do not run against the populated regular database.

Approval/audit tests have a documented persistent side effect: audit rows intentionally survive deletion of synthetic story/user rows, with snapshot fields retained and some foreign keys set null. Use the fresh disposable database, record a pre-test count and expected row delta, and do not erase those audit rows to force a zero count. For a repeat run, a separately approved fresh disposable instance is safer than broad truncation/reset.

## 12. Cleanup and Rollback Plan

There is no automatic cleanup, including after failure. First preserve logs and sanitized evidence. Then request Gate G approval for each exact destructive action, after rechecking immutable container ID, Compose labels, project/service identity, mount associations, and protected-resource exclusion.

| Resource | Safe planning boundary |
|---|---|
| Container | Remove only the exact verified disposable container ID/name after separate approval; do not remove by wildcard or project guess. |
| Project network | Identify exact network ID and Compose labels; request separate approval before removal. |
| Named volume | None is declared by this Compose file. If one unexpectedly exists, stop and preserve it unless exact ownership and a separate removal approval are established. |
| Anonymous volume | Identify from the exact container's mount record; generated name alone is not ownership evidence. Separate approval is required before removal. Never target the protected volume. |
| Bootstrap secret file | Separate approval for deletion; verify exact outside-repository path and that it is no longer needed. Do not delete other secrets. |

Do not use `docker system prune`, `docker volume prune`, wildcard deletion, or `docker compose down -v`. Even plain Compose teardown can remove project-associated resources and therefore requires exact scope review and approval. A partial provision is not a reason for automatic teardown. Rollback means stop further phases, preserve evidence/resources, and seek a narrowly scoped owner decision.

## 13. Failure and Recovery Matrix

| Scenario | Detection and stop condition | Safe recovery proposal | Approval required |
|---|---|---|---|
| Port 55435 occupied | Host listener/binding found | Do not stop the owner process; choose a new port only after guard/config approval and a new preflight | Separate config and provisioning approval |
| Secret missing, unreadable, empty, or malformed | File/path/ACL/content-format preflight fails; never display content | Do not start Compose; correct the protected file only through approved secret handling | Gate A again; Gate B remains blocked |
| Compose project identity mismatch | Rendered/static identity or labels differ | Stop; do not operate on discovered resources | Gate B/C review |
| Container name collision or unexpected object | Exact name/ID exists before creation | Stop; inspect read-only and choose a newly approved unique identity; do not adopt/remove it | Separate identity/provision approval |
| Unexpected/anonymous mount or protected-volume reference | Gate C mount/source/labels do not match isolated expectation | Stop before credentials, migration or tests; preserve object and mounts | Gate C finding review; Gate G for any removal |
| PostgreSQL health check fails | Container health remains unhealthy or times out | Stop; collect sanitized diagnostics; do not rerun or rebuild automatically | Separate troubleshooting/provision approval |
| Runtime-role creation/grant failure | Approved bootstrap step does not verify least privilege | Do not use bootstrap account for tests; preserve database and request review | Gate D again |
| Alembic target mismatch/failure | Guard rejects selectors/URL or migration result is unexpected | Do not bypass guard or retry raw Alembic; preserve evidence | Gate E again |
| Test guard rejection or test failure | Guard/test output nonzero or unexpected database delta | Stop; do not weaken guard or run another target; capture sanitized evidence | Gate F review |
| Docker Desktop unavailable | Read-only CLI preflight fails | Stop; no elevation/context/WSL workaround under this plan | Separate host-operation authorization |
| Partial provisioning | Exact inventory shows some but not all expected resources | Preserve and inventory; do not auto-clean or retry | Gate C and, if needed, per-resource Gate G |
| Any unexpected existing project/volume/network | Labels/IDs do not prove exclusive disposable ownership | Stop; do not infer ownership from generated names | Human review before any action |

## 14. Human Approval Gates

Approval of this plan authorizes none of the following gates:

| Gate | Scope requiring fresh explicit approval | Evidence/stop condition |
|---|---|---|
| A — Bootstrap secret | Generate and protect one local bootstrap secret file outside the repository | Verify ACL/path/format without revealing value; stop on ACL or path uncertainty |
| B — Docker provisioning | Create only the proposed service using explicit project/file identity | Preflight names and port; stop on any collision or missing secret |
| C — Read-only resource verification | Inspect exact container, health, labels, port and mounts | Record container ID and mount metadata; stop on unexpected/protected mount |
| D — Runtime-role bootstrap | Execute approved local SQL/role setup using bootstrap credentials | Verify runtime role flags, scoped privileges and independent credentials; never use bootstrap for tests |
| E — Disposable migration | Run guarded wrapper against exact target | Verify selectors/effective URL before DDL; stop on mismatch/failure |
| F — Database-backed tests | Run separately approved regression phases with runtime role | Capture counts/revision; stop on any unexpected side effect |
| G — Cleanup/rollback | Each exact container/network/volume/secret removal | Separate approval for each resource; establish ownership and retain evidence first |

Gates are ordered, independent approvals. A failure at one gate does not authorize a retry, workaround, resource deletion, or progression to the next gate.

## 15. Acceptance Criteria Matrix

| Criterion | Result | Evidence / limitation |
|---|---|---|
| AC-01 Only one new Markdown report | PASS | This report only. |
| AC-02 No existing source file modified | PASS | Read-only inspection; no source edits. |
| AC-03 No Docker daemon/resource operation | PASS | None performed. |
| AC-04 No PostgreSQL connection or SQL | PASS | None performed. |
| AC-05 No credentials read or created | PASS | No secret files or values accessed/generated. |
| AC-06 No migration or tests executed | PASS | None executed. |
| AC-07 No Git/GitHub mutation | PASS | Read-only Git only; no GitHub calls. |
| AC-08 Exact project/container identity defined | PASS | Static YAML and supplied target. |
| AC-09 Port 55435 and loopback binding documented | PASS | Compose line 19 and deployment docs lines 61–68. |
| AC-10 Protected environments identified | PASS | Section 4; no access performed. |
| AC-11 Anonymous-volume risk addressed | PASS | Section 8; runtime behavior explicitly NOT VERIFIED. |
| AC-12 Bootstrap secret procedure designed | PASS | Section 7; not executed. |
| AC-13 Runtime role and grants planned | PASS | Section 9; actual bootstrap implementation absent. |
| AC-14 Migration isolation planned | PASS | Section 10. |
| AC-15 Regression test isolation planned | PASS | Section 11. |
| AC-16 Cleanup ownership verification planned | PASS | Section 12 and Gate G. |
| AC-17 Failure recovery scenarios covered | PASS | Section 13. |
| AC-18 Separate approval gates documented | PASS | Section 14. |
| AC-19 No provisioning authorized/performed | PASS | Planning-only boundary maintained. |
| AC-20 No unsupported runtime PASS claims | PASS | Runtime mounts, current collisions, health, roles and DB state remain unverified. |

## 16. Residual Risks and Blockers

1. **Evidence reconciliation blocker:** the owner-supplied historical image/host observations conflict with the limitations recorded in `adm_8.10.206.md`. Obtain a fresh, separately authorized read-only host preflight before relying on image, port, or resource-availability claims.
2. **Runtime isolation not established:** the proposed target is unprovisioned. Current name/port availability, labels, health, actual mounts, and database identity are not verified now.
3. **Least-privilege bootstrap gap:** Compose initializes only a privileged bootstrap identity; no runtime role creation/grant script or verified procedure is implemented. Resolve and approve this before migrations/tests.
4. **Anonymous mount:** supplied image metadata suggests an anonymous mount at `/var/lib/postgresql/data`; runtime association and whether it stores database files are not verified.
5. **Test side effects:** audit history intentionally persists; use aggregate snapshots and a fresh isolated database rather than broad cleanup.
6. **Credential exposure:** the old regular test password is compromised and must not be reused. Its rotation is a separate authorization-gated security task; it is not a prerequisite to a truly separate new cluster, but should be tracked and completed before any future use of the old target.
7. **Host boundary:** Docker Desktop/PowerShell execution is host-side and must be performed only under the relevant gate; do not assume the Codex sandbox can safely access Docker.

## 17. Git and Resource Preservation

Final read-only checks confirmed branch `docs/ci-pr-evidence`, HEAD `f6fff10898fc9a7c3d56a303fba7f50a1b1715e2`, and an empty index. Existing tracked modifications and untracked reports/configuration remain present; no source or other pre-existing file was changed. The only created file is `docs/codex-reports/adm_8.10.210.md`. No Docker/PostgreSQL resource was contacted, no credential was accessed, and no test, migration, GitHub, cloud, or deployment operation occurred. The protected 50-record database was not contacted; its preservation is based on non-access in this step, not a fresh count query.

## 18. Recommended SINGLE Next Step

Request a separately scoped Human Product Owner approval for a **host-side read-only pre-provisioning identity/mount/port recheck**, explicitly reconciling the evidence discrepancy with `adm_8.10.206.md`. Do not create the secret or provision the container until that evidence is reviewed and the runtime-role bootstrap plan is separately approved.
