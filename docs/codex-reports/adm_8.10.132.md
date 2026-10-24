# ADIM 8.10.132 — Deployment Risk Decision Record

## Objective

Record the current Render deployment status and the unresolved deployment-security risks before a separately authorized merge decision for pull request #1. This is a documentation and governance record only; it does not authorize a merge, provisioning, deployment, or platform configuration change.

## PR and repository verification

- Local branch: `docs/ci-pr-evidence`.
- Local `HEAD`: `f66d4a33dc35ba0f1cea486c7eb6f0d838aeeb84`.
- Git index: empty at inspection.
- Pull request: [#1](https://github.com/imend35/ai-bap/pull/1), open and unmerged, from `docs/ci-pr-evidence` into `main`.
- Public GitHub API inspection reported that the PR head matches the local commit, its base remains `main` at `1e4333738947f131816901b9fdb71e4fff61d4f2`, and GitHub currently reports it as mergeable.
- The associated [Continuous Integration run](https://github.com/imend35/ai-bap/actions/runs/39927087481) is a `pull_request` run for the same head commit and completed with conclusion `success`.

The merge-governance procedure and final source review remain documented in [ADIM 8.10.129](adm_8.10.129.md) and [ADIM 8.10.130](adm_8.10.130.md). Neither report constitutes an independent human approval.

## Owner-confirmed Render status

The owner states that no AI BAP Render Web Service, Static Site, or PostgreSQL resource has been created.

**Evidence classification: OWNER-CONFIRMED, NOT INDEPENDENTLY PLATFORM-VERIFIED.** This statement supports the conclusion that no known Render deployment is currently operating, but this review did not inspect a Render account, dashboard, billing configuration, or resource inventory. It must not be treated as direct platform evidence.

## Security findings and severity

| Severity | Finding | Evidence and risk | Decision impact |
| --- | --- | --- | --- |
| MEDIUM | Migration errors may disclose sensitive configuration metadata in platform logs. | `docker/backend/migrate_production.py` resolves the managed connection configuration and does not provide a generic redacting boundary around every configuration, driver, and Alembic failure path. The Free startup wrapper reports a generic failure, but child-process output can still reach the platform log stream. A malformed URL or driver failure could expose configuration metadata. This is a deployment-only risk; no such disclosure was demonstrated. | Blocks public deployment readiness until redaction behavior is hardened and tested. It does not itself change the reviewed PR's merge scope. |
| MEDIUM | CORS and temporary initial-administrator bootstrap secrets require operator verification. | `CORS_ORIGINS` is deliberately operator-supplied in both Render Blueprints, while `docs/deployment-render-free.md` and `docs/bootstrap-admin.md` require temporary bootstrap variables to be removed after first administrator creation. Incorrect CORS can safely prevent the public frontend from reaching the API; retaining bootstrap inputs expands privileged-secret exposure. | Blocks public deployment approval until an operator completes and records the required configuration and cleanup checks. It does not itself change the reviewed PR's merge scope. |

No verified CRITICAL or HIGH finding was identified by the final source review. This record does not convert potential platform risks into verified runtime defects.

## Public-deployment blockers and acceptance criteria

| Blocker | Evidence required to clear it | Status |
| --- | --- | --- |
| Migration failure redaction | A narrowly scoped code hardening change and automated tests showing synthetic configuration/connection failures exit nonzero without emitting secret-like values, followed by review and CI evidence. | Open |
| Explicit CORS configuration | Operator evidence that the exact public HTTPS static-site origin is configured, that the allowed browser API flow succeeds, and that an unintended origin is not accepted. No origin or credential value should be recorded in this report. | Open |
| One-time bootstrap secret lifecycle | Operator evidence that temporary bootstrap inputs were supplied only for initial creation, one administrator was created without defaults, all bootstrap variables were removed, and the service was restarted or redeployed with bootstrap disabled. | Open |
| Managed database and migration safety | Render dashboard/operator evidence that the database is private, persistent as selected, referenced only through managed configuration, and migrations run only through the approved startup strategy. | Open |
| Platform and runtime verification | Authorized public deployment evidence: HTTPS health checks, frontend-to-API behavior, migration result, sanitized log review, and a rollback/recovery check appropriate to the selected plan. | Open |

These are public-deployment gates. They are not evidence that a deployment should be attempted now.

## Merge-versus-deployment decision

The repository contains one GitHub Actions workflow, `.github/workflows/ci.yml`. Its triggers are `push` and `pull_request`; it defines validation jobs and contains no Render provisioning, deployment, or cloud-resource workflow. A merge to `main` can trigger CI but introduces no repository-managed deployment workflow.

Accordingly:

- **Merge readiness:** conditionally separable from deployment readiness. A future controlled merge still requires the final owner GitHub UI governance check and explicit merge authorization described in ADIM 8.10.129. This report does not supply human approval.
- **Public deployment readiness:** **NO-GO**. The two MEDIUM findings and the listed operator/platform evidence gates remain open. No Render resources are known to exist, based only on the owner's statement.

## External integration verification limits

The following remain not independently verifiable from this repository review:

- Render account/resource absence, selected plans, billing eligibility, Blueprint interpretation, and Auto Deploy configuration.
- Managed PostgreSQL privacy, persistence, backups, restore options, and network binding.
- Public HTTPS endpoint availability, real browser CORS behavior, migration execution against a managed database, and platform-log redaction.
- Operator removal of temporary bootstrap inputs after initial administrator creation.
- Production observability, alerting, and on-call response behavior.

## Working-tree preservation

This task created only this untracked report. Existing modified and untracked work, including earlier Codex reports, was not staged, committed, discarded, or otherwise changed.

## Validation

Commands executed:

- Read-only inspection of `AGENTS.md`, ADIM 8.10.129, ADIM 8.10.130, repository state, and workflow triggers.
- Read-only public GitHub API queries for PR #1 and workflow run `39927087481`.
- `git diff --check` (run after creating this report).
- `git status --short` (run after creating this report).

No tests, Docker operations, database operations, Render provisioning, deployment, staging, commits, or pushes were performed.

## Recommended single next action

Before any Render provisioning, obtain separate authorization for the smallest deployment-hardening change: add a redacting migration-failure boundary with focused tests. For a merge decision, separately complete the final owner GitHub UI governance checklist in ADIM 8.10.129 and obtain explicit merge authorization.

## GO / NO-GO

- **GO (conditional):** proceed only to the separately authorized final merge-governance check; merging remains distinct from deployment and no repository deployment workflow is introduced by this PR.
- **NO-GO:** public Render provisioning or deployment until every public-deployment blocker above is closed with operator and platform evidence.
