# ADIM 8.10.92 — Zero-Cost Public Deployment Feasibility Assessment

## Step Name and Objective

Assess the safest and fastest genuinely zero-cost public-demo architecture for
AI BAP, including a public HTTPS frontend, FastAPI API, and persistent
PostgreSQL data. This was an assessment-only step: no cloud account, billing
method, service, database, Docker resource, or Git state was changed.

## Files and Configurations Inspected

- `AGENTS.md`
- `render.yaml`
- `docs/deployment-render.md`
- `docker/backend/Dockerfile`
- `docker/backend/migrate_production.py`
- `docker/backend/start_api.py`
- `backend/app/config.py`
- `backend/scripts/bootstrap_admin.py`
- `backend/alembic.ini` and migration layout
- `frontend/src/App.tsx`
- `.github/workflows/ci.yml`
- Existing pending Git changes and Codex reports

## Verified Repository Facts

- The committed `render.yaml` targets paid Render PostgreSQL
  (`0.1c-256mb`) and API (`0.5c-512mb`) plans and uses the paid-only
  `preDeployCommand` migration mechanism.
- The backend already reads a managed `DATABASE_URL`, fails closed without a
  usable database configuration, validates the platform `PORT`, and accepts a
  configured CORS allowlist.
- `migrate_production.py` obtains a PostgreSQL advisory lock and then runs
  `alembic upgrade head`. It neither invokes the local fresh-database
  initializer nor resets, downgrades, or seeds a database.
- The frontend accepts `VITE_API_BASE_URL`; without it a production build uses
  a same-origin relative API path, not a hard-coded localhost API URL.
- Initial administrator creation is intentionally interactive and prompts for
  a password. It uses an advisory lock and does not embed a fixed administrator
  password.
- Existing GitHub Actions CI uses an ephemeral PostgreSQL service and is
  unrelated to public deployment. It does not provision cloud resources.

## Provider Evidence and Feasibility

| Provider option | Zero-cost / card position | Stack and persistence | Demonstration suitability |
| --- | --- | --- | --- |
| Render Free Static Site + Free Web Service + Free Postgres | Render documents that its free tutorial requires no payment, and Free compute plans cost $0. A workspace with a payment method can incur bandwidth/build overages; without one, Render suspends affected free services/builds instead. | Static sites, Docker web services, managed TLS/`onrender.com` URLs, and Postgres are supported. One free Postgres per workspace is limited to 1 GB, has no backups or managed pooling, expires after 30 days, then has a 14-day upgrade grace period before deletion. | **Primary recommendation for a time-bounded capstone demo.** The API spins down after 15 minutes and normally wakes in about a minute; account availability/name/region must still be confirmed in the dashboard. |
| Koyeb Free Web Service + Free PostgreSQL | Koyeb documents one free web service and free PostgreSQL instance, but also documents a required credit card and a validation hold. It is therefore not card-free. | Free web: 512 MB, 0.1 vCPU, 2 GB SSD; it can scale down after one hour. Free Postgres: 0.25 vCPU, 1 GB RAM/storage, only 5 active compute hours per month, sleeps after five minutes. Database service is described as public preview. | **Not recommended.** Mandatory card and five database-active-hours/month make a live demo unreliable. Frankfurt is documented as an available database region. |
| Railway Free / Trial | Railway documents a no-card free trial ($5, 30 days) and then a $0 Free plan with $1 resource credit/month. A full trial depends on automated GitHub verification; otherwise outbound networking is restricted. | Docker/FastAPI, public domain generation, PostgreSQL, reference variables, and a migration pre-deploy command are documented. Free-plan limits are 0.5 GB RAM, one replica, 0.5 GB volume; stateful trial/free data may be deleted 30 days after expiry. | **Fallback only.** It is credit-limited rather than an indefinitely reliable zero-cost service. A low-use demo might fit, but API + PostgreSQL usage can exhaust the monthly credit and stop workloads. |

Official sources consulted:

- Render: <https://render.com/docs/free>,
  <https://render.com/docs/your-first-deploy>,
  <https://render.com/docs/deploys>, and
  <https://render.com/docs/faq>.
- Koyeb: <https://www.koyeb.com/docs/faqs/pricing>,
  <https://www.koyeb.com/docs/databases>, and
  <https://www.koyeb.com/docs/reference/instances>.
- Railway: <https://docs.railway.com/pricing/free-trial>,
  <https://docs.railway.com/pricing/plans>,
  <https://docs.railway.com/pricing/faqs>, and
  <https://docs.railway.com/guides/fastapi>.

Pricing, region capacity, abuse controls, and account eligibility remain
provider- and account-specific and must be reconfirmed in the selected
dashboard immediately before provisioning.

## Render Free-Plan Migration Assessment

The current paid Blueprint cannot be switched to Free unchanged:
Render documents `preDeployCommand` as a paid-service feature. The safe
replacement is a **controlled migration-before-API-start wrapper**, not the
Compose-only fresh-database initializer.

The future wrapper should:

1. Require the managed `DATABASE_URL` and fail before serving if it is absent
   or unusable.
2. Call the existing `migrate_production.py` once at process start.
3. Retain its PostgreSQL advisory lock while `alembic upgrade head` runs.
4. Start Uvicorn only after a zero exit result; migration failure must leave
   the API unavailable rather than serve an incompatible schema.
5. Remain idempotent for a cold start or service restart. `upgrade head` on an
   already-current schema should make no schema change.
6. Never call `initialize_fresh_database.py`, downgrade migrations, reset a
   sequence, drop a database, or create a fixed administrator.

This does add migration time to Free-service cold starts. It is technically
reasonable for a single-instance demonstration, but requires a runtime test
against a disposable public database before being relied on.

## Recommended Architecture

### Primary: Render Free, time-bounded public demonstration

- **Frontend:** Render Static Site (public HTTPS).
- **API:** Render Free Docker web service (public HTTPS), with the approved
  migration-before-start wrapper.
- **Database:** one Render Free PostgreSQL instance in the same region, using
  the managed private `DATABASE_URL`; keep its public IP allowlist empty.
- **Browser communication:** build the frontend with the API public HTTPS URL
  in `VITE_API_BASE_URL`, and set `CORS_ORIGINS` to an exact JSON list of the
  frontend HTTPS origin. Neither value is a database or JWT secret.
- **Secrets:** let Render generate `JWT_SECRET_KEY`; keep database credentials
  in Render environment references only.

### Fallback: Railway Free/Trial

Use only if Render account provisioning is unavailable. Deploy the Docker API,
PostgreSQL service, and static frontend with Railway reference variables and
manual migration configuration. This fallback is not a durable zero-cost
choice because trial verification/network rules and limited recurring credit
can interrupt the demo.

## Initial Administrator and Public Smoke Test

The current interactive bootstrap script is safe for deliberate operator use,
but Render Free web services do not provide shell access. With the database
externally blocked, the current repository has no approved way to execute that
script against a new Render Free database. This is the main functional
deployment blocker.

Two possible future approaches require separate approval and security review:

1. Temporarily allow only the operator's exact public IP in the managed
   database IP allowlist, run the existing interactive local bootstrap using a
   dashboard-supplied connection value, verify the account, then immediately
   restore the empty allowlist. This exposes the database only to that IP for
   the shortest possible window but is still an operational risk.
2. Implement a one-time, secret-controlled bootstrap mechanism that accepts
   operator-provided credentials from platform secrets, consumes/disables its
   bootstrap secret after success, and never logs credentials. This expands
   application behavior and needs a dedicated design and test step.

After an approved bootstrap path, use only disposable demonstration data:

1. Verify API health over HTTPS.
2. Load and refresh the static frontend.
3. Verify one browser API request from the approved origin and rejection from
   an unapproved origin.
4. Sign in with the deliberately created administrator and complete one
   ordinary project workflow.
5. Record URLs and results without recording credentials.

## Exact Future Repository Changes Needed

1. Add a separate free-tier Blueprint, for example `render.free.yaml`, rather
   than silently converting the committed paid `render.yaml`.
2. Set Free API and database plans, remove `preDeployCommand`, preserve the
   private database reference, exact CORS input, static build, and automatic
   deployment policy.
3. Add and test a minimal backend startup wrapper that runs the existing
   advisory-locked production migration then delegates to `start_api.py`.
4. Select that wrapper only in the free Blueprint/Docker command, preserving
   local Compose and paid pre-deploy behavior.
5. Add focused tests for wrapper ordering and fail-closed behavior, plus a
   free-deployment guide that documents the 30-day database expiration,
   cold-start behavior, administrator bootstrap process, and manual recovery.
6. Complete an isolated public-runtime test before describing the deployment
   as verified.

## Commands Executed and Results

- `Get-Content -Raw AGENTS.md` — PASS; project instructions read.
- Read-only inspection of the deployment, migration, configuration, frontend,
  bootstrap, Alembic, CI, and existing-report files — PASS.
- Official provider documentation review through read-only web queries — PASS.
- `git status --short` before creating this report — PASS; the only existing
  pending files were the modified ADIM 8.10.76 report and untracked ADIM
  8.10.88–8.10.91 reports.
- `git diff --check` before creating this report — PASS (no whitespace error;
  Git emitted only an informational line-ending warning for the existing
  ADIM 8.10.76 report).
- No provisioning, billing action, Docker operation, database access,
  migration, staging, commit, push, PR action, or deployment was performed.

## Validation and Test Results

- Repository configuration review: PASS.
- Official provider capability review: PASS, subject to account-specific
  dashboard confirmation.
- Runtime deployment/build/migration/browser verification: NOT RUN by scope.
- Final `git diff --check` and status: to be run after this report is created.

## Issues and Remaining Tasks

1. Render Free Postgres is persistent only for the limited 30-day period; it
   has no backups and cannot support a durable application claim.
2. Render Free API cold starts, restarts, and 750 free-instance-hours/month
   can affect a live demonstration.
3. The current paid Blueprint cannot use its pre-deploy migration feature on
   Free.
4. The interactive administrator bootstrap has no current safe execution path
   for an externally blocked Free Render database.
5. Provider availability, account eligibility, name availability, region
   capacity, and exact dashboard terms remain unverified.

## Final GO / NO-GO Assessment

**GO** to implement a separate, explicitly free-tier Render configuration and
an approved, advisory-locked migration-before-start wrapper for a temporary
October demonstration.

**NO-GO** to call the architecture permanently zero-cost, production-ready,
or deployment-ready today. The administrator-bootstrap decision and a
disposable runtime verification are mandatory before provisioning. It also
does not demonstrate public deployment longevity, production HTTPS ownership,
continuous deployment, observability, alerting, or on-call recovery.

## Recommended Next Step

Approve a narrowly scoped design/implementation step for a separate Render
Free Blueprint, the fail-closed migration-before-start wrapper, and one
security-reviewed administrator-bootstrap method. Do not provision the
services until those changes have been reviewed and validated.
