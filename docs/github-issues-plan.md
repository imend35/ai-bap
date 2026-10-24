# AI BAP — Public GitHub Issue Plan

## Status and publication safeguards

This file contains ten numbered local draft records for `imend35/ai-bap`; the original draft identifiers are retained for traceability. They are not GitHub Issues and have no Issue numbers or URLs. The ADIM 8.10.172 live check found no standalone Issues (a closed PR was not counted as an Issue), but the tracker must be checked again immediately before any publication.

The drafts distinguish completed evidence from outstanding tasks. Do not publish completed work as an open implementation task. If a retrospective Issue is useful, label it retrospective, link only real evidence, and state that the Issue was created after the work; never imply that an agent used it earlier. Publication requires Human Product Owner approval. Creating or publishing an Issue does not authorize implementation, deployment, provisioning, billing, or other external changes.

Before publication, search both open and closed Issues for duplicates. Add a real Issue number and URL only after GitHub confirms creation. Never invent comments, timestamps, activity, test results, or evidence links.

## Draft 1 — Containerize the Full AI BAP Application with Docker Compose

**Status: COMPLETED; do not publish as an open implementation task.**

**Original problem:** The initial draft said `compose.yaml` started PostgreSQL only. That statement is outdated: the current Compose configuration defines database, migration, API, and frontend services.

**Completed evidence:** `docs/codex-reports/adm_8.10.82.md` records isolated Compose service health, migration completion, and direct/proxied HTTP checks. `docs/codex-reports/adm_8.10.168.md` records a fresh disposable Compose run and one real-Chrome authenticated project create/reload/retrieval journey, including count-only PostgreSQL persistence verification and ownership-verified cleanup.

**Acceptance evidence:**

- Full stack starts in an isolated disposable Compose project: verified in the cited runtime reports.
- Database, migration, API, frontend, and same-origin proxy become healthy: verified in the cited runtime reports.
- A synthetic least-privileged user creates and retrieves one project through the browser after reload and reauthentication: verified in ADIM 8.10.168 only.
- This evidence does not prove every application workflow, public deployment, or production readiness.

**Verification method:** Review the isolated runtime and E2E reports linked above; do not rerun against shared resources.
**Rubric category:** Application; Containerization.
**Disposition:** Keep as completed local evidence. A separately approved retrospective Issue may link these reports, but must not claim tracker use during prior work.

## Draft 2 — Provide One-Command Isolated Test Verification

**Status: COMPLETED for the documented frontend-plus-backend runner; do not publish as an open implementation task as written.**

**Completed evidence:** `scripts/test-all.ps1` runs frontend tests, then checks the documented fail-closed isolated PostgreSQL environment before running backend Pytest. `docs/testing-strategy.md` records the unified execution result of 4 frontend and 511 backend tests passing. The runner does not start Docker, migrate, or alter a database; browser E2E remains a separate procedure.

**Acceptance evidence:**

- One documented command invokes frontend and backend suites: implemented and recorded.
- Missing/unsafe database setup does not silently pass as a full test run: runner exits nonzero when prerequisites are absent.
- No development or production database is used as a fallback: enforced by the guarded procedure.
- Browser E2E orchestration is not included and must not be implied by this completed scope.

**Verification method:** Review `scripts/test-all.ps1` and the recorded unified-run result in `docs/testing-strategy.md`; confirm the backend target followed the documented isolated guard.
**Rubric category:** Testing.
**Disposition:** Retain the verification report as local evidence. Any future E2E-runner task must be a new, narrowly scoped draft and must not restate the completed runner as missing.

## Draft 3 — Expand Frontend Automated Tests for Uncovered Workflows

**Status: OUTSTANDING, narrowly scoped to demonstrated coverage gaps.**

**Problem statement:** Frontend automated tests exist. Current Vitest coverage includes sign-in rendering and validation, safe login-failure feedback, and a mocked successful login that displays the protected Projects view. One isolated real-browser E2E test covers project creation and persistence after reload. Coverage remains incomplete for other product workflows, including archive-aware interactions and broader loading/error behavior.

**Scope:** Add focused frontend tests for archive-aware project visibility and interaction, plus representative loading and API-error states not already covered by the current tests. Do not duplicate the existing login cases or claim coverage for all product requirements.

**Acceptance criteria:**

- Tests verify active versus archived project visibility and the relevant permitted UI action using deterministic fixtures.
- Tests cover at least one loading state and one API failure state for a selected project workflow not already covered by existing assertions.
- Tests assert accessible user-visible outcomes and do not rely on production credentials or a live external service.
- The suite remains non-interactive under the existing Vitest command and passes in CI.
- The report links the actual test file(s), command output, and CI run after implementation.

**Verification method:** Run `npm run test -- --run`, inspect the named assertions and test count, then verify the frontend CI job for the resulting commit/PR.
**Rubric category:** Testing; Application quality.
**Specification references:** `product-spec.md` FR-001 (active/archived project behavior); `docs/testing-strategy.md` current limitations.
**Dependencies:** Existing Vitest setup and stable mocked API fixtures.
**Agent-assisted evidence:** After publication and authorized work, link the real Issue, changed tests, report, and CI run. Do not backdate tracker use.

## Draft 4 — Verified Pull-Request CI Quality Gates

**Status: COMPLETED and remotely verified; do not publish as an open CI implementation task.**

**Completed evidence:** `.github/workflows/ci.yml` configures frontend and backend quality jobs for pull requests targeting `main` and pushes to `main`. Existing Codex evidence reports record successful runs, including PR-triggered CI and post-merge main CI. CI runs frontend tests/build/lint and backend migration, tests, and Ruff using an ephemeral PostgreSQL service.

**Acceptance evidence:**

- Pull-request workflow and quality jobs: implemented and verified by the recorded run evidence.
- Backend database target is an ephemeral CI service guarded by explicit test configuration.
- Frontend and backend checks completed successfully on the recorded commits.
- CI does not constitute continuous deployment or public deployment.

**Verification method:** Review `.github/workflows/ci.yml` and the exact successful run records in the referenced reports; treat each recorded run as evidence only for its recorded commit/event.
**Rubric category:** CI/CD.
**Disposition:** Keep the workflow and run reports as evidence. Any retrospective Issue must explicitly say it was created after completion and cannot prove agents used the Issue during earlier work.

## Draft 5 — Implement Development CD and Manual Production Deployment

**Status: OUTSTANDING.** No continuous deployment workflow or verified deployment is claimed.

**Problem statement:** CI validates changes, but automated development deployment and a separately controlled production release path are not implemented or verified.

**Scope:** Design and implement an approved development deployment after the deployment target and cost/security gates are accepted; separately provide a manually authorized production deployment path with health verification and recovery guidance.

**Acceptance criteria:**

- A successful, exact-commit CI result gates any development deployment.
- Development and production use separate environments and secrets; secrets are not stored in Git or exposed in logs.
- Production deployment requires an explicit human approval gate.
- A deployment record identifies source commit, target environment, and result.
- Health verification and a tested, non-destructive rollback/recovery procedure are documented.
- Workflow behavior is tested without accidentally deploying production.

**Verification method:** Demonstrate a development deployment and separately verify the production approval gate and recovery procedure; retain real workflow/run evidence.
**Rubric category:** CI/CD.
**Specification references:** `docs/Project.md` CI/CD tiers; `docs/deployment-render.md` and `docs/deployment-render-free.md` for current deployment boundaries.
**Dependencies and gates:** Approved provider, cost/billing review, target environments, secrets, artifact strategy, migration policy, and explicit owner authorization. Issue publication is not authorization to provision or deploy.
**Agent-assisted evidence:** Link only real workflow files, runs, reports, and approvals created after the Issue exists.

## Draft 6 — Deploy AI BAP Publicly for Reviewer Access

**Status: OUTSTANDING; deployment remains NO-GO until its independent security and owner-approval gates pass.** No public AI BAP URL or production operation is verified.

**Problem statement:** Reviewers do not have a verified public application URL or hosted demo.

**Scope:** Subject to explicit owner approval, deploy the application over HTTPS with an approved PostgreSQL strategy, external secrets, safe migrations, health checks, and reviewer-safe data. Do not imply that prepared Render descriptors mean resources have been provisioned.

**Acceptance criteria:**

- A reviewer-accessible HTTPS frontend and API health endpoint are live and verified.
- A documented core workflow completes using non-sensitive reviewer-safe data.
- Secrets are configured outside the repository and are not present in frontend bundles or logs.
- Migration, backup/retention limitations, health, and recovery behavior are verified for the selected provider/plan.
- README deployment/demo links are added only after successful verification and owner approval.
- Public database access is not exposed; CORS and administrator bootstrap are independently checked.

**Verification method:** Verify provider configuration and costs before provisioning; after separate deployment authorization, check HTTPS endpoints and perform a safe reviewer workflow. Record actual evidence and limitations.
**Rubric category:** Deployment.
**Specification references:** `docs/Project.md` Deployment tiers; `docs/deployment-render.md`; `docs/deployment-render-free.md`.
**Dependencies and gates:** Owner approval, provider/eligibility and cost confirmation, secure admin bootstrap, migration safety, CORS, persistence/retention, secrets, and rollback. Publishing this Issue does not authorize paid services, provisioning, or deployment.
**Agent-assisted evidence:** Link the real deployment record, commit/PR, and public URL only after they exist.

## Draft 7 — Instrument Metrics, Structured Logs, and Distributed Tracing

**Status: OUTSTANDING.** Default server logs do not establish the correlated telemetry and viewable UI required by this scope.

**Problem statement:** A key user journey does not have verified, privacy-safe correlated telemetry available in an operator UI.

**Scope:** Select one journey (for example, login-to-project-list), instrument structured logs, metrics, and traces with a shared trace identifier, and collect them in an approved viewable interface.

**Acceptance criteria:**

- A controlled journey emits a correlated trace ID across its structured logs and traces.
- A user-impact metric is emitted without customer content, credentials, or tokens.
- Logs, metrics, and traces are collected, stored, and visible in an operator UI.
- Data minimization, retention, access control, and failure behavior are documented.
- Redacted evidence demonstrates correlation for the selected journey.

**Verification method:** Execute the selected non-production journey and show linked log/metric/trace evidence in the configured UI; review captured fields for sensitive data.
**Rubric category:** Observability.
**Specification references:** `docs/Project.md` Observability tiers; `docs/architecture.md` current operational boundaries.
**Dependencies and gates:** Approved telemetry provider/stack, cost and data-handling review, target environment, and privacy/access policy.
**Agent-assisted evidence:** Link actual configuration, dashboard view, sanitized test evidence, and report after work.

## Draft 8 — Create a User-Impact Alert and Controlled Trigger

**Status: OUTSTANDING.** No user-impact alert or verified trigger is claimed.

**Problem statement:** No demonstrated alert is tied to a user-visible failure rather than a host-resource threshold alone.

**Scope:** Define one measurable user-impact condition, route it to an owner-approved destination, and safely demonstrate trigger, notification, suppression, and recovery in non-production.

**Acceptance criteria:**

- Alert condition uses a user-impact signal such as login or project-read failure rate.
- Alert includes non-sensitive service/environment, correlation, and runbook context.
- A controlled non-production trigger reaches the approved destination.
- Rate limiting/suppression and resolved-state behavior are documented and tested.
- No credentials, tokens, customer data, or sensitive logs are included in notifications.

**Verification method:** Trigger a bounded non-production test event, verify delivery and recovery, then retain redacted evidence.
**Rubric category:** Alerting on User Impact.
**Specification references:** `docs/Project.md` Alerting on User Impact; future telemetry/runbook documentation.
**Dependencies and gates:** Draft 7's selected user-impact telemetry, approved alert destination, delivery credentials managed externally, and owner approval for the test trigger.
**Agent-assisted evidence:** Link the real alert rule, runbook, trigger result, and report; never claim an alert exists before verification.

## Draft 9 — Implement a Controlled On-Call Responder

**Status: OUTSTANDING.** No alert-driven on-call responder or remediation demonstration is verified.

**Problem statement:** There is no verified responder that receives a user-impact alert, diagnoses it, and safely fixes or escalates the issue.

**Scope:** Implement a narrowly scoped responder that consumes an approved alert, uses privacy-safe telemetry and a runbook, and performs only pre-authorized reversible remediation; otherwise it escalates to a human.

**Acceptance criteria:**

- Responder receives the selected alert and correlates it with safe telemetry.
- It follows a documented runbook and reports an evidence-based impact/cause assessment.
- Any automated action is least-privilege, pre-approved, reversible, and auditable; uncertain or privileged actions escalate.
- A controlled end-to-end non-production scenario demonstrates alert → diagnosis → action/escalation → validation.
- Secrets and customer data do not enter prompts, logs, or Issue comments.

**Verification method:** Run a controlled incident simulation, verify the audit trail and recovery/rollback, and retain redacted evidence.
**Rubric category:** On-Call Agent.
**Specification references:** `docs/Project.md` On-Call Agent; `docs/agent-team.md`; `docs/agent-workflow.md` incident handling.
**Dependencies and gates:** Drafts 7 and 8, a reviewed runbook/remediation policy, approved integration and credentials, non-production test target, and explicit human approval boundaries.
**Agent-assisted evidence:** Link responder code/configuration, scenario report, policy approval, and actual validation evidence.

## Draft 10 — Final Documentation and Submission Verification

**Status: OUTSTANDING.** This final audit does not substitute for course-platform peer-review completion.

**Problem statement:** Submission requires accurate reviewer-facing evidence for the project criteria and separate completion of the course's mandatory peer reviews.

**Scope:** Audit README, specification, tracker links, CI/CD, deployment/demo, telemetry/alert/responder claims, limitations, rubric mapping, and course-platform peer-review evidence. Keep repository evidence and course-platform evidence distinct.

**Acceptance criteria:**

- Documentation labels capabilities as implemented, verified, planned, blocked, or not run and links only to real evidence.
- Every claimed rubric point has reviewer-accessible repository or platform evidence.
- No secrets, credentials, or temporary sensitive diagnostics are included in submission materials.
- The three mandatory peer reviews are each independently verified on the course platform; GitHub PR reviews, Issues, and checklists do not count as proof of course completion.
- A concise reviewer demo/verification path is documented and tested to the extent claimed.
- Human Product Owner completes the final acceptance/sign-off decision.

**Verification method:** Perform a clean documentation/evidence audit and separately confirm all three course-platform review records; record evidence sources and unresolved blockers without reproducing private data.
**Rubric category:** Cross-cutting; mandatory course peer-review requirement.
**Specification references:** `docs/Project.md` criteria and Peer Reviewing section; `README.md`; current rubric gap analysis.
**Dependencies:** Accurate Issue/evidence links, actual implementation and CI/deployment/operations evidence as applicable, course-platform access, and Human Product Owner review.
**Agent-assisted evidence:** Link real reports and repository artifacts; record course review completion only from verified course-platform evidence.

## Publication-readiness summary

- **Completed-work evidence — #1, #2, #4:** implementation/verification already exists. Do not publish them as open implementation tasks. A retrospective Issue, if separately approved, must say it was created after the work and cannot demonstrate historical tracker use.
- **Corrected outstanding drafts — #3, #10:** scopes now reflect uncovered frontend testing and the separate final submission/peer-review evidence gates.
- **Outstanding publication candidates — #5–#9:** CD, public deployment, telemetry, user-impact alerting, and responder work remain outstanding. Their publication does not authorize provisioning, spending, or deployment.

The Product Specification criterion remains **1/2** until public task Issues with acceptance criteria exist and there is verifiable evidence of agents using the tracker. The three mandatory course peer reviews remain separately **NOT VERIFIED**.

## Prospective agent-use evidence process

For future work, use this sequence:

1. Obtain owner approval and publish the approved Issue.
2. Record the real Issue number and URL after successful creation.
3. Reference that Issue in subsequent agent task intake and handoffs.
4. Link genuine implementation, tests, reports, commits, PRs, runs, or deployment evidence as it becomes available.
5. Update Issue status/checklists after the work and evidence actually exist.
6. Keep secrets and sensitive personal or customer data out of Issues.

This provides prospective evidence only; it does not fabricate or retroactively claim agent activity before publication.

## Evidence currently available

- `docs/codex-reports/adm_8.10.82.md` — isolated full-stack Compose runtime evidence.
- `docs/codex-reports/adm_8.10.168.md` — isolated authenticated real-Chrome project workflow evidence.
- `docs/testing-strategy.md` and `scripts/test-all.ps1` — current Vitest/backend runner behavior and recorded result.
- `docs/codex-reports/adm_8.10.72.md`, `adm_8.10.76.md`, `adm_8.10.124.md`, and `adm_8.10.150.md` — CI evidence records; use only links and results actually present in those reports.

These are local evidence references, not evidence that the corresponding work was performed under a previously published Issue.
