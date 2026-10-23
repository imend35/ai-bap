# ADIM 8.10.94 — Secure Initial Administrator Bootstrap Design

## Step Name and Objective

Design, without implementing or deploying, a one-time initial-administrator
bootstrap mechanism that works on Render Free without shell access or public
PostgreSQL connectivity.

## Existing Bootstrap Behavior and Limitation

The existing local command, documented in `docs/bootstrap-admin.md`, runs
`python -m scripts.bootstrap_admin`. It interactively collects the
administrator's email, full name, password, and confirmation without echoing
the password.

`backend/scripts/bootstrap_admin.py` already provides the required secure
domain operation:

- validates the input with the existing `UserRegister` rules;
- normalizes the email;
- uses the existing Argon2id `hash_password` implementation;
- creates an active `admin` role only when no active administrator exists;
- relies on PostgreSQL-generated immutable record numbers;
- obtains the shared transaction-scoped active-administrator advisory lock;
- rejects duplicate email or existing-active-administrator cases without
  printing user data, password hashes, tokens, or database errors.

The public registration endpoint is not an alternative: it assigns only the
least-privileged `business_analyst` role. Existing administrative user routes
require an authenticated administrator, so they cannot establish the first
one.

The command cannot currently be used for Render Free because the Free web
service has no shell access and `render.free.yaml` deliberately keeps managed
PostgreSQL externally blocked. A local process must not be assumed able to
reach Render's private database address.

## Security Requirements

The proposed design must:

1. run inside the API container, without a shell or public database access;
2. require an explicit operator action in the Render Dashboard;
3. create at most one initial active administrator;
4. make no change when an active administrator already exists;
5. have no default email, name, password, token, or privileged account;
6. avoid logging plaintext passwords, Bootstrap configuration values, URLs, or
   user details;
7. expose no HTTP bootstrap route;
8. reuse the existing validation, hashing, role, and advisory-lock logic;
9. fail closed for enabled-but-incomplete or invalid bootstrap configuration;
10. never reset, truncate, overwrite, deactivate, or promote existing users;
11. remain race-safe when startup/deploy attempts overlap; and
12. use only Render-managed environment values, with no paid service or new
    dependency.

## Alternatives Evaluated

| Alternative | Benefits | Risks and limitations | Decision |
| --- | --- | --- | --- |
| Startup bootstrap from operator-managed environment values | Works entirely inside the API's private network; no public endpoint or shell; can reuse the existing transaction lock and helper; easy to mock and test. | Secrets remain in the platform environment until the operator removes them; startup sequencing must ensure migration succeeds first; configuration needs strict fail-closed validation. | **Recommended.** |
| Short-lived token-protected public bootstrap endpoint | Allows an operator to submit data after service startup. | Creates an internet-facing privileged operation, increases replay/brute-force/logging risk, needs token expiry/consumption and endpoint hardening, and could accidentally remain reachable. A token alone does not remove the risk. | Rejected for the capstone demo. |
| Adapt existing interactive command for a temporary local run | Reuses proven interaction and avoids code changes. | Does not work with the database private to Render Free. Temporarily exposing the database to an operator IP is an operational security exception, depends on dashboard capabilities, and introduces client/network risk. | Not recommended as the normal design; retain only as a separately approved recovery option. |

## Recommended Design: Explicit Startup-Only Bootstrap

Add a small environment-backed bootstrap adapter invoked only by the Free
startup path, after the advisory-locked Alembic migration and before the API
process starts. It must not be used by the paid Blueprint or local Compose.

### Required Environment Variables

| Variable | Purpose | Handling |
| --- | --- | --- |
| `AI_BAP_INITIAL_ADMIN_BOOTSTRAP_ENABLED` | Exact opt-in switch; only literal `true` enables bootstrap. | Not secret, no default enabling value. |
| `AI_BAP_INITIAL_ADMIN_EMAIL` | Initial administrator email. | Operator-provided, treated as sensitive personal data; no logs. |
| `AI_BAP_INITIAL_ADMIN_FULL_NAME` | Initial administrator name. | Operator-provided, treated as sensitive personal data; no logs. |
| `AI_BAP_INITIAL_ADMIN_PASSWORD` | Initial administrator password. | Render secret variable; supplied from a password manager; never logged, returned, or committed. |

No additional token is recommended. A token stored in the same trusted
platform environment would not create a meaningful security boundary over the
explicit enable flag and secret password. The enabling action is the Human
Product Owner adding all four values in Render's dashboard for one controlled
deployment.

### Execution Lifecycle

1. The Free entrypoint runs the existing `migrate_production.py`; an Alembic
   failure exits nonzero and prevents every later step.
2. It invokes a dedicated, internal environment-bootstrap adapter.
3. If the enable flag is absent or not exactly `true`, the adapter is a no-op
   and the API starts normally.
4. If the flag is `true`, all three administrator values must be present and
   nonblank. Any partial or invalid configuration returns nonzero before API
   startup.
5. The adapter passes validated values to the existing
   `bootstrap_initial_admin` function. It does not duplicate SQL, password
   hashing, role selection, record numbering, or locking code.
6. The existing transaction-scoped PostgreSQL advisory lock serializes
   concurrent initializations. A single successful transaction creates the
   administrator; another sees an existing administrator and creates none.
7. A successful creation allows API startup. An existing active administrator
   is a safe no-op, logged only as a generic non-sensitive outcome, so a
   restart cannot create a second account while the operator is completing
   cleanup.
8. Existing-email-without-active-admin, invalid input, database error, or
   missing enabled configuration returns nonzero and prevents API startup.
9. Immediately after the first successful deployment, the operator removes
   all four bootstrap values in the Render dashboard and triggers a controlled
   redeploy. This is required secret cleanup; the application must not attempt
   to mutate platform configuration or call the Render API.

## Atomicity, Failure, and Recovery

- The existing `pg_advisory_xact_lock` covers the administrator-existence
  check and insert in one transaction. The database's email uniqueness
  constraint remains a second layer of protection.
- The adapter must call no destructive database function and must never modify
  a pre-existing user.
- Generic logs may state `created`, `skipped because an administrator exists`,
  or `failed`; they must not include environment values, user email/name,
  plaintext passwords, hashes, database URLs, or tracebacks containing values.
- A failed enabled bootstrap should keep the API unavailable. This prevents a
  public service from appearing ready while its explicitly requested initial
  access control state is unresolved.
- There is no automatic rollback after a successful administrator insert. The
  account is a deliberate security action; subsequent correction uses the
  authenticated administrator lifecycle, not a destructive rollback.

## Minimal Future Implementation Plan

1. Add a small internal module, for example
   `backend/app/initial_admin_bootstrap.py`, that reads and validates only the
   four named variables and delegates to `bootstrap_initial_admin`.
2. Refactor `backend/scripts/bootstrap_admin.py` only if necessary to move its
   reusable non-interactive result handling into that module. Preserve the
   current interactive local command and its prompts.
3. Add a Free-only child process, for example
   `docker/backend/bootstrap_initial_admin_from_environment.py`, and invoke it
   from `start_api_free.py` between migration and `start_api.py`.
4. Extend `render.free.yaml` documentation—not its committed values—to list
   the four optional one-time variables. Do not place their values in the
   Blueprint, `.env.example`, source, tests, or reports.
5. Update `docs/deployment-render-free.md` and `docs/bootstrap-admin.md` with
   the controlled deployment, validation, manual secret-removal, and recovery
   procedure.
6. Do not change `render.yaml`, the public OpenAPI contract, migrations,
   database schema, registration endpoint, or local Compose initialization.

## Required Tests Before Deployment

- Unit tests for disabled/no-op behavior and exact enable-flag parsing.
- Unit tests rejecting every partial configuration and invalid registration
  detail without opening a database session.
- Unit tests proving `hash_password` and `bootstrap_initial_admin` are reused,
  not reimplemented.
- Unit tests for `CREATED`, `ACTIVE_ADMIN_EXISTS`, `EMAIL_EXISTS`, and failure
  outcomes with generic, non-sensitive output.
- Startup-wrapper tests proving strict order: migration, bootstrap adapter,
  then API exec; any nonzero prior result prevents API startup.
- Database integration tests in the existing guarded isolated environment for
  one creation, repeated execution, concurrent attempts, no overwrite of an
  existing user, and login with the generated administrator.
- Static tests proving no HTTP bootstrap endpoint or OpenAPI path is added and
  no default credential is present.
- Render Free disposable runtime verification after separate approval, including
  secret removal and a clean restart after bootstrap.

## Commands Executed and Results

- Read-only inspection of the existing bootstrap documentation/script,
  administrator lifecycle lock, user model, password service, authentication
  routes, migrations, Free Blueprint, Free wrapper, deployment documentation,
  existing tests, and Git status — PASS.
- `git status --short` — PASS; pre-existing ADIM 8.10.76 and ADIM 8.10.88–8.10.93
  changes were observed and preserved.
- No tests, Docker commands, database operations, environment changes, secret
  generation, provisioning, staging, commit, push, or deployment occurred.

## Issues, Approval Gates, and Remaining Tasks

1. The present repository cannot provision a secure first administrator on
   Render Free; the design requires a separately approved implementation.
2. The Human Product Owner must approve storing one temporary administrator
   password in Render's secret manager and removing the bootstrap values after
   the verified first creation.
3. The one-time deployment remains subject to Render account/plan availability
   and a disposable public runtime validation.
4. Full Free-tier limits remain: 30-day PostgreSQL expiry, no managed backups,
   and API cold starts.

## Final GO / NO-GO Assessment

**GO for a narrowly scoped implementation and test step.** The recommended
design reuses existing Argon2id hashing, validation, and transaction-scoped
advisory locking, requires no public bootstrap endpoint, and adds no paid
service or dependency.

**NO-GO for deployment today.** Implementation, guarded integration tests,
explicit approval of the temporary Render-secret lifecycle, and a disposable
runtime verification remain mandatory.

## Recommended Next Step

Obtain explicit approval to implement the environment-backed, Free-only
bootstrap adapter and its focused tests. Provisioning should remain prohibited
until that implementation is reviewed and verified.
