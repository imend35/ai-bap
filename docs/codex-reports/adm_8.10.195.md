# ADIM 8.10.195 — Accelerated Demo Deployment and Minimum Rubric Readiness Audit

## Step Name and Objective

Read-only assessment of the shortest safe route to a shareable AI BAP demo before October 27, 2026, and evidence for the course's minimum 10/24 score. The requested target is a working public demo by October 26. No implementation, GitHub mutation, provisioning, or deployment was performed.

## Human Product Owner Authorization

Authorization was limited to a read-only audit. The final instruction separately authorized creation of this report only. No other file was changed; no Git, GitHub, CI, Render, or cloud mutation was performed.

## Summary of Completed Work

- Inspected the local Git baseline, deployment Blueprints, API and frontend configuration, startup/migration path, relevant tests and documentation, CI evidence, and the authoritative course rubric.
- Read current official Render documentation on October 24, 2026. The Free topology is statically plausible, but its import/deployment has not been validated in a Render account.
- Found a significant public-demo security decision: public registration creates business-analyst accounts, while project access is shared rather than tenant-isolated. A public writable instance therefore needs an explicit owner risk decision or a separately authorized access-control change before it is safe to expose.
- Supported numeric rubric estimate is **16/24** (conservative treatment of Observability); even a more favorable one-point interpretation does not change the 10-point conclusion. Three mandatory course peer reviews remain **NOT VERIFIED** and are an independent submission gate.
- Deployment and provisioning remain **NO-GO** absent separate authorization.

## Files Inspected

Repository instructions and baseline: `AGENTS.md`, Git remote/status/index, and `docs/Project.md`.

Deployment and runtime: `render.free.yaml`, `render.yaml`, `docs/deployment-render-free.md`, `docs/deployment-render.md`, `docker/backend/Dockerfile`, `docker/backend/start_api_free.py`, `docker/backend/start_api.py`, `docker/backend/migrate_production.py`, backend configuration, app entrypoint, health/auth/project routes, Alembic configuration and migration files, and `backend/tests/test_render_free_deployment_configuration.py`.

Frontend, verification, and project evidence: `frontend/package.json`, Vite configuration, API client and `frontend/src/App.tsx`, `frontend/src/App.test.tsx`, local-only `frontend/playwright.config.ts` and `frontend/e2e/authenticated-project.spec.ts`, `README.md`, `docs/testing-strategy.md`, `docs/project-rubric-gap-analysis.md`, `docs/agent-team.md`, `docs/agent-workflow.md`, product specification, relevant Codex reports, and `.github/workflows/ci.yml`.

## Deployment Readiness Findings

### Local versus committed deployment inventory

The repository is at `f6fff10898fc9a7c3d56a303fba7f50a1b1715e2` on `docs/ci-pr-evidence`, with origin `https://github.com/imend35/ai-bap.git` and an empty Git index. Existing local work was preserved: tracked modifications in `docs/codex-reports/adm_8.10.76.md`, `docs/github-issues-plan.md`, `docs/project-rubric-gap-analysis.md`, `docs/testing-strategy.md`, `frontend/package.json`, and `frontend/package-lock.json`; untracked Codex reports, `frontend/e2e/`, and `frontend/playwright.config.ts` were also present. This report is the only new file authorized by this task.

The Render manifests and application/deployment code inspected are present in the committed tree at this HEAD. The later Playwright E2E artifacts, their report, and the current local documentation/package changes are not part of this HEAD and are local-only. A Git-connected deployment cannot use uncommitted files. Those test artifacts are not needed to run the service, but their evidence is not thereby remote or part of this commit. No existing public Render URL or live resource state was verified; historical owner-reported resource status is not a live provider check.

### Render Free Blueprint readiness

`render.free.yaml` describes a Free PostgreSQL database, a Free Docker FastAPI service, and a static frontend. API and database are configured for Frankfurt; the API takes the database's private `connectionString`, has `/api/v1/health` as its health path, and receives a generated JWT secret. The static site builds `frontend` and publishes `frontend/dist`, receives the API `RENDER_EXTERNAL_URL` as `VITE_API_BASE_URL`, and rewrites SPA paths to `/`. Free services have automatic deployment disabled in this manifest. The API command uses `docker/backend/start_api_free.py`; migration is not delegated to a paid-only pre-deploy hook.

This is structurally plausible from source inspection, not a successful Render Blueprint validation/import. Account eligibility, workspace quota, available Free PostgreSQL slot, region availability, billing/payment status, and actual provider-side service state are **NOT VERIFIED**. Do not select paid `render.yaml` as a substitute for the intended Free configuration.

Current official documentation, checked October 24, 2026:

- Render documents Free web services, static sites, and PostgreSQL, but Free web services spin down after 15 minutes without inbound traffic and typically take about a minute to start again. Free PostgreSQL is limited to 1 GB and expires after 30 days, with a 14-day recovery window; backups are not included. Free filesystems are ephemeral. Usage limits and eligibility still need confirmation in the actual workspace. [Free instance limitations](https://render.com/docs/free)
- Blueprint specifications describe supported service types, environment references, generated values, and static-site routing. This does not prove this repository's Blueprint will import successfully. [Blueprint specification](https://render.com/docs/blueprint-spec)
- Render documents internal database URLs for same-account, same-region services; external PostgreSQL connections require TLS. The manifest's API-to-DB private URL pattern is appropriate for the colocated services. [Connecting to Render PostgreSQL](https://render.com/docs/postgresql-creating-connecting) and [Private networking](https://render.com/docs/private-network)
- Web services must bind to `0.0.0.0`; Render supplies `PORT` (default 10000). The inspected API launcher uses that environment variable and binds to `0.0.0.0`. [Web services](https://render.com/docs/web-services)

Free-tier inactivity means a live demo should be warmed before reviewers arrive. Data durability is unsuitable for production: use synthetic demo data, retain an external safe copy of anything needed for evidence, and expect the Free database to expire. Confirm workspace-specific usage/billing in Render before provisioning; documentation is not a guarantee of this account's entitlement or absence of charges.

## Security and Migration Assessment

| Area | Result | Evidence and implication |
|---|---|---|
| Migration-before-start | **CONDITIONAL GO** | `start_api_free.py` runs the migration wrapper before API execution and treats a nonzero child exit or launch error as fatal. `migrate_production.py` uses the configured database URL, a PostgreSQL advisory lock, and Alembic upgrade-to-head; failures are surfaced generically rather than silently ignored. No migration was run against Render and runtime timing is unverified. |
| Destructive startup/seed behavior | **PASS (static review)** | The Free wrapper does not call the fresh-database initializer or reset production data. Bootstrap creates an initial administrator only when explicitly enabled; no general seed/reset step was found in this startup path. |
| Binding and health | **CONDITIONAL** | `start_api.py` binds `0.0.0.0` and uses `PORT`; manifest health path matches `/api/v1/health`. Health reports application process health, not a live DB query. A successful health check alone cannot establish database persistence. |
| Database and JWT configuration | **CONDITIONAL** | `DATABASE_URL` is treated as a secret and checked as PostgreSQL; `JWT_SECRET_KEY` is secret-valued and requires at least 32 characters. Blueprint supplies private DB reference and generated JWT value. Actual values and Render TLS behavior were not inspected or changed. |
| CORS and frontend API | **CONDITIONAL** | Backend uses exact configured `CORS_ORIGINS` and does not allow credentialed cookies; bearer auth is used. Set the exact deployed HTTPS static-site origin after its URL exists. The frontend's production API base must resolve to the API HTTPS URL. Public browser behavior has not been tested. |
| Bootstrap lifecycle | **MANUAL GATE** | Deployment guide requires temporary initial-admin bootstrap environment settings in the Render dashboard for first startup, then removal of all bootstrap settings and a controlled restart/deploy. This lifecycle has not been executed. No bootstrap credentials should be committed or placed in the static frontend environment. |
| Public account/data boundary | **NO-GO for an unqualified public writable demo** | `backend/app/routers/auth.py` exposes registration that creates active `business_analyst` users. Project routes allow business analysts to list/create (and applicable project actions) in the shared project store; inspection found no per-user tenant ownership boundary or public-registration throttling in these paths. A visitor can create/alter shared demo content and may enumerate it. Use only synthetic data and obtain explicit owner acceptance of this short-lived writable shared-demo risk, or separately authorize a safe guest/read-only or ownership/access-control design. Do not expose real or confidential user data. |
| Logging/errors | **PASS with limits** | Migration failures are redacted to generic operator messages; settings use secret wrappers. No secret values are included in this report. No live Render logs or public error behavior were assessed. |

Security configuration names to set/review are `DATABASE_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS`, `PORT`, `VITE_API_BASE_URL`, and the temporary `AI_BAP_INITIAL_ADMIN_BOOTSTRAP_*` settings. Never place secrets in committed files, client-visible `VITE_*` variables, or reports. No production credentials or user data are appropriate for this demo.

## Frontend/API Integration Audit

The static frontend service's configured build and publish paths align with Vite's output (`npm ci`, `npm run build`, `frontend/dist`). The SPA catch-all rewrite supports client-side routes and refresh. `VITE_API_BASE_URL` is injected at build time from the API service URL; the browser then calls that URL over HTTPS. CORS must be updated with the actual exact frontend origin. These relationships are source-level findings only: no hosted URLs, browser requests, CORS preflight, deep-link refresh, or Render build were exercised.

The auth API supports login/registration, and project UI/API behavior is implemented. A successful local isolated Chrome test previously verified one login → Projects → create project → success status → reload/reauthentication → project retrieval flow, with one count-only persistence check against disposable PostgreSQL. That evidence is local and is recorded in untracked `docs/codex-reports/adm_8.10.168.md`; it is not a public deployment test. It does not establish all requirements/story/acceptance criteria/traceability flows, public auth, or production infrastructure.

## Minimum Viable Demo Workflow

Recommended five-minute story, using only synthetic content and a warmed instance:

1. Open the public HTTPS frontend and show the sign-in page; confirm no browser console/API/CORS error.
2. Sign in with the deliberately prepared demo account. Keep credentials private and rotate/remove temporary bootstrap material after initial setup.
3. Open Projects, create one synthetic business-analysis project, and show the success status.
4. Refresh/re-authenticate if needed and show the project remains available. Treat this as application behavior evidence, not backup/durability evidence.
5. If the UI is stable and time permits, show one existing requirements workflow. Do not promise story generation or AI output in the demo unless it is verified; OpenAI configuration is optional and should not be a deadline dependency.
6. Show the API health URL as an operational check, while explaining that this endpoint does not itself test PostgreSQL. A successful project list/create is the DB-path smoke check.

Acceptance: frontend is HTTPS and refreshable; API health returns 200; sign-in works; project list loads; synthetic project create is confirmed; project remains after page refresh/reauth; browser network requests succeed; no real data is used. Keep a local/demo fallback ready because Free services sleep and cold-start. Only the project workflow has prior real-browser E2E evidence, and that was local.

## Rubric Evidence and Conservative Score

Authoritative wording is in `docs/Project.md`: twelve criteria, maximum 24 points, numeric passing threshold 10 (around lines 37–107). It separately makes three peer reviews mandatory for submission (around line 28). The matrix below applies conservative scores to evidence available at this baseline; it is an estimate, not a course-grader decision.

| Criterion | Max | Conservative score | Evidence/status | Missing evidence / deployment impact |
|---|---:|---:|---|---|
| Problem Description | 2 | 2 | `product-spec.md`, charter and project documentation — **VERIFIED** | No apparent score dependency on live deployment. |
| Product Specification | 2 | 2 | Public tracker Issue #2, issue-driven implementation/PR and CI evidence; `docs/github-issues-plan.md` contains local changes, but live Issue #2 was previously verified — **VERIFIED with evidence-date limitation** | Current issue state is not freshly queried in this audit; deployment not required. |
| Agent Team Specification | 2 | 2 | `docs/agent-team.md`, `docs/agent-workflow.md` — **VERIFIED** | Do not confuse repo agent evidence with course peer reviews. |
| Context Management | 2 | 2 | `AGENTS.md` and modular project documentation — **VERIFIED** | None identified for score; peer reviews remain separate. |
| Application | 2 | 2 | Implementation and one isolated authenticated Chrome project flow — **PARTIALLY VERIFIED in breadth, score supported by implemented application** | Only one local workflow E2E-tested; does not establish all features. Public deployment is not required for the 2-point application tier as read. |
| Testing | 2 | 2 | CI run [40048651886](https://github.com/imend35/ai-bap/actions/runs/40048651886): frontend 8/8, backend 560, migration and Ruff passed — **VERIFIED for CI head** | CI is not public-browser or Render testing; deployment not needed for this criterion. |
| Containerization | 2 | 2 | Docker/Compose definitions and isolated local runtime evidence — **VERIFIED** | Local-only evidence/report is not remotely committed at this baseline; no score deduction assumed. |
| Deployment | 2 | 1 | Free deployment manifest and procedure exist — **PARTIALLY VERIFIED** | The rubric's 1-point tier is documented procedure; 2 points require public deployment/live demo. Deployment would add one point, but is not needed to reach numeric threshold. |
| CI/CD | 3 | 1 | GitHub Actions PR CI — **VERIFIED** | No verified continuous deployment; higher tiers require CD. No deployment claim. |
| Observability | 2 | 0 | No verified structured telemetry collection, correlated journey metrics/traces, storage or dashboard — **NOT VERIFIED for rubric tier** | Default Uvicorn logs may be argued as basic logs, but are not counted absent evidence. Deployment is not sufficient by itself. |
| Alerting | 1 | 0 | No verified user-impact alerting — **NOT VERIFIED** | No alert evidence. |
| On-Call Agent | 2 | 0 | No verified on-call agent — **NOT VERIFIED** | No on-call evidence. |
| **Total** | **24** | **16** | **Conservative supported estimate** | One point may be added if an evaluator accepts default Uvicorn logs for basic Observability. This does not change the threshold result. |

Arithmetic: `2+2+2+2+2+2+2+1+1+0+0+0 = 16/24`. Numeric margin over the 10-point threshold is six points. The 10-point threshold is supported by the rubric and this evidence-based estimate, but the score itself remains subject to evaluator judgment. A public URL increases the Deployment criterion from 1 to 2 if verified; it is not a separate numeric 10-point prerequisite under the criterion table.

### Mandatory Submission and Peer-Review Rules

`docs/Project.md` distinguishes scoring from submission: three course-platform peer reviews are required; all three remain **NOT VERIFIED**. GitHub reviews on PR #3, Sourcery approvals, and issue/PR activity cannot substitute. Thus numeric minimum readiness is **CONDITIONAL GO**, but final submission readiness is **NO-GO** until actual course-platform evidence confirms all three required reviews. A public demo is the stated target and would improve Deployment scoring, but the rubric's numeric threshold can be met without it on this estimate.

## Risks and Blockers

| ID | Severity | Blocker / scope | Evidence and smallest safe next action | Validation / authorization / effort |
|---|---|---|---|---|
| B1 | HIGH | Public writable demo exposes a shared project workspace | Public registration creates active BA accounts and project routes operate on shared records. Before provisioning, owner must either explicitly accept a synthetic-only, short-lived shared writable demo risk or separately authorize a safer read-only/ownership-bound demo access change. | Verify guest/public access behavior and role restrictions with tests; owner risk acceptance or implementation authorization required; M–L depending on design. Blocks public exposure absent disposition. |
| B2 | HIGH | Current Render workspace entitlement/cost is unknown | Free slot, quota, billing/payment and region availability are account-specific and were not accessed. Confirm the exact workspace can use the intended Free services and no paid service is selected. | Dashboard review before any create action; owner authorization; XS. |
| B3 | MEDIUM | Initial admin bootstrap is a manual one-time lifecycle | Guide requires temporary bootstrap env values and their removal after first successful startup. | Verify admin login, remove bootstrap variables, controlled redeploy/restart, verify service still starts; separate owner/deployment authorization; XS. |
| B4 | MEDIUM | Hosted URL/CORS/frontend build integration is untested | Exact HTTPS origin and API URL are only known after service URLs exist. | Configure exact `CORS_ORIGINS`, verify frontend build value and browser preflight/login; deployment authorization; S. |
| B5 | MEDIUM | Blueprint import, migrations and DB-backed runtime are unverified in Render | Static config/tests do not equal provider runtime; health route is process-only. | Deploy only after approval; check migration completion, health, then actual authenticated list/create/refresh and logs; M. |
| B6 | MEDIUM | Free services unsuitable for durable production | 15-minute sleep, ephemeral web filesystem, 1 GB/30-day DB, no included backups. | Use synthetic data, explain cold starts/expiry, keep needed evidence elsewhere; provider doc check and user disclosure; XS. Does not necessarily block a short demo. |
| G1 | HIGH (submission) | Three mandatory peer reviews unverified | Course rubric explicitly requires three. | Obtain/retain authentic course-platform completion evidence; no GitHub proxy. Blocks final submission, not technical deployment. Effort depends on course schedule. |

Can defer: advanced observability, alerts, on-call agent, production-grade durability, full FR-001–FR-009 browser coverage, AI-provider integration, paid `render.yaml` route. Do not let these displace the required peer reviews or safe demo decision before the deadline.

## GO / NO-GO Decisions

| Decision area | Result | Rationale |
|---|---|---|
| Free deployment configuration | **CONDITIONAL GO** | Static manifest is coherent; provider import, workspace quota and account eligibility unverified. |
| Security readiness | **NO-GO** for public writable demo until owner explicitly accepts the shared synthetic-data risk or separately authorizes safe access-control work. |
| Migration-before-start | **CONDITIONAL GO** | Source fails closed and CI migration tests passed; actual Render timing/DB behavior not tested. |
| Frontend/API integration | **CONDITIONAL GO** | Static URL/CORS wiring is plausible; exact hosted URLs and browser requests unverified. |
| Minimum live-demo workflow | **CONDITIONAL GO** | One local isolated project workflow passed; hosted login/connectivity/persistence still need verification. |
| Minimum 10-point rubric evidence | **CONDITIONAL GO** — estimated 16/24, threshold 10/24 | Numeric evidence supports threshold; score not official and peer reviews remain a separate mandatory submission blocker. |
| Overall cloud authorization | **NO-GO** | This audit authorizes no provisioning or deployment; B1/B2 also need disposition. |

## Risks and Blockers — October 24–26 Execution Plan

**October 24:** Complete this audit; obtain an explicit owner decision on the public shared-write demo risk; verify Render workspace Free eligibility/quota/cost and choose only `render.free.yaml`. If risk is not accepted, request a separate narrowly scoped access-control implementation authorization. Confirm peer-review obligations and start collecting authentic course evidence. Do not create services today under this authorization.

**October 25:** Only after separate explicit deployment authorization and resolved B1/B2: create the Free Blueprint resources; verify the plan of every resource before confirming; configure generated JWT and exact CORS/frontend URL; perform temporary first-admin bootstrap; deploy and inspect migration/startup logs without exposing secrets; remove bootstrap settings and controlled redeploy; test API and static site. Stop if any paid resource, unexpected charge, unsafe migration, or permission failure appears.

**October 26:** Warm services shortly before demonstration. Run the five-minute synthetic workflow: HTTPS load, API health, login, project list/create, refresh/re-authentication, persisted project retrieval; optionally show a requirements screen only if verified. Capture redacted evidence and actual URLs. Verify the three course peer reviews independently. Keep a local isolated fallback in case cold-start, quota, or hosted integration fails.

**October 27:** Deadline buffer only; do not use the buffer to bypass security, payment, or peer-review requirements.

This is a proposed sequence, not a schedule or authorization to execute it.

## Recommended Next Step

Obtain one explicit Human Product Owner decision on whether a short-lived, synthetic-data-only but publicly writable shared demo is acceptable; if not, request a separately scoped safe demo-access change before any Render provisioning.
