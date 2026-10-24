# ADIM 8.10.174 — GitHub Issues Plan Local Draft Correction

## 1. Objective

Correct the local task plan to distinguish completed evidence from outstanding work and prepare future Issues for accurate, approved publication. No remote GitHub resource or setting was changed.

## 2. Git baseline

- Branch: `docs/ci-pr-evidence`
- HEAD: `2afe0d4d88188ad0a8de14c590ca95d0536b1241`
- Git index: empty before and after the work.
- Pre-existing tracked modifications: `docs/codex-reports/adm_8.10.76.md`, `docs/project-rubric-gap-analysis.md`, `docs/testing-strategy.md`, `frontend/package-lock.json`, and `frontend/package.json`.
- Pre-existing untracked entries: 56 (54 Codex report files, `frontend/e2e/authenticated-project.spec.ts`, and `frontend/playwright.config.ts`). All were preserved.

After this task, status additionally shows the authorized modification to `docs/github-issues-plan.md` and this new untracked report. No other path was changed by this step.

## 3. Documents inspected

Read `AGENTS.md`, `docs/Project.md`, `docs/github-issues-plan.md`, `docs/codex-reports/adm_8.10.172.md`, `docs/codex-reports/adm_8.10.173.md`, `docs/project-rubric-gap-analysis.md`, `docs/testing-strategy.md`, root `product-spec.md`, `docs/agent-team.md`, and `docs/agent-workflow.md`. Also reviewed the current frontend tests and package scripts, unified runner, CI workflow, Compose definition, and the prior Compose/E2E execution reports for status accuracy.

## 4. Completed-work draft corrections

- **Draft #1:** Replaced the stale claim that Compose only starts PostgreSQL. It is marked completed with references to isolated full-stack runtime evidence and ADIM 8.10.168's one authenticated browser project journey. The report explicitly limits the claim to that tested journey and local disposable runtime.
- **Draft #2:** Marked the documented frontend-plus-backend unified runner complete, referencing `scripts/test-all.ps1` and the recorded 4 frontend + 511 backend result. It explicitly says browser E2E remains separate and the runner does not start Docker or migrate databases.
- **Draft #4:** Marked PR CI gates completed and remotely verified, referencing the workflow and existing reports. It distinguishes CI from CD/public deployment.

The plan retains the original identifiers and cautions that any later retrospective Issue must disclose it was created after the work. No historical Issue usage is claimed.

## 5. Frontend testing draft correction

Draft #3 now acknowledges the existing Vitest tests (sign-in rendering/validation, safe login failure, and mocked successful login/protected Projects view) and the single isolated real-browser project workflow. It narrows outstanding acceptance criteria to archive-aware project interactions plus representative uncovered loading and API-error states, with deterministic fixtures, accessible outcomes, existing Vitest command, and CI verification. It does not claim all product workflows are covered.

## 6. Outstanding deployment/operations drafts

Drafts **#5–#9** remain outstanding and retain measurable acceptance and verification criteria:

- #5: development CD and manually approved production deployment, with exact-commit CI gate, separated environments/secrets, health verification, and recovery.
- #6: public HTTPS reviewer demo, gated on provider/cost, secure bootstrap, migration, CORS, persistence, secrets, and recovery verification.
- #7: correlated structured logs, metrics, traces, collection/UI, privacy, retention, and access evidence.
- #8: user-impact alert and bounded non-production delivery/recovery trigger, dependent on telemetry and an approved destination.
- #9: alert-driven responder with safe telemetry, runbook, reversible approved action or escalation, and a controlled demonstration, dependent on #7/#8.

The plan explicitly states that Issue publication is not permission to provision, spend, deploy, or perform other external changes. Render deployment remains NO-GO until independent safety and owner-approval gates pass.

## 7. Final submission draft correction

Draft #10 now separates repository tracker evidence from course-platform evidence. It requires three mandatory peer reviews to be independently verified on the course platform; GitHub PR reviews, Issues, or a repository checklist do not prove course completion. It retains final documentation, reviewer demo, evidence accuracy, and Human Product Owner sign-off as blockers/acceptance requirements. Peer reviews remain **NOT VERIFIED**.

## 8. Publication-readiness summary

The plan now states:

- **Completed-work evidence:** #1, #2, #4 — do not publish as open implementation tasks. A retrospective Issue requires explicit approval and must not imply earlier tracker use.
- **Corrected outstanding drafts:** #3, #10.
- **Outstanding publication candidates:** #5–#9.

The Product Specification score was not changed and remains **1/2** until published public task tracking, acceptance criteria, and prospective verifiable agent-use evidence exist.

## 9. Prospective agent-use evidence process

The revised plan specifies: obtain owner approval and publish an Issue; record only its real number and URL after creation; reference that Issue in subsequent agent tasks and handoffs; link genuine implementation/test/report/commit/PR/run/deployment evidence when it exists; update Issue status after actual work; and exclude secrets and sensitive data. It explicitly disallows fabricating or backdating agent activity.

## 10. Acceptance criteria and dependency checks

All ten original draft identifiers remain. Each section includes a status/disposition, acceptance or evidence criteria, rubric category, and verification/evidence guidance. Outstanding drafts #3 and #5–#10 have specification/documentation references and dependencies or approval gates as applicable. Drafts #1, #2, and #4 retain completion evidence instead of open-work acceptance claims. The #7 → #8 → #9 operational dependency is explicit; #5/#6 retain distinct CD versus public-deployment scopes.

## 11. Documentation consistency checks

- Product Specification rubric in `docs/Project.md` remains unchanged; its 2-point tier requires a public tracker, acceptance criteria, and evidence agents used it.
- `product-spec.md` and `docs/testing-strategy.md` support the description of existing frontend tests and one verified isolated browser flow.
- `docs/codex-reports/adm_8.10.82.md` and `adm_8.10.168.md` support local Compose/E2E evidence only, not public production deployment.
- `docs/agent-team.md` and `docs/agent-workflow.md` support prospective task intake/handoff and evidence practices, not historical use of unpublished Issues.
- ADIM 8.10.172 is cited as a prior live tracker snapshot; the plan requires a fresh duplicate check before any later publication.
- `git diff --check` passed with no whitespace errors. Git emitted line-ending conversion warnings for modified files; no line-ending conversion was intentionally performed. A direct trailing-whitespace scan of the changed plan and this report passed.
- Structural Markdown checks confirmed ten numbered draft sections and acceptance/evidence sections for each; no Markdown linter was installed or run.

## 12. Exact file changes

- Modified: `docs/github-issues-plan.md`
- Created: `docs/codex-reports/adm_8.10.174.md`

No other file was changed by this step. No score, source code, test, dependency, Docker, Compose, CI, or deployment configuration was modified.

## 13. Git and resource preservation

No Issue was created, edited, closed, labeled, assigned, or commented on. Repository settings were not changed. No Docker, deployment, or provisioning operation occurred. No staging, commit, push, pull, merge, rebase, or reset occurred. Existing working-tree changes were preserved and the index remains empty. The new report is untracked.

## 14. PASS / FAIL / BLOCKED matrix

| Check | Result | Evidence |
|---|---|---|
| Original ten draft identifiers retained | PASS | Plan contains Draft #1 through Draft #10 without renumbering. |
| Completed work #1/#2/#4 no longer represented as open implementation work | PASS | Status and evidence sections mark them complete and caution against open-task publication. |
| Draft #3 reflects existing tests and remaining gaps | PASS | Existing Vitest/E2E coverage acknowledged; archive/loading/error gaps scoped. |
| Drafts #5–#9 remain measurable outstanding work | PASS | Acceptance criteria, verification, dependencies, and authorization gates retained or clarified. |
| Draft #10 separates tracker from course peer reviews | PASS | Course-platform verification is explicit; GitHub activity is not accepted as proof. |
| Score and peer-review state remain accurate | PASS | Score remains 1/2; three reviews remain NOT VERIFIED. |
| Markdown/diff validation | PASS with warnings | No whitespace errors; only Git line-ending warnings for modified files. |
| Only authorized existing document modified | PASS | Tracked diff path is `docs/github-issues-plan.md`; report is the sole new file. |
| GitHub publication | NOT PERFORMED | No remote Issues or settings were changed. |

## 15. Recommended single next action

**Request Human Product Owner review and approval of the corrected local publication plan before publishing any Issues.**

## 16. GO / NO-GO conclusion

**GO** for review of the corrected local plan. **NO-GO** for publishing Issues until owner approval and a fresh duplicate check. The completed work is not misrepresented as outstanding, the rubric score is unchanged at **1/2**, Render deployment remains gated, and the three mandatory peer reviews remain **NOT VERIFIED**.
