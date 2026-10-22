# AI BAP — Agent-Assisted Delivery Workflow

## Purpose

This workflow complements `AGENTS.md`, [agent-team.md](agent-team.md), the product specification, and the architecture document. It does not grant authority beyond explicit Human Product Owner authorization.

## 1. Task Intake

1. Record the problem, outcome, deadline, and constraints in a GitHub Issue when the public tracker is available.
2. Identify the product requirement, user journey, architecture boundary, and existing evidence.
3. Classify the task as documentation, frontend, backend, database, infrastructure, observability, or incident work.
4. Stop for human direction when scope, authority, sensitive data, or production impact is unclear.

## 2. Requirement Clarification and Acceptance Criteria

- Translate the request into observable acceptance criteria, negative cases, dependencies, and non-goals.
- Keep planned capabilities distinct from implemented behavior.
- Capture required authorization boundaries for data changes, secrets, external services, deployment, and Git operations.
- Update material scope only with Human Product Owner approval.

## 3. Implementation Planning

- Inspect relevant source, tests, contracts, migrations, and documentation before editing.
- Plan the smallest safe change, affected files, validation commands, rollback considerations, and handoff.
- Verify migration ordering and isolated-test safety before database work.
- For operational work, define health checks, rollback, data protection, and evidence before implementation.

## 4. Implementation and Review

- Keep changes focused and preserve unrelated working-tree changes.
- Update contracts and documentation when externally visible behavior changes.
- Request explicit approval before dependency installation, schema modification, external-service configuration, deployment, commit, push, or destructive action.
- Review diffs for debug output, temporary files, secrets, and unsupported claims.

## 5. Test Verification

- Run only authorized checks from the correct directory and environment.
- Use the isolated PostgreSQL test procedure for database-backed tests.
- Record exact commands and actual PASS, FAIL, or NOT RUN results.
- Treat unexecuted tests as unverified even when a historical report records a pass.

## 6. Human Review and Approval

Submit the implementation summary, affected files, validation evidence, residual risks, and requested decision to the Human Product Owner. Do not commit, push, deploy, or alter shared resources unless explicitly authorized.

## 7. GitHub Issue Updates

Each public issue records the requirement, acceptance criteria, implementation scope, dependencies, verification evidence, status, blockers, and Human Product Owner decision. Issues must never contain passwords, tokens, connection strings, personal data, or copied sensitive logs.

## 8. Evidence Collection

- Keep evidence in tests, configuration, documentation, and `docs/codex-reports/`.
- Link rather than duplicate evidence.
- Label claims as implemented, verified, planned, blocked, or not run.
- Preserve original reports; create a new step report rather than rewriting history.

## 9. Incident Handling

1. Receive a user-impact alert only through an approved integration.
2. Collect minimum safe telemetry and redact credentials and customer data.
3. Match the symptom to a runbook and classify the response as observe, propose, reversible remediation, or escalate.
4. Require approval for privileged, destructive, irreversible, or production-changing action unless narrowly scoped policy explicitly permits it.
5. Record alert, diagnosis, action, validation, rollback state, and a follow-up issue.

## Complete Handoff

A handoff contains the issue link when available, requirement, changed paths, validation commands/results, known limitations, security considerations, evidence links, and the explicit next-owner decision.
