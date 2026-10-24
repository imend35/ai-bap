# ADIM 8.10.147 — Final Manual Security Diff Review

## 1. Objective

Perform a comprehensive manual, read-only security review of the complete Pull
Request #1 range to compensate for Sourcery AI's documented 150,000-character
diff-size review limitation. This report does not approve, merge, deploy, or
otherwise change the PR.

## 2. Repository and PR State

- Repository: `imend35/ai-bap`.
- Source: `docs/ci-pr-evidence` at
  `2afe0d4d88188ad0a8de14c590ca95d0536b1241`.
- Target: `main` at `1e4333738947f131816901b9fdb71e4fff61d4f2`.
- Review range: `main...docs/ci-pr-evidence`.
- Range composition: eight commits, 52 changed files, 4,705 additions, 176
  deletions, and zero deleted paths.
- Git index: empty.
- `git diff --check` for the committed PR range: PASS.

The local working tree contained the pre-existing modified
`docs/codex-reports/adm_8.10.76.md` and pre-existing untracked Codex reports.
They are not part of the committed comparison and were not changed by this
review.

## 3. Complete 52-File Review Inventory

Every changed line in the committed comparison was inspected. The files are
classified below; historical reports were also read for contradictory claims
and high-confidence credential indicators.

| Classification | Count | Reviewed paths |
| --- | ---: | --- |
| Security-sensitive application code | 4 | `backend/app/config.py`; `backend/app/initial_admin_bootstrap.py`; `backend/scripts/bootstrap_admin.py`; `frontend/src/App.tsx` |
| Deployment and infrastructure | 9 | `.env.example`; `docker/backend/Dockerfile`; `docker/backend/bootstrap_initial_admin_from_environment.py`; `docker/backend/migrate_production.py`; `docker/backend/start_api.py`; `docker/backend/start_api_free.py`; `render.yaml`; `render.free.yaml`; `README.md` |
| Tests | 6 | `backend/tests/test_bootstrap_admin.py`; `backend/tests/test_deployment_configuration.py`; `backend/tests/test_initial_admin_bootstrap.py`; `backend/tests/test_initial_admin_bootstrap_integration.py`; `backend/tests/test_migrate_production.py`; `backend/tests/test_render_free_deployment_configuration.py` |
| Current documentation | 10 | `docs/architecture.md`; `docs/bootstrap-admin.md`; `docs/deployment-render.md`; `docs/deployment-render-free.md`; `docs/github-issues-plan.md`; `docs/project-charter.md`; `docs/project-rubric-gap-analysis.md`; `docs/revised-project-roadmap.md`; `docs/testing-strategy.md`; `product-spec.md` |
| Historical evidence | 23 | `docs/codex-reports/adm_8.10.72.md`; `adm_8.10.76.md`; `adm_8.10.82.md`; `adm_8.10.83.md`; `adm_8.10.84.md`; `adm_8.10.85.md`; `adm_8.10.86.md`; `adm_8.10.87.md`; `adm_8.10.92.md`; `adm_8.10.93.md`; `adm_8.10.94.md`; `adm_8.10.96.md`; `adm_8.10.97.md`; `adm_8.10.98.md`; `adm_8.10.100.2.md`; `adm_8.10.100.4.md`; `adm_8.10.100.6.md`; `adm_8.10.100.8.md`; `adm_8.10.100.10.md`; `adm_8.10.101.md`; `adm_8.10.108.md`; `adm_8.10.110.md`; `adm_8.10.119.md` |

No changed file was excluded from review. No Alembic revision, database dump,
environment file containing a real secret, binary artifact, or generated
dependency directory is in the PR range.

## 4. Security-Sensitive Diff Analysis

### Authentication and initial administrator bootstrap

- `backend/app/initial_admin_bootstrap.py:99-109` normalizes input and reuses
  `UserRegister`; it does not relax normal registration policy.
- `:123-159` obtains the shared transaction-scoped active-administrator lock,
  checks existing email before creating anything, refuses when an active
  administrator exists, and calls the existing Argon2id hashing service.
- `:160-175` returns `EMAIL_EXISTS` only for PostgreSQL SQLSTATE `23505` and
  the known `ix_users_email` constraint; unrelated integrity failures roll
  back and fail closed.
- `:178-227` enables environment bootstrap only for literal `true`, requires
  all fields, and uses fixed diagnostic categories only when tests request a
  callback. It does not expose a route or OpenAPI operation.
- `docker/backend/bootstrap_initial_admin_from_environment.py:11-27` contains
  the deployment boundary: unexpected exceptions produce a generic failure and
  nonzero exit without formatting exception details.
- `backend/scripts/bootstrap_admin.py` retains the interactive local command;
  password entry is through `getpass`, not a CLI argument or default value.

No authentication bypass, administrator promotion of an existing user,
default privileged account, password disclosure, or public bootstrap endpoint
was found.

### Database migration and startup

- `docker/backend/migrate_production.py:16-48` uses a fixed advisory-lock key,
  runs `alembic upgrade head` with an argument list rather than a shell,
  captures child output, releases the lock in `finally`, and returns nonzero
  with one generic stderr message for configuration, connection, lock,
  migration, unlock, and unexpected ordinary errors.
- `docker/backend/start_api_free.py:27-47` orders migration, bootstrap, then
  API execution and returns before API startup if either prerequisite fails.
- `docker/backend/start_api.py:9-25` validates a numeric bounded `PORT` and
  uses `execvp` with fixed arguments; no command-string interpolation occurs.
- `backend/app/config.py:53-75` accepts only PostgreSQL `DATABASE_URL` values
  and fails closed if neither a valid override nor a passworded component
  configuration is present. Secret-bearing settings use `SecretStr`.

There is no reset, truncate, downgrade, fresh-local initializer, or schema
revision in the reviewed migration path.

### Render, CORS, and frontend API base

- `render.yaml:22-31` and `render.free.yaml:22-31` obtain managed database
  connectivity and generated JWT secrets from Render configuration rather than
  repository literals.
- Both descriptors require operator-supplied `CORS_ORIGINS` (`:28-29`); the
  backend default allowlist is local-only (`backend/app/config.py:38-44`). No
  wildcard origin is introduced.
- `frontend/src/App.tsx:173-177` receives only a public Vite API-base variable,
  falls back to host-based development routing, and uses same-origin requests
  in a production build without an explicit API base. It does not carry a
  database or JWT secret.
- `.env.example:2-14` contains placeholders and variable names only. Its
  connection example is explicitly a placeholder, not a real URL.

### Documentation and secret review

The 23 historical reports and all current documentation were read. A
high-confidence scan found no private-key marker, GitHub token pattern,
credential-bearing connection URL, AWS-key pattern, or Bearer-token value.
Reported CI passwords and JWT values are documented or configured only as
synthetic, isolated CI fixtures, not production credentials.

Historical reports retain statements accurate at their recorded point in time.
They must not be read as current deployment evidence. Current documents do not
claim public deployment, production HTTPS, continuous deployment,
observability, alerting, or on-call operation.

## 5. Test Coverage Assessment

The changed tests cover exact bootstrap enablement, missing and invalid
configuration, validation behavior, constraint classification, expected and
unexpected failure sanitization, no public bootstrap route, repeat execution,
concurrent initialization, existing-user protection, and administrator login
in the guarded integration suite.

Migration tests cover successful lock/unlock ordering and generic nonzero
failure behavior for invalid settings, connection, advisory-lock, Alembic, and
unexpected failures. They assert synthetic secret-like markers, traceback text,
and URL indicators are absent from captured output. Free-startup tests confirm
that a migration or bootstrap failure prevents API launch.

For the exact PR head, the verified GitHub Actions pull-request run
`40006283556` completed successfully with both `Frontend quality` and
`Backend quality` successful. CI is meaningful source-quality evidence, not
evidence of Render provisioning or public operation. Sourcery remained skipped
because of its documented size limit, so this manual review is compensating
coverage rather than an independent human approval.

## 6. Findings by Severity

### CRITICAL — none verified

No verified hardcoded production credential, unauthenticated privileged route,
authentication/authorization bypass, destructive database behavior, or SQL or
shell injection was found.

### HIGH — none verified

No verified high-severity source-level defect was found in the authentication,
bootstrap, migration, CORS, or frontend API-base changes.

### MEDIUM — deployment-only: paid Blueprint auto-deploy value needs platform confirmation

- **Location:** `render.yaml:18` and `render.yaml:38`.
- **Evidence:** the paid descriptor uses the unquoted scalar `off`, while the
  Free descriptor uses the explicit string `"off"` at
  `render.free.yaml:19,38`. YAML-schema interpretation and Render Blueprint
  acceptance were not verified against a live Render validation.
- **Impact:** if Render interprets the paid value as a boolean or rejects it,
  deployment behavior may not match the documented manual-release intent.
  There is no provisioned service, so this is not an active exposure.
- **Merge blocker:** No.
- **Deployment blocker:** Yes, until validated or corrected using Render's
  supported schema.
- **Mitigation:** before provisioning, verify the field through Render's
  Blueprint validation; if a string is required, make the paid values explicit
  strings and add a focused descriptor regression test.

This is a source-supported configuration risk, not a confirmed Render defect.

### LOW — current documentation has stale Compose-runtime wording

- **Location:** `product-spec.md:160-161,197`;
  `docs/project-charter.md:124,144`; `docs/architecture.md:195`.
- **Evidence:** these current-state passages say the isolated full-stack
  Compose runtime has not been verified, while
  `docs/codex-reports/adm_8.10.82.md:15-81` records the successful isolated
  build, migration, health, direct API, frontend, and same-origin proxy checks.
  `docs/project-rubric-gap-analysis.md` already preserves the correct limited
  distinction: isolated local runtime verified; public deployment and
  authenticated end-to-end testing not verified.
- **Impact:** documentation quality and evidence clarity only; no runtime
  security control is weakened.
- **Merge blocker:** No.
- **Deployment blocker:** No, but correct before final submission.
- **Mitigation:** make a separate narrowly scoped documentation correction;
  retain the explicit limitation that public production operation remains
  unverified.

### INFORMATIONAL — external deployment controls remain unverified

`CORS_ORIGINS` and the one-time administrator bootstrap secrets are deliberately
operator-managed (`render.free.yaml:28-29`,
`docs/bootstrap-admin.md:45-69`). The code fails closed on missing or invalid
input and documentation requires removal after first creation. Actual Render
secret handling, CORS browser behavior, platform logs, managed PostgreSQL,
backup/recovery, and plan/schema compatibility remain externally unverified
because no Render resource has been provisioned. These are deployment gates,
not merge-time source defects.

## 7. Reconciliation with Earlier Reviews

- ADIM 8.10.130 identified migration-log redaction as a medium deployment
  concern. The committed `2afe0d4` change now supplies a generic error
  boundary, captured Alembic output, and focused tests; no equivalent verified
  source-level issue remains.
- ADIM 8.10.140 reviewed that local fix and recorded only low residual
  limitations. The current full-range review confirms the same behavior.
- ADIM 8.10.145 correctly separated successful CI and merge readiness from
  public deployment readiness. This review maintains that separation and adds
  the paid-Blueprint value as an external deployment validation gate.

## 8. Merge and Deployment Assessment

**Merge security readiness: conditional GO.** The full committed PR range has
no verified CRITICAL or HIGH source-level security blocker. The reviewed
security-sensitive paths preserve fail-closed behavior, administrator lifecycle
protection, secrets outside source control, non-destructive migrations, and
safe child-process invocation.

**Deployment readiness: NO-GO.** Public deployment still requires Render
Blueprint/platform validation, exact HTTPS CORS configuration, one-time
bootstrap-secret lifecycle verification, managed-database migration evidence,
platform-log inspection, public smoke tests, and recovery evidence.

This assessment is not independent human approval and does not override
GitHub policy, required checks, unresolved-conversation status, or a separate
Human Product Owner authorization for any merge.

## 9. Working-Tree Preservation and Validation

- No application, test, infrastructure, or existing documentation file was
  modified by this review.
- No file was staged, committed, pushed, merged, deployed, or provisioned.
- This report is the only file created by ADIM 8.10.147 and remains untracked.
- `git diff --check` for the complete committed PR comparison passed.

## 10. Recommended Single Next Action

The Human Product Owner should complete the GitHub UI merge-governance
checklist from ADIM 8.10.145 (required checks, protection policy, approval
requirements, and resolved conversations). If those gates pass and the owner
accepts the deployment-only risks, request separately authorized merge
execution. Do not treat that merge as authorization to provision or deploy
Render resources.
