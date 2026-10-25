# AI BAP — Final Submission Evidence and Rubric Audit

## Purpose and evidence standard

This report maps the repository to the authoritative 24-point rubric in
[`Project.md`](Project.md). Scores are conservative estimates, not course
grades. Repository files and CI evidence are distinguished from owner-reported
production smoke tests and uncommitted local work. The target published
revision is `75833f910aec23d2aaf79ac7c3733c8ac79ed4aa` (`75833f9`).

**Conservative evidence-supported estimate: 17/24.** The rubric requires 10
points to pass. This point estimate does not satisfy the separate mandatory
course requirement to complete three peer reviews; their completion is
**NOT VERIFIED**, and the course rubric says submission without all three does
not pass.

“Verified” below means supported by inspected repository artifacts or the
specific CI/live evidence identified. It does not mean that every workflow was
independently rerun during this documentation task.

## Rubric score

| Criterion | Maximum | Estimated score | Evidence and basis | Remaining gap |
|---|---:|---:|---|---|
| Problem Description | 2 | **2** | README explains the business problem, product functionality, and expected requirement-to-delivery workflow. | None identified for this criterion. |
| Product Specification | 2 | **1** | `product-spec.md` and related specifications exist. A public GitHub Issue #2 includes acceptance criteria. `docs/github-issues-plan.md` explicitly says the issue was created after earlier work and cannot prove agents used a public tracker during that work. | Build prospective evidence that agents use public issues for future tasks; historical tracker-use evidence cannot be backdated. |
| Agent Team Specification | 2 | **2** | `docs/agent-team.md` defines responsibilities, handoffs, and authority boundaries; `docs/agent-workflow.md` describes the collaboration process. | No additional gap identified for the written rubric criterion. |
| Context Management | 2 | **2** | `AGENTS.md` describes development rules and points to modular product, process, team, architecture, and project documents. | None identified for this criterion. |
| Application | 2 | **2** | Full-stack source and database-backed workflows exist. Disposable Compose and browser-project persistence evidence is recorded in `docs/codex-reports/adm_8.10.82.md` and `adm_8.10.168.md`. Owner-reported live smoke checks cover login/dashboard, project and requirements, story linkage, and selected persistence/traceability checks. | The supplied live smoke evidence is selective; the third REQ-004 story omitted AC-08 and AC-09 and its ID is unavailable. It does not verify every workflow. |
| Testing | 2 | **2** | Unit and integration tests, the unified runner, and CI workflow are present. GitHub Actions run [40175160244](https://github.com/imend35/ai-bap/actions/runs/40175160244) for the target commit reported both Backend quality and Frontend quality successful. The README records 589 locally passed backend tests; that is local evidence, not the CI count. | Broader product workflow coverage remains incomplete; do not treat the local count as a fresh rerun or as the GitHub result. |
| Containerization | 2 | **2** | `compose.yaml` defines the database, migration, API, and frontend services with a one-command startup. Prior disposable runtime reports provide local full-stack evidence. | No new Compose runtime was run for this audit. |
| Deployment | 2 | **2** | Public Render frontend/API URLs are documented. The Product Owner confirms Docker deployment of backend and frontend at `75833f9`, `/api/v1/health` as the health-check path, and a healthy live response. | This confirmation is owner-reported rather than independently queried during this documentation audit. |
| CI/CD | 3 | **1** | `.github/workflows/ci.yml` runs quality checks on pull requests and pushes to `main`; the target SHA has a reported successful CI run. Render auto-deploy is disabled and deployment is manual. | No automatic deployment or verified development-environment CD. Manual production deployment alone does not meet the rubric's 2- or 3-point CI/CD tiers. |
| Observability | 2 | **1** | The published target source emits application logs, including controlled AI-provider error logs. It does not provide request-correlated metrics and traces. The rubric's 1-point tier covers logs without metrics/traces or correlation. | No committed, runtime-verified correlated journey metrics/traces with structured logs collected, stored, and viewable in a UI. Local uncommitted observability work is excluded from the published-revision score. |
| Alerting on User Impact | 1 | **0** | No user-impact alert rule or verified alert trigger/notification is present in the published target evidence. | Implement and demonstrate at least one user-impact alert in a safe non-production environment. |
| On-Call Agent | 2 | **0** | The agent-team/workflow documents describe roles and incident boundaries, but no alert-triggered responder that fixes an issue is implemented and demonstrated. | Implement and safely demonstrate an alert-to-response/remediation flow with least privilege and evidence. |
| **Total** | **24** | **17** | Conservative repository and supplied-evidence estimate. | See criterion-specific gaps and mandatory completion requirement. |

### Score interpretation

The total is an evidence estimate against the rubric, not a prediction of the
grader's decision. The most material operational gaps are the missing complete
observability tier, user-impact alerting, and on-call responder. Product
Specification remains at 1/2 because public issue existence is not evidence of
historical agent use.

## Evidence scope and live smoke record

### Published versus local-only

- The published GitHub target used for this audit is commit `75833f9` on
  `main`. CI run [40175160244](https://github.com/imend35/ai-bap/actions/runs/40175160244)
  is associated with that target and reports successful backend and frontend
  quality jobs.
- The working tree contains pending observability implementation,
  configuration, dependency, and documentation changes. They are **not part
  of** `75833f9`, are not included in this score, and must not be represented
  as reviewer-accessible or production-verified capabilities.
- README notes that local observability work remains unverified and does not
  claim it as published or runtime-verified evidence.
- The README records a local backend result of 589 passed. The evidence is
  local; it is not substituted for the exact-commit GitHub Actions result.

### Product Owner-reported production smoke tests

The Product Owner confirms both Render services are deployed at `75833f9` and
provided the following results:

1. Backend `https://ai-bap-api-free.onrender.com/api/v1/health` returned
   `{"status":"healthy"}`.
2. Admin login and Dashboard passed.
3. The **Digital Loan Origination Platform** project was created.
4. Requirements REQ-002, REQ-003, and REQ-004 were created.
5. US-002 and US-003 were created and linked to their requirements.
6. A third story was reported saved for REQ-004. AC-08 and AC-09 were omitted,
   and the generated ID was not supplied; that record's identity and
   completeness cannot be independently checked from the supplied evidence.
7. Persistence and traceability checks passed for REQ-002 and US-002.

No other production test outcome is claimed. The Product Owner confirmed the
runtime is Docker-based and that `/api/v1/health` is the configured Render
health-check path. The health response is owner-supplied evidence; this audit
did not make a production request.

## Manual Render deployment

`render.free.yaml` sets automatic deployment triggers to `off`. The documented
release path is manual through the Render Dashboard: an owner reviews and
selects the intended revision, deploys the backend and frontend services, and
checks health and the intended application workflow. The Free backend startup
wrapper applies Alembic migrations before starting the API and fails closed on
migration/startup failure. No migration was run for this audit, and the
production database's actual schema/state was not inspected. A push or CI pass
must not be described as a deployment.

## Demo access and security boundaries

The planned demo identities remain `banlyst@example.com` and
`reviwer@example.com`; this audit does not establish that either account exists,
is active, or can log in. No passwords or credentials belong in public
documentation. The application's Business Analyst and Reviewer accounts use a
shared workspace, not tenant-isolated data. Any reviewer access must use
synthetic, shareable data and must not be characterized as private or safe for
untrusted users without further isolation controls.

The source at `75833f9` contains backend and frontend restrictions against live
AI generation for those exact identities. Local focused regression results
were six backend cases and twelve frontend App tests. They use isolated or
mocked dependencies and do not prove production enforcement; the supplied
smoke journey did not test the restricted identities or invoke generation.
Authorized non-demo users retain generation only under the existing role and
provider conditions. Saved stories do not have reliably established AI
provenance.

## Mandatory submission requirement outside the 24-point score

`docs/Project.md` requires evaluation of **three other course participants'
projects**. It explicitly states that a submission without all three reviews
does not pass, regardless of rubric points. Completion must be confirmed on
the course platform; this report has no platform evidence and marks it
**NOT VERIFIED**. GitHub reviews, Issues, local audit records, and this report
are not substitutes.

## Submission blockers and minimum remaining work

1. Complete and retain evidence of all three mandatory course-platform peer
   reviews; report status is **NOT VERIFIED**.
2. If seeking points beyond the current estimate, implement and verify
   correlated, privacy-safe journey observability, at least one user-impact
   alert, and the alert-driven on-call responder; configuration or plans alone
   are insufficient.
3. Preserve honest evidence boundaries: do not claim the third REQ-004 story is
   complete, demo accounts are active, public AI restriction enforcement has
   been tested, or screenshots exist without new evidence.
4. Continue to disclose Render Free cold-start and database lifecycle limits,
   manual deployment, and shared-workspace risks.

## Audit validation

- **Repository/source/document inspection:** completed for the target commit,
  rubric, README, User Guide, Render Free configuration/deployment guide,
  agent specifications, issue plan, tests/CI descriptions, and relevant
  existing runtime reports.
- **CI evidence:** target commit's two quality jobs reported successful in run
  `40175160244`; this task did not trigger or rerun CI.
- **Live smoke evidence:** Product Owner supplied results summarized above;
  not independently repeated in this task.
- **Production API/Render revision verification:** Product Owner confirmed the
  deployed SHA, Docker runtime, `/api/v1/health` path, and healthy response;
  independently querying Render was **NOT RUN**.
- **Tests, migrations, Docker, database, production data, AI provider:** **NOT
  RUN / NOT ACCESSED** for this documentation task.
- **Peer reviews:** **NOT VERIFIED**.
