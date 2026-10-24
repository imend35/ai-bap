# ADIM 8.10.173 — GitHub Issues Publication Readiness Review

## 1. Objective

Review the ten locally drafted GitHub Issues for publication readiness, current-state accuracy, acceptance criteria, dependencies, and evidence expectations. This is a preparation review only; no project document, draft, GitHub Issue, or repository setting was changed.

## 2. Git baseline

- Branch: `docs/ci-pr-evidence`
- HEAD: `2afe0d4d88188ad0a8de14c590ca95d0536b1241`
- Index: empty at inspection.
- Five tracked modifications were present: `docs/codex-reports/adm_8.10.76.md`, `docs/project-rubric-gap-analysis.md`, `docs/testing-strategy.md`, `frontend/package-lock.json`, and `frontend/package.json`.
- There were 56 untracked status entries before this report: 54 existing Codex reports, `frontend/e2e/authenticated-project.spec.ts`, and `frontend/playwright.config.ts`. The report itself is the only additional path created by this task.

All pre-existing modifications and untracked files were preserved.

## 3. Documents inspected

- `AGENTS.md`
- `docs/Project.md` (authoritative course rubric)
- `docs/github-issues-plan.md` (all ten drafts)
- `product-spec.md` (root-level product specification)
- `docs/project-rubric-gap-analysis.md`
- `docs/agent-team.md`
- `docs/agent-workflow.md`
- `docs/testing-strategy.md`
- `scripts/test-all.ps1`, `frontend/package.json`, `frontend/src/App.test.tsx`, and `.github/workflows/ci.yml` for current testing/CI status
- `compose.yaml`, plus execution evidence in `docs/codex-reports/adm_8.10.82.md` and `docs/codex-reports/adm_8.10.168.md`

The previous live GitHub check in ADIM 8.10.172 found a public repository, Issues enabled, and no standalone Issues. That is a dated verification snapshot, not a new live query in this review. PR #1 was identified separately as a pull request, not a task Issue.

## 4. Ten-draft inventory

| # | Draft | Current-state assessment | Publication readiness |
|---:|---|---|---|
| 1 | Containerize the Full AI BAP Application with Docker Compose | Stale: `compose.yaml` now defines the full stack, isolated Compose runtime evidence exists, and authenticated browser E2E evidence covers one create/read journey. It must not be framed as entirely unfinished. | **Do not publish as an open implementation task as written.** If useful, reframe as a completed-work evidence issue only after owner approval; do not claim agents used an issue before it existed. |
| 2 | Provide One-Command Isolated Test Verification | Stale: `scripts/test-all.ps1` runs frontend tests and guarded backend tests, and `docs/testing-strategy.md` records a passing unified run (4 frontend + 511 backend). It intentionally does not start Docker or run browser E2E. | **Do not publish as an open task as written.** A separately scoped future enhancement could add browser E2E orchestration, but that is not the draft's current acceptance scope. |
| 3 | Add Frontend Automated Tests for Critical Workflows | Partly stale: Vitest is implemented and CI runs it; current component coverage includes sign-in, browser validation, safe login failure, and mocked authenticated Projects display. The draft's archive-aware behavior and broader loading/error coverage are not demonstrated by those tests. | **Requires correction.** Narrow it to missing tests and explicitly exclude already covered cases. |
| 4 | Verified Pull-Request CI Quality Gates | Completed according to the recorded remote PR CI evidence: frontend/backend quality jobs, tests, build, lint, migration, and Ruff results are documented. The linked run is historical evidence and should remain labeled as such. | **Do not publish as an open task as written.** Could be retained as a completed evidence record after human review, not as outstanding implementation. |
| 5 | Implement Development CD and Manual Production Deployment | CD is not implemented. It is distinct from the existing CI workflow and from merely preparing deployment descriptors. | **Publishable as an outstanding task.** Retain clear separation between development auto-deploy and manually gated production deployment. |
| 6 | Deploy AI BAP Publicly for Reviewer Access | No public AI BAP deployment is verified. Deployment configuration and procedures exist, but no deployed URL or production operation is evidenced. | **Publishable as an outstanding task.** Keep provider eligibility, cost approval, admin bootstrap, migration, and public security gates explicit. |
| 7 | Instrument Metrics, Structured Logs, and Distributed Tracing | Advanced correlated telemetry and a viewable collection UI are not verified. Default server logs do not satisfy this draft's stated advanced scope. | **Publishable as an outstanding task.** No material status correction needed; avoid implying telemetry already exists. |
| 8 | Create a User-Impact Alert and Controlled Trigger | No user-impact alert or controlled delivery/trigger is verified. It depends on an agreed metric/telemetry source and alert destination. | **Publishable as an outstanding task**, after or alongside issue 7's telemetry design; do not claim a trigger exists. |
| 9 | Implement a Controlled On-Call Responder | No alert-consuming responder, controlled remediation, or incident demonstration is verified. | **Publishable as an outstanding task**, dependent on alerting, telemetry, runbook, and human authorization policy. |
| 10 | Final Documentation and Submission Verification | The final audit is still useful; three mandatory course peer reviews remain NOT VERIFIED. Its tracker-related acceptance needs to be evaluated against the actual published Issue set at execution time. | **Requires a small correction before publication** to make course-platform peer-review evidence separate from repository tracker evidence and to avoid treating an Issue checklist as proof of completion. |

## 5. Acceptance criteria review

All ten drafts have explicit acceptance criteria and a verification method. They also name a rubric category and include agent-assisted evidence guidance. Draft quality is generally actionable, but criteria that assert current state must be refreshed:

- Draft 1 still says Compose starts PostgreSQL only, which conflicts with current `compose.yaml` and verified runtime evidence. Its clean-environment persisted browser/API smoke criterion has since been met for one isolated authenticated project flow, not for every workflow.
- Draft 2's “future frontend tests” and missing unified orchestration premise are outdated. Current unified runner executes Vitest and guarded backend Pytest; browser E2E is intentionally separate.
- Draft 3's “no automated test suite” premise is outdated. Remaining scope should focus on archive-aware and other demonstrably uncovered behavior, after checking current tests.
- Draft 4 is an evidence-retention task for work already verified, not outstanding CI implementation.
- Drafts 5–9 describe capabilities that remain not implemented or not verified, with dependency sequencing noted below.
- Draft 10 is an outstanding final verification task, but peer-review completion must be evidenced on the course platform and cannot be inferred from GitHub activity.

## 6. Implementation-status accuracy

Current evidence distinguishes implemented work from unfinished tasks:

- **Implemented and verified locally:** full-stack Compose runtime; one real-Chrome authenticated project create/reload/retrieval journey; PostgreSQL persistence for that synthetic project; frontend Vitest suite; unified frontend/backend test runner.
- **Implemented and remotely verified:** pull-request CI quality gates (historical successful workflow evidence in the repository reports).
- **Not implemented/not verified:** continuous deployment, public deployment, advanced observability/telemetry UI, user-impact alerting, and on-call responder.
- **Partially covered:** frontend automated tests exist but do not constitute comprehensive coverage for archive-aware or all product workflows.
- **Separate mandatory requirement:** three course peer reviews remain **NOT VERIFIED**.

“Implemented” does not imply every acceptance criterion, production behavior, or public runtime has been verified.

## 7. Duplicate and overlap assessment

- Drafts 1 and 2 overlap with completed implementation/evidence. Publishing them as open work would misrepresent status. They are not duplicates of each other: one concerns full-stack runtime; the other concerns safe test orchestration.
- Drafts 3 and 4 are distinct: frontend test breadth versus CI execution. Both have existing implementation; #3 retains genuine coverage gaps, while #4 is principally completed evidence.
- Drafts 5 and 6 are related but not duplicates: #5 is deployment automation and release gates; #6 is a reachable public demo and its operational safeguards. They can be separate Issues with an explicit dependency/order.
- Drafts 7, 8, and 9 form a dependency chain (telemetry → user-impact alert → responder), not duplicate tasks.
- Draft 10 is cross-cutting and depends on accurate evidence from the other work plus course-platform peer-review completion.

## 8. Publication readiness by draft

- **Publish as outstanding after routine owner review:** #5, #6, #7, #8, #9.
- **Correct before publishing:** #3 (remove completed test-suite premise; scope only uncovered test gaps); #10 (separate course peer-review evidence from public repository Issue tracking and define evidence without assuming completion).
- **Do not publish as open implementation work as written:** #1, #2, #4. Their core implementation or verification criteria are already evidenced. If a completed-work Issue is desired for rubric evidence, it must be transparently created after the work, labeled/worded as retrospective, and must not imply the agent used it during the earlier work.

No draft is a published Issue, and no historical agent activity should be retroactively attributed to an Issue that did not exist.

## 9. Recommended publication order

1. After owner approval, first revise the draft set outside this read-only step: close/remove the stale open-task framing for #1, #2, and #4; correct #3 and #10; retain #5–#9 as future work.
2. Publish the genuine outstanding work with real Issues and acceptance criteria. For dependency clarity, publish #5 and #6 as separately scoped deployment tasks; begin #7 before #8, then #9; publish #10 as a final cross-cutting audit after evidence is available.
3. For public deployment, satisfy the independent security, cost, administrator-bootstrap, and migration gates before provisioning. An Issue being published is not deployment authorization.
4. Complete the three mandatory peer reviews separately on the course platform and preserve verifiable completion evidence.

Before each Issue is created, search open and closed Issues for duplicates as required in the draft plan. This review did not create or edit drafts or Issues.

## 10. Agent-use evidence plan

After an Issue exists, future agent-assisted work can provide verifiable evidence by:

1. Referencing the real Issue number/URL in task intake and handoffs.
2. Linking the Issue from relevant PRs/commits and recording implementation status there.
3. Posting or updating a concise, human-reviewed Issue comment with changed paths, exact verification commands/results, evidence report links, blockers, and remaining criteria.
4. Updating checklist/status only after the corresponding evidence exists; never invent timestamps, results, or agent activity.
5. Keeping secrets, personal data, and sensitive logs out of Issues.

This process can demonstrate tracker use prospectively; it cannot retroactively prove that an agent used an Issue before publication.

## 11. Remaining blockers

- Owner authorization is required before publishing any Issue.
- Drafts #1–#4 and #10 need status/scope decisions or edits before publication as open tasks.
- #3 requires a focused gap statement grounded in the existing frontend tests.
- #5–#9 need explicit dependency, provider/security approval, and evidence expectations maintained when published.
- The tracker currently has no standalone Issues per the ADIM 8.10.172 live snapshot; confirm again immediately before publication.
- Three mandatory course peer reviews remain NOT VERIFIED.

## 12. Git and resource preservation

No existing file or draft was modified. No GitHub Issue or repository setting was changed. No staging, commit, push, pull, merge, rebase, reset, Docker operation, or deployment occurred. The index remained empty. This report is the only file created by this step and is untracked.

## 13. PASS / FAIL / BLOCKED matrix

| Check | Result | Evidence / reason |
|---|---|---|
| Read authoritative Product Specification rubric | PASS | `docs/Project.md` defines public tracker + acceptance criteria + agent-use evidence for 2 points. |
| Review ten local drafts | PASS | All ten numbered draft sections reviewed. |
| Every draft includes acceptance criteria and verification method | PASS | Present in each draft; current-status accuracy differs. |
| Drafts accurately distinguish completed work from outstanding work | FAIL | #1, #2, #3, and #4 have stale premises/status; #10 needs evidence-boundary clarification. |
| Outstanding deployment/operations tasks are identifiable | PASS | #5–#9 remain relevant with dependency order. |
| Duplicate/overlap risks assessed | PASS | Related dependency chain distinguished from duplicate scope. |
| GitHub publication readiness without corrections | FAIL | Several drafts must not be published as open work unchanged. |
| Live tracker rechecked in this step | NOT RUN | Prior ADIM 8.10.172 query is used as dated context; verify again before publication. |
| Git/resource preservation | PASS | No remote or Docker mutation; pre-existing work preserved. |
| Three mandatory course peer reviews | BLOCKED / NOT VERIFIED | Requires separate course-platform evidence. |

## 14. Recommended single next action

**Request owner approval for a narrowly scoped correction of the local Issue plan: retire the completed-work framing in drafts #1, #2, and #4, rewrite #3 and #10 to reflect verified gaps, and preserve #5–#9 as outstanding tasks before any publication.**

## 15. GO / NO-GO conclusion

**NO-GO for publishing all ten drafts as written.** Five drafts (#5–#9) are suitable outstanding-task candidates after routine owner review; #3 and #10 need correction, and #1, #2, and #4 should not be presented as unfinished. **GO** for a separately authorized local draft-correction step. The Product Specification score remains unchanged at **1/2** until published task tracking and prospective agent-use evidence are verified. The mandatory peer reviews remain separately **NOT VERIFIED**.
