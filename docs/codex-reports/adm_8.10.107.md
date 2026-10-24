# ADIM 8.10.107 — Focused Manual Security Review

## Step name and objective

Perform an independent source-based security review of PR #1 at committed head `47b7f20a1476375c057eef71d47a2c1a53d04a2b`. This is technical evidence for a future Human Product Owner merge decision; it is not independent human approval and it does not verify a public deployment.

## Verified facts

- The reviewed range is `main...47b7f20a1476375c057eef71d47a2c1a53d04a2b`: five commits and 48 changed files.
- The supplied GitHub evidence records successful frontend and backend CI jobs for PR #1. Sourcery AI was skipped because the PR exceeded its review-size limit.
- The local CI workflow has least-privilege `contents: read`, locked frontend dependencies, an ephemeral PostgreSQL service, guarded migration execution, full backend pytest discovery, and Ruff.
- `git diff --check main...HEAD` passed. No new application tests were executed for this review.
- Live branch protection, required-check policy, current PR review state, and Render platform behavior could not be independently queried from this environment.

## Files inspected

- Bootstrap and authentication: `backend/app/initial_admin_bootstrap.py`, `backend/app/admin_user_lifecycle.py`, `backend/app/config.py`, `backend/app/models/user.py`, `backend/app/password_service.py`, `backend/app/security.py`, `backend/app/jwt_service.py`, `backend/app/routers/auth.py`, `backend/app/routers/admin_users.py`, and `backend/scripts/bootstrap_admin.py`.
- Deployment: `docker/backend/bootstrap_initial_admin_from_environment.py`, `docker/backend/start_api_free.py`, `docker/backend/migrate_production.py`, `docker/backend/Dockerfile`, `render.yaml`, `render.free.yaml`, `.env.example`, and `frontend/src/App.tsx`.
- Verification: relevant bootstrap/deployment tests and `.github/workflows/ci.yml`.

## Security findings

| Severity | Classification | Finding and evidence | Recommendation |
| --- | --- | --- | --- |
| CRITICAL | None verified | No source evidence of a public bootstrap endpoint, default privileged credential, committed production secret, unauthenticated administrator-creation route, or JWT-role bypass. `backend/app/main.py:37-57` registers no bootstrap route; `backend/tests/test_initial_admin_bootstrap.py:301-307` checks main/OpenAPI for it. | Preserve the no-public-route assertion and require review of any future bootstrap transport change. |
| HIGH | None verified | Bootstrap requires exact opt-in and complete values (`backend/app/initial_admin_bootstrap.py:164-174`), reuses registration validation (`81-91`), and serializes lifecycle work with a transaction-scoped advisory lock (`105-140`; `backend/app/admin_user_lifecycle.py:10-16`). Existing email and active-admin cases do not overwrite data (`110-129`). | Preserve these invariants and retain isolated concurrency coverage in CI. |
| MEDIUM | Potential / platform-unverified | `CORS_ORIGINS` is deliberately operator-supplied (`render.yaml:28-29`; `render.free.yaml:28-29`) while the frontend API URL is injected at static-build time (`render*.yaml:43-48`). A wrong/missing exact HTTPS origin fails closed for browsers but makes the public demo unusable. Blueprint service-reference timing and field behavior were not live-verified. | Set the final static-site HTTPS origin exactly before an authorized deploy and run allowed/disallowed-origin browser smoke tests. |
| MEDIUM | Potential / runtime-unverified | Migration reconstructs an unmasked driver connection string (`docker/backend/migrate_production.py:16-21`) without printing it. The Free wrapper emits generic child-process failures (`docker/backend/start_api_free.py:14-23`) but cannot suppress child Python tracebacks. No deployed log policy or real Render failure was inspected. | During an authorized disposable runtime test, verify failed-start logs contain no connection credential. Consider a narrowly approved sanitized process boundary for unexpected exceptions. |
| LOW | Verified defect | Every `IntegrityError` maps to `EMAIL_EXISTS` (`backend/app/initial_admin_bootstrap.py:142-148`). Tests cover duplicate email (`backend/tests/test_bootstrap_admin.py:167-183`) but not a different constraint. A non-email integrity error can fail startup with an inaccurate safe outcome. It fails closed and does not escalate privileges. | In a follow-up, safely distinguish the known email constraint from other integrity errors and test both results. |
| LOW | Potential / defense in depth | The environment launcher catches only `RuntimeError` and `ValueError` (`docker/backend/bootstrap_initial_admin_from_environment.py:13-17`). Expected validation/database outcomes become result values, but another dependency exception could escape as a child traceback. There is no evidence that this leaks a secret. | Test a representative non-`RuntimeError` exception and consider a generic sanitized process boundary while preserving nonzero failure. |
| LOW | Pre-existing attack-surface risk | Public registration exists (`backend/app/routers/auth.py:29-76`) and grants only the least-privileged business-analyst role (`53-60`). No rate-limit, email-verification, or abuse-control evidence was found. This is not introduced by this PR. | Decide whether a public demo requires registration abuse controls before broader exposure. |

## Positive security evidence

- The password service uses Argon2id (`backend/app/password_service.py:4-12`), and public user responses omit hashes (`backend/app/schemas/auth.py:24-34`).
- Bootstrap creates an administrator only after lock, email lookup, and active-admin lookup (`initial_admin_bootstrap.py:105-141`).
- Administrator lifecycle routes reuse the same lock (`backend/app/routers/admin_users.py:34-86`, `105-157`, `244-308`).
- The Free wrapper runs migration, bootstrap, then API startup and stops on child failure (`docker/backend/start_api_free.py:27-49`); tests cover ordering/interruption (`backend/tests/test_render_free_deployment_configuration.py:89-159`).
- Managed database injection and platform-generated JWT configuration avoid committed secrets (`render*.yaml:21-31`). The Free path excludes the fresh-local-database initializer (`backend/tests/test_render_free_deployment_configuration.py:162-166`).

## Test coverage and remaining gaps

Covered source tests include exact enablement, validation failure, safe diagnostics, absence of default credentials/public route, existing-email protection, existing-active-admin no-op, hash verification, guarded concurrency, login, Blueprint shape, and Free startup ordering. The supplied CI evidence confirms successful frontend/backend jobs; this review did not obtain a live per-module log for this head.

Missing or not demonstrated:

- Non-email `IntegrityError` classification.
- Sanitized handling of an arbitrary unexpected bootstrap-child exception.
- Authorized Render runtime tests for managed-database connectivity, final CORS, cold restart, bootstrap-secret removal, and container-log redaction.
- Public-registration abuse controls, if the public registration model remains.
- Live branch-protection and required-review evidence.

## CI and release assessment

Successful CI is meaningful for test-covered code but does not prove deployment, Render Blueprint availability, managed-database behavior, production CORS, or platform-side log redaction. Sourcery's skip removes an automated review layer; this source review is alternative technical evidence, not a substitute for Human Product Owner approval or required human review.

## Blockers, final status, and next step

**Conditional GO for an explicitly authorized human merge review; NO-GO for public deployment.** No CRITICAL or HIGH verified source defect was found. Before merge, the Human Product Owner should accept or schedule the LOW findings and verify live required checks/reviews. Before public deployment, resolve the MEDIUM platform/logging risks through an authorized disposable Render runtime test.

## Commands executed and actual results

| Command or check | Result |
| --- | --- |
| Commit/head/status inspection | PASS — reviewed the committed head; pre-existing uncommitted reports were not changed. |
| `git diff --check main...HEAD` | PASS. |
| Line-numbered source inspection | PASS. |
| Live GitHub protection/reviews and Render runtime checks | NOT RUN / unavailable in this read-only environment. |

## Recommended next step

Obtain Human Product Owner review of the findings and broad PR scope. If the LOW follow-ups are accepted, verify GitHub required checks/reviews before separately authorizing merge. Schedule an authorized disposable Render runtime smoke test before any public-demo claim.
