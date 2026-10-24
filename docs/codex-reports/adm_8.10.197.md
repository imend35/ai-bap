# ADIM 8.10.197 — Secure Demo Registration Gate Implementation

## Step Name and Objective

I implemented a fail-closed public-registration setting for the short-lived AI BAP demo. The API now denies anonymous self-registration by default, while retaining login and the existing authenticated business-analyst workflow. Render Free explicitly disables public registration. No schema or dependency changes were made.

## Human Product Owner Authorization

Implementation was authorized only for the narrowly scoped backend registration gate, its tests, Render Free configuration, deployment documentation, local non-destructive tests/static checks, and this report. Git/GitHub mutation, cloud provisioning, deployment, persistent-database migrations, account creation, paid services, and unrelated changes were not authorized and were not performed.

## Summary of Completed Work

- Added `PUBLIC_REGISTRATION_ENABLED` with a secure default of `false` using the existing Pydantic settings mechanism.
- Added an early registration guard that returns HTTP 403 with a generic message before account lookup, password hashing, or persistence.
- Kept `/api/v1/auth/login`, JWT behavior, and RBAC code unchanged.
- Set the Render Free API environment value explicitly to the string `false`.
- Added coverage for the default, disabled behavior/no side effects, login while disabled, enabled registration/role assignment, and duplicate handling. Legacy registration-dependent tests opt in only within the isolated pytest process.
- Updated deployment documentation for curated accounts, the fresh synthetic database, private credentials, shared-workspace limitations, and remaining risks.

## Files Changed

1. `.env.example` — documents the disabled default.
2. `backend/app/config.py` — adds the boolean setting.
3. `backend/app/routers/auth.py` — adds the 403 gate.
4. `backend/tests/conftest.py` — enables the existing registration contract only inside the isolated test process; tests can explicitly override it.
5. `backend/tests/test_auth_registration_api.py` — adds DB-free gate/login/enabled-path tests and explicitly opts existing positive integration tests into registration.
6. `backend/tests/test_render_free_deployment_configuration.py` — asserts the Free Blueprint setting is the string `false`.
7. `docs/deployment-render-free.md` — documents safe account and deployment requirements.
8. `render.free.yaml` — explicitly disables public registration for the Free API.
9. `docs/codex-reports/adm_8.10.197.md` — this authorized, untracked report.

No frontend production code, database model, migration, package manifest, dependency, paid `render.yaml`, CI workflow, or unrelated file was changed by this task.

## Registration Gate Implementation

`backend/app/config.py` now defines `public_registration_enabled: bool = Field(default=False)`. `backend/app/routers/auth.py` injects the existing cached `get_settings` object and returns `403 Forbidden` (`Public registration is disabled.`) before checking for an existing email or hashing the password. The denied path does not call account lookup, `add`, `commit`, password hashing, or token creation. Validation of the request schema still occurs before the handler, as normal for FastAPI.

When explicitly enabled, the existing registration code continues to normalize/check the email, hash the password, create an active `business_analyst`, and preserve duplicate handling. The request schema does not grant a requested role; a test supplies an attempted admin role and confirms the created role remains `business_analyst`.

Login remains unchanged. A curated active account can authenticate when registration is disabled. This gate does not implement tenant isolation or revoke accounts already in a database.

## Render Free Configuration

`render.free.yaml` now explicitly sets `PUBLIC_REGISTRATION_ENABLED` to the YAML string `"false"`. The Render Free configuration test parses the YAML and verifies the value. No Blueprint import, migration, account creation, or deployment occurred.

## Test Changes

The registration test module contains fake-session tests that avoid connecting to PostgreSQL. They verify the secure default, the 403/no-side-effect path, login while registration is disabled, the enabled BA-only creation contract, and duplicate-account conflict behavior. Existing DB-backed registration tests remain and explicitly opt into registration.

`backend/tests/conftest.py` sets the legacy-registration flag only in the test process after its fail-closed PostgreSQL test-target checks. Security tests override the flag and clear the cached settings around requests. This adaptation preserves other existing tests that register users; it does not change application defaults or deployment configuration.

## Validation Commands and Results

All test commands ran from `backend` using synthetic process-local test configuration. The PostgreSQL safety guard was configured to the designated isolated test target, but its port was not listening. The selected auth tests use a fake database dependency and did not connect to PostgreSQL.

1. `python -m pytest -p no:cacheprovider tests/test_auth_registration_api.py -k 'public_registration_is_disabled_by_default or disabled_registration_returns_403_without_side_effects or existing_user_can_log_in_while_registration_is_disabled or enabled_registration_preserves' -q` — **PASS**, exit 0; 5 passed, 5 deselected.
2. `python -m pytest -p no:cacheprovider tests/test_render_free_deployment_configuration.py -q` — **PASS**, exit 0; 8 passed.
3. `ruff check app/config.py app/routers/auth.py tests/conftest.py tests/test_auth_registration_api.py tests/test_render_free_deployment_configuration.py` — **PASS**, exit 0; all checks passed.
4. `git diff --check` — **PASS**, no whitespace errors. Git emitted working-tree LF-to-CRLF conversion warnings for files with existing line-ending policy; no line-ending normalization was performed.

An initial focused test iteration used `.test` email domains rejected by the existing email validator (422 before the endpoint). The synthetic test addresses were corrected to valid `example.com` fixtures; the final focused run above passed.

The five deselected auth cases include existing DB-backed registration tests and input-validation cases. The full backend suite and DB-backed registration tests were **not run** because the isolated PostgreSQL endpoint at `127.0.0.1:55432` was not listening. No service was started. Frontend tests were not run because frontend production code was unchanged. No build was run. GitHub CI has not verified these local changes.

## Acceptance Criteria Matrix

| Criterion | Status | Evidence / limitation |
|---|---|---|
| AC-01 Registration disabled by default | **PASS** | Settings unit test verifies false with no environment override. |
| AC-02 Disabled registration returns HTTP 403 | **PASS** | DB-free API test asserts exact status and generic detail. |
| AC-03 Denied registration creates no user | **PASS** | Fake session confirms no account lookup, add, or commit; hashing/token functions are guarded to fail if called. No persistent DB was used. |
| AC-04 Login remains functional | **PASS** | Login API test with a synthetic active BA and fake DB returns 200 while registration is false; token generation is mocked. |
| AC-05 Explicitly enabled registration retains behavior | **PASS** | DB-free test confirms 201, active BA and duplicate 409; existing DB-backed behavior tests remain but were not locally run. |
| AC-06 Self-registration cannot grant admin | **PASS** | Enabled-path test attempts role escalation and confirms BA; role schema/assignment unchanged. |
| AC-07 JWT/RBAC protections remain intact | **NOT VERIFIED** | Those files were not changed, but the broader auth/RBAC test suite was not run locally. |
| AC-08 Render Free explicitly disables registration | **PASS** | YAML test asserts `PUBLIC_REGISTRATION_ENABLED` is the string `false`. |
| AC-09 No database schema migration | **PASS** | No models or migration files changed. |
| AC-10 No new dependency | **PASS** | No dependency manifests or lockfiles were changed by this task. |
| AC-11 No production frontend change | **PASS** | No frontend production file changed. |
| AC-12 Unrelated local work preserved | **PASS** | Before/after status retained the pre-existing modifications and untracked paths. |
| AC-13 No Git/GitHub/cloud mutation | **PASS** | No staging, commit, push, GitHub action, provisioning, or deployment occurred. |
| AC-14 Deployment documentation covers required safe demo boundaries | **PASS** | Guide documents registration setting, login, bootstrap lifecycle, curated BA, fresh synthetic DB, existing-account review, private credentials, shared workspace, lack of throttling, and separate deployment approval. |
| AC-15 Authenticated project demo remains compatible | **NOT VERIFIED** | Login behavior was API-tested; no project-flow E2E or PostgreSQL-backed demo test was run in this step. Project routes and frontend were unchanged. |

## Security and Residual Risks

- The registration endpoint is now disabled by default and explicitly disabled in the Render Free manifest. Login remains public by design but requires valid credentials.
- This is not tenant isolation. Any deliberately provisioned BA can still read and modify the shared demo workspace. Use only a dedicated fresh database with synthetic data and review accounts before exposure.
- Do not publish demo or administrator credentials; provide them only to authorized evaluators through a private channel. If arbitrary visitors must receive public credentials, this design is insufficient.
- Login throttling/account lockout remains unimplemented and is a residual brute-force risk.
- A registration flag does not deactivate existing accounts. Deployment must use a fresh dedicated database or verify/deactivate unauthorized existing accounts before public exposure.
- No secret values or real personal data were added. Test credentials and identities are synthetic fixtures only.

## Deployment Readiness Assessment

The code and Free Blueprint configuration are ready for review, but **deployment remains NO-GO**. The Render Blueprint was not imported or deployed; no database was created; no runtime migration, CORS, public login, project persistence, or account-lifecycle behavior was verified on Render. Provisioning and deployment still require separate explicit owner authorization. This implementation does not establish production readiness or tenant isolation.

## Preservation Verification

Branch remained `docs/ci-pr-evidence`; HEAD remained `f6fff10898fc9a7c3d56a303fba7f50a1b1715e2`; the index remained empty. The original local modifications and untracked reports/Playwright artifacts remain preserved. Only the eight authorized existing files listed above were modified, plus this one new untracked report. No GitHub, CI, cloud, account, or deployment mutation occurred.

## Recommended SINGLE Next Step

Request a separately authorized isolated PostgreSQL test run for the remaining DB-backed auth suite, then review the resulting evidence before any separately approved Render provisioning decision.
