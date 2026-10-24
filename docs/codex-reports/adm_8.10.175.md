# ADIM 8.10.175 — Approved GitHub Issues Publication Plan

## 1. Objective

Prepare seven duplicate-checked, owner-approved local draft bodies for later human-reviewed publication. This is plan-only: no GitHub Issue or repository setting was created or changed, and no implementation or deployment was authorized.

## 2. Human Product Owner authorization boundary

The owner approved the publication-planning scope for local drafts **#3, #5, #6, #7, #8, #9, and #10**. This authorizes preparing candidate text only. It does not authorize publishing during this step, implementing tasks, activating CI/CD, provisioning cloud resources, spending money, changing secrets, committing, pushing, or merging.

## 3. Git baseline

- Branch: `docs/ci-pr-evidence`
- HEAD: `2afe0d4d88188ad0a8de14c590ca95d0536b1241`
- Git index: empty at inspection.
- Existing modified tracked paths: `docs/codex-reports/adm_8.10.76.md`, `docs/github-issues-plan.md`, `docs/project-rubric-gap-analysis.md`, `docs/testing-strategy.md`, `frontend/package-lock.json`, and `frontend/package.json` (six tracked modifications, including the already-pending local issue-plan correction).
- Existing untracked paths: 58 status entries before this report: 56 Codex reports, `frontend/e2e/authenticated-project.spec.ts`, and `frontend/playwright.config.ts`.

All pre-existing changes were preserved. This report is the only file created by this step.

Pre-existing untracked paths:

```text
docs/codex-reports/adm_8.10.102.md
docs/codex-reports/adm_8.10.103.md
docs/codex-reports/adm_8.10.105.md
docs/codex-reports/adm_8.10.106.md
docs/codex-reports/adm_8.10.107.md
docs/codex-reports/adm_8.10.111.md
docs/codex-reports/adm_8.10.112.md
docs/codex-reports/adm_8.10.113.md
docs/codex-reports/adm_8.10.114.md
docs/codex-reports/adm_8.10.116.md
docs/codex-reports/adm_8.10.118.md
docs/codex-reports/adm_8.10.120.md
docs/codex-reports/adm_8.10.121.md
docs/codex-reports/adm_8.10.122.md
docs/codex-reports/adm_8.10.123.md
docs/codex-reports/adm_8.10.124.md
docs/codex-reports/adm_8.10.125.md
docs/codex-reports/adm_8.10.127.md
docs/codex-reports/adm_8.10.129.md
docs/codex-reports/adm_8.10.130.md
docs/codex-reports/adm_8.10.132.md
docs/codex-reports/adm_8.10.134.md
docs/codex-reports/adm_8.10.135.md
docs/codex-reports/adm_8.10.140.md
docs/codex-reports/adm_8.10.141.md
docs/codex-reports/adm_8.10.142.md
docs/codex-reports/adm_8.10.143.md
docs/codex-reports/adm_8.10.144.md
docs/codex-reports/adm_8.10.145.md
docs/codex-reports/adm_8.10.147.md
docs/codex-reports/adm_8.10.148.md
docs/codex-reports/adm_8.10.150.md
docs/codex-reports/adm_8.10.151.md
docs/codex-reports/adm_8.10.152.md
docs/codex-reports/adm_8.10.153.md
docs/codex-reports/adm_8.10.154.md
docs/codex-reports/adm_8.10.155.md
docs/codex-reports/adm_8.10.156.md
docs/codex-reports/adm_8.10.157.md
docs/codex-reports/adm_8.10.158.md
docs/codex-reports/adm_8.10.159.md
docs/codex-reports/adm_8.10.164.md
docs/codex-reports/adm_8.10.165.md
docs/codex-reports/adm_8.10.166.md
docs/codex-reports/adm_8.10.167.md
docs/codex-reports/adm_8.10.168.md
docs/codex-reports/adm_8.10.169.md
docs/codex-reports/adm_8.10.170.md
docs/codex-reports/adm_8.10.171.md
docs/codex-reports/adm_8.10.172.md
docs/codex-reports/adm_8.10.173.md
docs/codex-reports/adm_8.10.174.md
docs/codex-reports/adm_8.10.88.md
docs/codex-reports/adm_8.10.89.md
docs/codex-reports/adm_8.10.90.md
docs/codex-reports/adm_8.10.91.md
frontend/e2e/authenticated-project.spec.ts
frontend/playwright.config.ts
```

## 4. Documents inspected

Read `AGENTS.md`, `docs/Project.md`, `docs/github-issues-plan.md`, `docs/codex-reports/adm_8.10.172.md`, `docs/codex-reports/adm_8.10.173.md`, `docs/codex-reports/adm_8.10.174.md`, root `product-spec.md`, `docs/agent-team.md`, and `docs/agent-workflow.md`. Also checked current testing and deployment evidence referenced by the seven drafts, including `docs/testing-strategy.md`, `scripts/test-all.ps1`, `frontend/src/App.test.tsx`, `.github/workflows/ci.yml`, `docs/codex-reports/adm_8.10.168.md`, and `docs/codex-reports/adm_8.10.150.md`.

## 5. Live GitHub repository verification

Fresh read-only GitHub API queries returned:

- Repository identity: `imend35/ai-bap` (repository ID `1418730977`; default branch `main`).
- Visibility: `public`.
- Issues enabled: `has_issues = true`.
- Open standalone Issues: none.
- Closed standalone Issues: none.
- The closed Issues endpoint returned PR #1, [docs: record GitHub Actions CI evidence](https://github.com/imend35/ai-bap/pull/1), with a `pull_request` marker. It is excluded from the standalone Issue inventory and duplicate matching.

The configured remote URL was inspected in sanitized form and identifies `github.com/imend35/ai-bap`. No credentials were displayed. Both repository metadata and issue-list API access succeeded; duplicate verification is not blocked.

## 6. Open and closed Issue inventory

| State | Standalone Issue count | Inventory result |
|---|---:|---|
| Open | 0 | No standalone items returned. |
| Closed | 0 | No standalone items returned. |
| Closed pull request, excluded | 1 | PR #1 only; not a task Issue. |

This inventory is a live snapshot at this review. Repeat the duplicate check immediately before any later creation because the tracker may change.

## 7. Duplicate-detection matrix

All seven approved drafts were compared with the complete current open/closed standalone Issue results by title, scope, acceptance criteria, implementation area, and evidence links. Since those result sets contain no standalone Issues, no title/scope/criteria/evidence duplicate was found in the queried inventory. PR #1 was not treated as an Issue.

| Local draft | Title/scope match in open Issues | Match in closed Issues | Similarity/overlap assessment | Duplicate result |
|---:|---|---|---|---|
| #3 | None; open inventory empty. | None; closed standalone inventory empty. | Frontend test work is distinct from PR #1; PR #1 is a documentation CI PR, not an Issue. | No duplicate found in current snapshot. |
| #5 | None; open inventory empty. | None; closed standalone inventory empty. | Development CD/manual production gates are distinct from the existing CI workflow and from public-demo deployment. | No duplicate found in current snapshot. |
| #6 | None; open inventory empty. | None; closed standalone inventory empty. | Public deployment is related to #5 but has distinct public URL, security, persistence, and demo acceptance criteria. | No duplicate found in current snapshot. |
| #7 | None; open inventory empty. | None; closed standalone inventory empty. | Correlated telemetry is an upstream operational capability, not an alert or responder. | No duplicate found in current snapshot. |
| #8 | None; open inventory empty. | None; closed standalone inventory empty. | Alert rule/trigger depends on telemetry (#7); not duplicate scope. | No duplicate found in current snapshot. |
| #9 | None; open inventory empty. | None; closed standalone inventory empty. | Responder/remediation is downstream from telemetry and alerting (#7/#8); not duplicate scope. | No duplicate found in current snapshot. |
| #10 | None; open inventory empty. | None; closed standalone inventory empty. | Final evidence audit is cross-cutting; mandatory course reviews are distinct from GitHub PR reviews and Issues. | No duplicate found in current snapshot. |

## 8. Seven proposed Issue titles and full bodies

The following bodies are publication candidates, not remote Issue content. Paths are given as repository paths rather than fabricated Issue IDs or links. Before publication, the owner should review the text and convert repository paths to stable links if desired. The “Original local draft” field preserves traceability.

### Draft #3 — Expand Frontend Automated Tests for Uncovered Workflows

```markdown
## Summary

Expand frontend automated coverage for selected project workflows that are not demonstrated by the existing tests. This is a gap-focused task: Vitest tests and one isolated browser E2E journey already exist.

## Current status

`frontend/src/App.test.tsx` covers sign-in rendering and native validation, safe login-failure feedback, and a mocked successful login that renders the protected Projects view. `frontend/e2e/authenticated-project.spec.ts` covers one isolated real-browser project create/reload/retrieval journey. The current evidence does not cover every product workflow; archive-aware interactions and broader loading/error states remain gaps. Do not duplicate the existing login tests or claim all FR-001–FR-009 flows are covered.

## Scope

Add focused Vitest cases for archive-aware project visibility/interaction and representative loading and API-error behavior for a selected project workflow. Use deterministic fixtures/mocks; do not require production credentials or an external service.

## Acceptance criteria

- Tests verify active versus archived project visibility and the applicable permitted UI action.
- Tests cover at least one loading state and one API failure state not already covered by existing assertions.
- Assertions check accessible, user-visible outcomes and use deterministic test data.
- `npm run test -- --run` passes with the new cases and remains non-interactive/CI-compatible.
- Evidence identifies the added tests and exact test command/result; the frontend CI job passes for the resulting commit/PR.
- Documentation continues to describe browser E2E as one workflow, not complete application coverage.

## Verification

Run `npm run test -- --run` from `frontend`, inspect the new assertions and summary, and verify the frontend quality job on the resulting PR/commit. Link actual test files, report, and CI run after they exist.

## References

- `product-spec.md` FR-001 — active and archived project behavior.
- `docs/testing-strategy.md` — current frontend and E2E coverage limitations.
- Existing tests: `frontend/src/App.test.tsx` and `frontend/e2e/authenticated-project.spec.ts`.

## Dependencies and approval

Use the existing Vitest setup and stable mocked API fixtures. Any dependency change requires separate approval. Publishing this Issue authorizes neither implementation nor other repository changes.

## Evidence and agent use

After this Issue is published, reference its real number/URL in subsequent agent tasks. Link the actual test diff, command output, report, and CI run. Do not imply prior work used this Issue or invent historical activity.

Original local draft: #3.
```

### Draft #5 — Implement Development CD and Manual Production Deployment

```markdown
## Summary

Design and implement a controlled deployment pipeline after provider, cost, security, and environment gates are explicitly approved. Current GitHub Actions performs CI quality validation; CD deployment is not implemented or verified.

## Current status

The repository has successful CI evidence, deployment preparation documentation/configuration, and no verified development or production deployment. A prepared descriptor is not a provisioned service. This task must not activate deployment or incur cost without separate Human Product Owner authorization.

## Scope

Provide an automatically gated deployment to an approved non-production development environment and a separate manually approved production release path. Include health verification, source/environment traceability, and a tested recovery/rollback procedure.

## Acceptance criteria

- Deployment is gated by successful CI for the exact source commit.
- Development and production environments and secrets are separated; secret values are not committed or emitted in logs.
- Development deployment occurs only after its target/provider and cost are approved.
- Production deployment requires an explicit manual human approval gate.
- Deployment records identify source SHA, target environment, outcome, and verification.
- Health checks and a non-destructive rollback/recovery process are documented and validated.
- Tests or workflow validation demonstrate that CI does not accidentally deploy production.
- No production deployment is claimed until a separately authorized run succeeds.

## Verification

Validate the workflow without deploying production. After provider approval, record an actual development deployment run and health check; inspect the production approval gate and exercise a safe recovery scenario in an approved non-production target.

## References

- `docs/Project.md` — CI/CD rubric.
- `.github/workflows/ci.yml` — current CI-only workflow.
- `docs/deployment-render.md` and `docs/deployment-render-free.md` — current deployment preparation and limitations.

## Dependencies and approval gates

Requires approved provider and pricing, target environments, artifact strategy, environment-specific secrets, migration policy, health/rollback plan, and explicit owner authorization. Issue publication is not approval to activate CI/CD, create cloud resources, spend money, or deploy.

## Evidence and agent use

After publication, reference the real Issue in future agent tasks and link actual workflow changes, validation, deployment run, recovery evidence, and owner approval. Do not invent runs or prior tracker activity.

Original local draft: #5.
```

### Draft #6 — Deploy AI BAP Publicly for Reviewer Access

```markdown
## Summary

Provide a reviewer-accessible public HTTPS demo only after deployment security, cost, provider eligibility, and owner-approval gates pass. No public AI BAP deployment or production operation is currently verified.

## Current status

Render paid and Free deployment descriptors and procedures have been prepared, but the owner previously confirmed no AI BAP Render Web Service, Static Site, or PostgreSQL resource had been created (owner-confirmed, not independently platform-verified). Public deployment remains NO-GO pending the blockers below. Prepared configuration is not deployment evidence.

## Scope

Subject to separate explicit approval, deploy the full application with an approved PostgreSQL strategy, external secrets, safe migrations, health checks, and a reviewer-safe core workflow. Keep PostgreSQL private and do not expose credentials or privileged bootstrap material.

## Acceptance criteria

- Provider eligibility, plan limits, persistence/retention, backup, expiration, and all potential charges are confirmed before provisioning.
- The frontend and API health endpoint are reachable over HTTPS at real public URLs.
- A reviewer-safe core workflow completes and persists data in the selected database.
- Database access remains private; migrations fail closed and do not run the fresh local database initializer against public data.
- JWT and database credentials are managed outside Git; no secrets appear in logs or frontend artifacts.
- CORS contains only the approved public frontend origin; same-origin/API routing is verified.
- Initial administrator creation uses an approved secure bootstrap procedure; temporary bootstrap secrets are removed after successful creation.
- Health, database persistence/retention limitations, and recovery/rollback are verified and documented.
- README receives public URL/demo instructions only after a successful authorized deployment.

## Verification

First complete provider/pricing and configuration review without provisioning. Only after a separate owner authorization, verify public HTTPS/API health, CORS, safe authentication, one reviewer-safe persisted workflow, migration result, and recovery limitations. Record actual URLs and sanitized evidence.

## References

- `docs/Project.md` — Deployment rubric.
- `render.yaml`, `render.free.yaml` — prepared descriptors; not evidence of created resources.
- `docs/deployment-render.md`, `docs/deployment-render-free.md` — deployment procedures and limitations.
- `docs/codex-reports/adm_8.10.132.md` — prior deployment-risk decision record.

## Dependencies and approval gates

Requires provider/region/eligibility and pricing approval, cost/billing consent, secure administrator bootstrap, external environment secrets, migration safety, HTTPS, exact CORS configuration, private database access, health/persistence checks, and recovery plan. Each provisioning/deployment operation requires separate explicit owner authorization. Publishing this Issue grants none of that authority.

## Evidence and agent use

After publication and authorized deployment work, link the real Issue, change/PR, actual deployment record, public URL, sanitized verification evidence, and limitations. Never claim deployment before it is verified.

Original local draft: #6.
```

### Draft #7 — Instrument Metrics, Structured Logs, and Distributed Tracing

```markdown
## Summary

Instrument one selected user journey with privacy-safe, correlated structured logs, metrics, and distributed traces, and make the signals viewable in an approved operator UI.

## Current status

Advanced correlated telemetry, collection/storage, and a dashboard/UI are not verified. Default Uvicorn logs, if present, do not satisfy this task's full acceptance criteria or the rubric's 2-point observability tier.

## Scope

Select a bounded journey (for example, login-to-project-list); define telemetry fields, trace propagation, user-impact metric, collection/storage, operator view, retention, and access controls.

## Acceptance criteria

- A controlled journey propagates a trace identifier across structured application logs and traces.
- At least one useful journey metric is emitted and correlated without customer content, credentials, or tokens.
- Logs, metrics, and traces are collected, stored, and visible in an operator UI.
- Data minimization, retention, access control, and telemetry failure behavior are documented.
- Redacted evidence demonstrates correlation for the selected journey.
- Tests or checks verify sensitive fields are not emitted.

## Verification

Run the selected non-production journey and demonstrate linked log/metric/trace records in the configured UI. Inspect emitted fields and retained evidence for sensitive data; report any unavailable signal explicitly.

## References

- `docs/Project.md` — Observability rubric.
- `docs/architecture.md` — current architecture and operational limitations.
- `docs/agent-team.md` and `docs/agent-workflow.md` — observability and incident handoffs.

## Dependencies and approval gates

Requires owner approval of telemetry provider/stack, cost, privacy/data-handling, target environment, retention, and access policy. Do not transmit customer data or secrets to telemetry.

## Evidence and agent use

After publication, reference the actual Issue in agent tasks and link real configuration, tests, sanitized UI evidence, and report. Do not claim historical Issue use.

Original local draft: #7.
```

### Draft #8 — Create a User-Impact Alert and Controlled Trigger

```markdown
## Summary

Define and demonstrate one alert tied to a measurable user-visible failure, with a bounded non-production trigger and verified notification/recovery behavior.

## Current status

No user-impact alert or controlled alert delivery is verified. Host CPU/resource thresholds alone do not meet this task's user-impact intent.

## Scope

Choose a user-impact signal (for example, login or project-read failure rate), define a privacy-safe alert, route it to an owner-approved destination, and test trigger, suppression, resolution, and recovery in non-production.

## Acceptance criteria

- Alert condition is based on a user-impact metric and a documented threshold/window.
- Alert includes non-sensitive service/environment, correlation, severity, and runbook context.
- A controlled non-production trigger is delivered to the approved destination.
- Suppression/rate-limiting, duplicate handling, and resolved-state behavior are documented and tested.
- Notifications contain no credentials, tokens, customer data, or sensitive logs.
- Trigger and recovery evidence is redacted and reproducible.

## Verification

Generate a bounded non-production test event, verify notification delivery and resolution, and confirm sensitive data is absent. Do not trigger against production without separate approval.

## References

- `docs/Project.md` — Alerting on User Impact rubric.
- `docs/agent-team.md` and `docs/agent-workflow.md` — incident response and approval boundaries.

## Dependencies and approval gates

Depends on a verified user-impact signal/telemetry from Draft #7, an owner-approved destination, externally managed delivery credentials, a runbook, and explicit approval for the test trigger. Issue publication does not authorize integration setup or triggering.

## Evidence and agent use

After publication, reference the real Issue and link the actual alert rule, runbook, trigger/recovery result, and report. Never claim an alert or delivery before verification.

Original local draft: #8.
```

### Draft #9 — Implement a Controlled On-Call Responder

```markdown
## Summary

Implement and demonstrate a narrowly scoped responder that receives a user-impact alert, diagnoses it with safe telemetry and a runbook, then performs only approved reversible remediation or escalates to a human.

## Current status

No alert-driven on-call responder or end-to-end remediation evidence is verified. Documented agent-team roles do not mean an operational responder is running.

## Scope

Build a bounded alert intake and response workflow with least-privilege diagnostics, auditable decisions, explicit human approval boundaries, reversible actions, and safe escalation.

## Acceptance criteria

- Responder receives the selected alert and correlates it with privacy-safe telemetry.
- It follows a versioned runbook and reports evidence for user impact and likely cause.
- Automated actions are pre-approved, least-privilege, reversible, and auditable; uncertain, privileged, destructive, or irreversible actions are escalated.
- A controlled non-production scenario demonstrates alert → diagnosis → action/escalation → validation and, where applicable, rollback.
- Secrets and customer data do not enter prompts, logs, or Issue comments.
- Human approval and escalation paths are exercised and recorded.

## Verification

Run a non-production incident simulation; inspect the sanitized audit trail, action boundary, outcome, validation, and rollback/escalation behavior.

## References

- `docs/Project.md` — On-Call Agent rubric.
- `docs/agent-team.md` — role and approval boundaries.
- `docs/agent-workflow.md` — incident handling and evidence process.

## Dependencies and approval gates

Depends on Drafts #7 (telemetry) and #8 (alert), an approved runbook/remediation policy, approved integration/credential management, non-production target, and explicit human authorization for any action. Publishing this Issue does not authorize production access or remediation.

## Evidence and agent use

After publication, reference the real Issue and link responder implementation, policy approval, controlled scenario report, and actual validation. Do not infer operational agent use from documentation alone.

Original local draft: #9.
```

### Draft #10 — Final Documentation and Submission Verification

```markdown
## Summary

Complete a final evidence-based submission audit while keeping repository rubric evidence separate from the course platform's mandatory peer-review records.

## Current status

The rubric evidence is still evolving. Three mandatory course peer reviews remain NOT VERIFIED. GitHub Issues, PR reviews, and repository checklists are not evidence that those course-platform reviews were completed.

## Scope

Review README, product specification, public tracker links, CI/CD, deployment/demo, telemetry/alert/responder claims, limitations, rubric mapping, and a reviewer verification path. Separately verify the three required peer reviews on the course platform.

## Acceptance criteria

- Documentation distinguishes implemented, verified, planned, blocked, and not-run items and links only to real evidence.
- Each claimed rubric point has reviewer-accessible evidence.
- Submission artifacts contain no secrets, credentials, or temporary sensitive diagnostics.
- Each of the three mandatory peer reviews is independently verified from course-platform evidence; record completion without exposing private details.
- GitHub Issue/PR activity is not substituted for course peer-review completion.
- Reviewer demo/verification instructions are concise and tested to the extent claimed.
- Human Product Owner records final acceptance and unresolved blockers.

## Verification

Perform a final repository/documentation evidence audit and separately inspect the course platform for three completed peer-review records. Record evidence source, date only when actually observed, and remaining blockers; do not fabricate timestamps or completion.

## References

- `docs/Project.md` — authoritative criteria and mandatory Peer Reviewing section.
- `README.md`, `product-spec.md`, `docs/project-rubric-gap-analysis.md`, and `docs/testing-strategy.md`.
- Relevant Codex reports and real Issue/PR/workflow/deployment links as available.

## Dependencies and approval gates

Depends on accurate published tracker links and available evidence for relevant implementation, CI/CD, deployment, and operations claims; requires course-platform access and Human Product Owner review. It does not itself complete the peer reviews.

## Evidence and agent use

After publication, reference the real Issue in subsequent audit tasks and link genuine repository/platform evidence. Course review completion must be evidenced only by the course platform. Do not backdate activity or treat Issue status as proof of peer review.

Original local draft: #10.
```

## 9. Publication order and dependencies

Recommended future order, after a separate publication authorization:

1. Publish #3 (focused frontend coverage) as an independent quality task.
2. Publish #5 (CD gates) and #6 (public demo) as distinct tasks. Keep #6 blocked until provider/pricing and security gates are accepted; do not provision during publication.
3. Publish #7 telemetry design/implementation.
4. Publish #8 after #7 defines a usable user-impact signal and approved destination.
5. Publish #9 after #7 and #8, and after remediation/approval policy exists.
6. Publish #10 as a final audit once evidence has accrued; separately verify course peer reviews.

Dependency chain: **Observability (#7) → Alerting (#8) → On-call responder (#9).** CD (#5) and public deployment (#6) are separate scopes with shared provider/security dependencies; neither is authorized by Issue publication.

## 10. Security and authorization gates

- Public deployment (#6) remains explicitly gated by provider and pricing approval; secure administrator bootstrap; environment/secret configuration; safe database migrations; HTTPS and exact CORS validation; health and persistence checks; and recovery/rollback planning.
- CD (#5) requires separate environments/secrets, exact-commit CI gates, production human approval, and safe rollback. No workflow activation is authorized here.
- Telemetry, alerts, and responder tasks require privacy-safe data, approved storage/destination, least privilege, and human approval boundaries.
- No Issue body includes credentials, secret values, customer data, or private account information.
- The three mandatory peer reviews are course-platform obligations, not GitHub Issues.

## 11. Prospective agent-use evidence plan

After a separate publication step:

1. Capture the real Issue number and URL only after GitHub confirms creation.
2. Reference that published Issue in subsequent agent task intake and handoffs.
3. Link genuine implementation and test evidence (paths, report, commit/PR, workflow run, or deployment record) as each becomes available.
4. Update status/checklists only after actual work and verification.
5. Keep secrets and sensitive data out of Issue content.
6. Never backdate activity or claim that an agent used an Issue before it existed.

## 12. Fail-closed publication checklist

Before each later Issue creation, stop unless all applicable checks pass:

- [ ] Confirm the repository identity is exactly `imend35/ai-bap`.
- [ ] Confirm the repository remains public.
- [ ] Confirm Issues remain enabled.
- [ ] Query current open and closed standalone Issues; exclude PRs and check title, scope, acceptance criteria, affected implementation area, and evidence for duplicates.
- [ ] If GitHub API access or inventory is incomplete, mark duplicate verification BLOCKED and do not publish.
- [ ] Confirm the selected draft is within the approved set (#3, #5, #6, #7, #8, #9, #10) and body matches the approved source/report.
- [ ] Confirm current implementation status and linked evidence are accurate.
- [ ] Check for credentials, tokens, database URLs, personal/customer data, and sensitive logs.
- [ ] Confirm dependencies and cost/provider/security/human-authorization gates are explicit.
- [ ] Ensure no historical agent activity, Issue ID, URL, comment, timestamp, test result, or deployment evidence is invented.
- [ ] Confirm the publication action itself has explicit authorization; do not infer implementation/deployment authority from it.

## 13. Blockers and uncertainties

- This plan does not authorize the later Issue creation action; separate explicit authorization is required.
- The GitHub inventory was successfully queried in this step and was empty for standalone Issues; it may change, so repeat the duplicate check immediately before publishing.
- Proposed bodies reference repository paths without fabricated path permalinks; validate stable links against the then-current default branch before posting.
- Public deployment remains NO-GO pending owner/provider/cost/security decisions and implementation evidence.
- Course platform evidence for the three mandatory peer reviews remains NOT VERIFIED.
- Publication of #5–#9 does not mean implementation has started or been approved.

## 14. Git and resource preservation

Only this untracked report was created. No existing file was modified. No Issues, repository settings, cloud resources, or Docker resources were changed. No stage, commit, push, pull, merge, rebase, or reset occurred. The index remained empty, and all pre-existing modified and untracked paths were preserved.

## 15. PASS / FAIL / BLOCKED matrix

| Check | Result | Evidence |
|---|---|---|
| Repository identity | PASS | Fresh API returned `imend35/ai-bap`, repository ID `1418730977`. |
| Public visibility | PASS | Fresh repository metadata returned visibility `public`. |
| Issues enabled | PASS | Fresh REST metadata returned `has_issues = true`. |
| Open standalone Issue inventory | PASS | Fresh API query returned no open items. |
| Closed standalone Issue inventory | PASS | Fresh API query returned no standalone items; one closed PR was identified by its `pull_request` marker and excluded. |
| Duplicate detection for seven candidates | PASS for current snapshot | No existing standalone Issue candidates were present. Repeat before publication. |
| Seven proposed bodies | PASS | Full Markdown candidates included in §8 with acceptance, verification, references, dependencies, gates, evidence expectations, and source draft number. |
| Historical agent activity claims | PASS | No historical Issue use, numbers, comments, or timestamps were invented. |
| Issue publication | NOT PERFORMED | This was plan-only. |
| Deployment/provisioning | NOT PERFORMED | Explicitly outside authorization. |
| Course peer reviews | BLOCKED / NOT VERIFIED | Requires separate course-platform evidence. |

## 16. Recommended single next action

**Request a separate explicit Human Product Owner authorization for a controlled publication operation of the seven reviewed bodies, with a fresh duplicate check immediately before each creation.**

## 17. GO / NO-GO conclusion

**GO** for Human Product Owner review of these seven prepared Issue bodies. **NO-GO** for publishing them in this plan-only step or treating publication as implementation/deployment authorization. Repository identity, visibility, Issues configuration, and current duplicate inventory were verified successfully; any later failed or incomplete gate must stop publication. Product Specification remains **1/2** until public task Issues and prospective agent-use evidence exist. The three course peer reviews remain separately **NOT VERIFIED**.
