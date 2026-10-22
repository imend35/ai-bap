# AI BAP — Revised Project Roadmap for October 22–27, 2026

## Goal

Move AI BAP from a conservatively estimated **8/24** to a demonstrably passing, reviewable final-project submission while preserving the existing application behavior and security boundaries.

## Non-Negotiable Submission Requirement

Complete **three peer reviews** through the course platform. The rubric states that a submission without three peer reviews does not pass, irrespective of project score. This is an external, manual requirement and should be completed early rather than left to the final day.

## Priority Roadmap

| Priority | Window | Deliverable | Rubric impact | Dependencies | Effort / risk | Acceptance evidence |
| --- | --- | --- | --- | --- | --- | --- |
| P0 | Oct 22 | Create a public task tracker with atomic tasks, acceptance criteria, links to implementation/PR evidence, and documented agent participation. | Product Specification: 1 → 2 | Repository access and a chosen public tracker. | Low effort; external setup risk. | Public URL, visible tasks with acceptance criteria, linked work evidence. |
| P0 | Oct 22 | Define the agent team and collaboration process in modular documentation; link it from AGENTS.md. | Agent Team: 1 → 2; Context: 1 → 2 | Decision on roles and review gates. | Low effort; claims must reflect actual practice. | Roles, handoffs, escalation, context sources, and tracker workflow in repository docs. |
| P0 | Oct 22–23 | Complete three mandatory peer reviews. | Mandatory submission requirement; no points | Course platform access. | Manual coordination risk. | Platform confirmation/screenshots or platform-recorded completion. |
| P1 | Oct 23–24 | Verify the implemented full-stack Compose runtime. | Application: 1 → 2; Containerization: 1 → 2 | Isolated Compose build, service health checks, and smoke-test evidence. | Medium; service readiness and migration ordering. | One documented Compose command starts app, database, and frontend in a disposable environment. |
| P1 | Oct 23–24 | Extend the implemented frontend automated tests for critical user journeys. | Testing: 1 → 2 | Additional Vitest/RTL coverage for project flows and error/loading states. | Medium; dependency and React state complexity. | Test files, repeatable command, passing results in a clean environment. |
| P1 | Oct 24 | Maintain and verify the one-command test runner. | Testing evidence | Preserve safe database requirements and capture frontend and backend suite evidence. | Medium; database lifecycle safety. | One documented command or task runner with passing output and isolation safeguards. |
| P1 | Oct 24–25 | Capture pull-request CI evidence for the implemented workflow. | CI/CD: 0 → 1 | Verify existing lint, build, frontend tests, and backend tests with ephemeral PostgreSQL on a pull request. | Low; secrets and service containers. | PR run URL/status and reproducible logs. |
| P2 | Oct 25 | Deploy the containerized application to a public, HTTPS-accessible environment and document a reviewer demo path. | Deployment: 0 → 2 | Hosting account, managed PostgreSQL, secret configuration, migrations. | Medium/high; operational and cost risk. | Public URL, successful health/API/UI demo, deployment runbook. |
| P2 | Oct 25–26 | Extend CI/CD: automatic dev deployment from CI, with a separate manual production deployment action. | CI/CD: 1 → 3 | Working deployment environments and secrets. | High; environment separation and rollback. | Workflow evidence for CI, dev deploy, manual production gate, rollback procedure. |
| P2 | Oct 25–26 | Instrument one key journey (for example login → project list) with structured logs, metrics, and traces sharing a trace ID; provision a UI. | Observability: 0 → 2 | Telemetry stack/hosted provider; privacy design. | High; avoid customer data and secrets. | Trace, metric, and structured-log views for the same request, plus data-safety review. |
| P2 | Oct 26 | Define and demonstrate one user-impact alert (for example failed login or project-read error rate). | Alerting: 0 → 1 | Observability metrics and alerting service. | Medium. | Alert rule, controlled trigger, delivered alert evidence. |
| P2 | Oct 26 | Implement a tightly scoped on-call responder agent that receives the alert, collects safe context, diagnoses, and performs an approved low-risk recovery or escalation. | On-Call Agent: 0 → 2 | Alert transport, telemetry queries, constrained remediation/runbook. | High; safety and proof risk. | Triggered end-to-end demonstration, safe action logs, guardrails, and rollback/escalation behavior. |
| P3 | Oct 27 | Final reproducibility pass and submission package: README, tracker links, public URL, workflow runs, telemetry/alert/on-call evidence, and known limitations. | Protects all points | All previous work. | Medium; deadline risk. | Fresh-environment checklist and reviewer-oriented demo script. |

## Recommended Implementation Sequence

1. **First secure the pass path:** peer reviews, public tracker, agent-team documentation, and modular context links. These can bring the documentation/process categories to full credit and avoid a non-technical submission failure.
2. **Make the app run as one system:** implement full-stack Compose before adding deployment or CI. This is the foundation for reliable local demonstration and service-based CI.
3. **Close testing and CI:** add a small, meaningful frontend suite, retain isolated database safeguards, and make CI execute the same validation commands.
4. **Deploy only after the local runtime is stable:** use environment-specific secrets, managed persistence, migration discipline, health checks, and a documented rollback path.
5. **Build observable operations last but deliberately:** implement one user journey end-to-end rather than superficially adding many signals. The alert and responder must be demonstrable and safe.

## Achievable Score Scenarios

| Scenario | Estimated score | Conditions |
| --- | ---: | --- |
| Current documented repository | 8 / 24 | Conservative assessment in `project-rubric-gap-analysis.md`. |
| Passing documentation/process path | 11 / 24 | Public tracker with agent evidence; agent-team and modular context documentation; three peer reviews completed. |
| Strong local engineering submission | 15 / 24 | Above plus full-stack Compose, frontend tests/full verification, and PR CI. |
| Production-ready target | 24 / 24 | Above plus public deployment, complete CD, correlated telemetry UI, user-impact alert, and demonstrated on-call responder. |

## Risk Controls

- Do not expose secrets in Compose files, workflows, logs, alert payloads, or screenshots.
- Keep database migrations forward-only and never point test automation at development or production data.
- Do not call an on-call agent autonomous unless its actions are explicitly scoped, reversible, auditable, and approved.
- Prefer a verifiable, narrow vertical slice over broad but unproven infrastructure claims.
- Do not claim a rubric point until its evidence can be shown to a reviewer.
