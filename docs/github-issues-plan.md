# AI BAP — Public GitHub Issue Plan

## Status

These are publication-ready drafts for `imend35/ai-bap`. They have **not** been created remotely because GitHub CLI authentication/access is unavailable in this environment. Before creating any issue, search the public repository for an equivalent open or closed issue to avoid duplicates. Add a real issue ID and URL only after creation.

## Required Fields

Each issue below includes a problem statement, scope, acceptance criteria, verification method, rubric category, dependencies, and agent-assisted evidence guidance. Link only real reports, commits, pull requests, workflow runs, deployments, or dashboards.

---

## 1. Containerize the Full AI BAP Application with Docker Compose

**Problem statement:** `compose.yaml` starts PostgreSQL only, so a reviewer cannot start the frontend, API, and database as one system.

**Scope:** Add frontend/backend container definitions and full-stack Compose with safe environment handling, health checks, migration sequencing, and documented startup.

**Acceptance criteria:**

- One documented Compose command starts frontend, backend, and PostgreSQL.
- API health becomes healthy only after dependencies are ready.
- Frontend reaches the configured backend runtime address.
- Secrets remain external and isolated test topology remains separate.
- A clean-environment smoke path proves persisted UI/API data.

**Verification method:** Run the documented command, inspect health, and complete a browser/API create-and-read smoke path.<br>
**Rubric category:** Application; Containerization.<br>
**Dependencies:** Runtime environment variables and migration startup strategy.<br>
**Agent-assisted evidence:** Link implementation report, test output, and commit/PR after completion.

## 2. Provide One-Command Isolated Test Verification

**Problem statement:** Backend safeguards exist, but no verified command orchestrates required unit, integration, and future frontend tests.

**Scope:** Add a safe entry point that validates the isolated target and runs all required suites without touching development or production data.

**Acceptance criteria:**

- One documented command runs required suites from a clean environment.
- Database checks fail closed without isolation variables/target validation.
- PASS/FAIL output and non-zero failure exit are clear.
- The process does not reset, migrate, or alter development/production databases.

**Verification method:** Execute against the dedicated test topology and record counts, exit code, and isolation evidence.<br>
**Rubric category:** Testing.<br>
**Dependencies:** Frontend test runner; confirmed isolated test procedure.<br>
**Agent-assisted evidence:** Link actual implementation/test report after completion.

## 3. Add Frontend Automated Tests for Critical Workflows

**Problem statement:** The frontend has build/lint scripts but no automated test suite.

**Scope:** Add focused tests for authentication/session behavior, project/archive visibility, and loading or error behavior.

**Acceptance criteria:**

- `frontend/package.json` exposes a documented test command.
- Tests cover an authenticated interaction, archive-aware project workflow, and error/loading state.
- Tests use deterministic mocks or isolated targets and no production credentials.
- The suite is non-interactive and CI-ready.

**Verification method:** Run the frontend test command and record test count/result.<br>
**Rubric category:** Testing.<br>
**Dependencies:** Approved test-runner design and dependencies.<br>
**Agent-assisted evidence:** Link actual code/test reports and CI result.

## 4. Add Pull-Request CI Quality Gates

**Problem statement:** No GitHub Actions workflow validates pull requests.

**Scope:** Add PR CI for backend tests/Ruff and frontend tests/build/lint using safe service configuration.

**Acceptance criteria:**

- Workflow triggers on pull requests targeting `main`.
- Backend tests and Ruff run in an isolated service environment.
- Frontend tests, build, and lint run after the frontend suite exists.
- Logs do not expose credentials or connection secrets.
- Failures are actionable and non-zero.

**Verification method:** Record a real workflow-run URL and results from a test pull request or permitted dispatch.<br>
**Rubric category:** CI/CD.<br>
**Dependencies:** Stable local commands, frontend tests, GitHub Actions permissions.<br>
**Agent-assisted evidence:** Link workflow file, run URL, and report after completion.

## 5. Implement Development CD and Manual Production Deployment

**Problem statement:** The project has no CD path or controlled production release gate.

**Scope:** Deploy validated changes to development automatically and provide separate manually approved production deployment with rollback.

**Acceptance criteria:**

- Successful CI deploys to a non-production development environment.
- Production deployment requires manual approval/action and isolated secrets.
- Health verification and rollback are documented and executable.
- Deployment records identify source commit and target environment.

**Verification method:** Demonstrate development deployment and a non-destructive production workflow/runbook.<br>
**Rubric category:** CI/CD.<br>
**Dependencies:** Hosting, container images, CI workflow, environment separation.<br>
**Agent-assisted evidence:** Link real workflow runs and operational reports.

## 6. Deploy AI BAP Publicly for Reviewer Access

**Problem statement:** No public deployment evidence is available to reviewers.

**Scope:** Deploy the full application over HTTPS with PostgreSQL, environment-based secrets, migrations, health checks, and a reviewer demo path.

**Acceptance criteria:**

- Public HTTPS frontend and backend health URL are reachable.
- Deployed app supports the documented core workflow with reviewer-safe data.
- Secrets are configured outside the repository.
- Migration, backup, health, and rollback procedures are documented.
- README receives URL/demo instructions only after deployment succeeds.

**Verification method:** Access public UI and health endpoint; complete reviewer demo with non-sensitive evidence.<br>
**Rubric category:** Deployment.<br>
**Dependencies:** Full-stack container image, hosting/database decision, TLS, secret access.<br>
**Agent-assisted evidence:** Link deployment report, commit/PR, and real URL.

## 7. Instrument Metrics, Structured Logs, and Distributed Tracing

**Problem statement:** No correlated telemetry UI exists for a key user journey.

**Scope:** Instrument a selected journey, such as login-to-project-list, with shared trace IDs across structured logs, metrics, and traces; collect them in a UI.

**Acceptance criteria:**

- Selected request propagates a trace ID through backend logs and traces.
- A user-impact metric emits without customer data, credentials, or tokens.
- Logs, metric, and trace are collected and visible in a UI.
- Documentation covers data minimization, retention, and access controls.

**Verification method:** Execute journey and show correlated trace, log, and metric using redacted evidence.<br>
**Rubric category:** Observability.<br>
**Dependencies:** Deployment/runtime target and approved telemetry stack.<br>
**Agent-assisted evidence:** Link configuration, dashboard evidence, and report.

## 8. Create a User-Impact Alert and Controlled Trigger

**Problem statement:** No alert is tied to a user-visible failure mode.

**Scope:** Define an alert for a measurable impact such as failed-login or project-read error rate and demonstrate a controlled trigger.

**Acceptance criteria:**

- Condition is based on user-impact metrics, not host-resource graphs alone.
- Alert has non-sensitive service, environment, correlation, and runbook context.
- A controlled trigger delivers it to the approved destination.
- Suppression/rate limiting and resolution behavior are documented.

**Verification method:** Safely trigger in non-production and record delivery/recovery evidence.<br>
**Rubric category:** Alerting on User Impact.<br>
**Dependencies:** Telemetry stack and approved alert destination.<br>
**Agent-assisted evidence:** Link alert rule, runbook, trigger evidence, and report.

## 9. Implement a Controlled On-Call Responder

**Problem statement:** No agent receives a user-impact alert, diagnoses it, and performs a safe recovery.

**Scope:** Implement a narrow responder with alert intake, safe diagnostics, runbook-based diagnosis, auditable reversible remediation or escalation, and human approval boundaries.

**Acceptance criteria:**

- Responder consumes selected alert and correlates it with safe telemetry.
- It follows a documented runbook and identifies impact/cause.
- Automated action is pre-approved, reversible, least-privilege, and logged; otherwise it escalates.
- A controlled end-to-end demonstration proves alert → diagnosis → action/escalation → validation.
- Secrets and customer data never enter prompts, logs, or issue comments.

**Verification method:** Run a controlled non-production incident scenario and retain redacted evidence.<br>
**Rubric category:** On-Call Agent.<br>
**Dependencies:** Alert, telemetry, runbook, approved remediation policy, escalation channel.<br>
**Agent-assisted evidence:** Link responder code/configuration, scenario report, and approval evidence.

## 10. Final Documentation and Submission Verification

**Problem statement:** Final submission needs reproducible evidence and mandatory peer-review completion without unsupported claims.

**Scope:** Verify README, tracker links, deployment/demo, CI/CD, observability/alert/responder evidence, limitations, rubric mapping, and course-platform peer reviews.

**Acceptance criteria:**

- Documentation distinguishes implemented, verified, planned, and blocked work.
- Every claimed rubric point has reviewer-accessible evidence.
- Repository excludes secrets and temporary diagnostics.
- Submission checklist records three completed peer reviews.
- Reviewer can follow a concise demo and verification path.

**Verification method:** Conduct clean-environment/documentation review and obtain Human Product Owner sign-off.<br>
**Rubric category:** Cross-cutting; mandatory peer-review requirement.<br>
**Dependencies:** Relevant implementation issues and course-platform access.<br>
**Agent-assisted evidence:** Link final reports and only real commit/PR/workflow/deployment URLs.

## Agent Usage Evidence Available Now

- `docs/codex-reports/adm_8.10.61.md` — real rubric gap analysis and roadmap work.
- `docs/codex-reports/adm_8.10.62.md` — real agent-team, workflow, and issue-draft work.

No GitHub issue number, public URL, agent comment, or external timestamp is claimed until a human or authenticated automation creates it.
