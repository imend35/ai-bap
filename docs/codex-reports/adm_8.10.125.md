# ADIM 8.10.125 — PR Review Governance Audit

## Step name and objective

Perform a read-only governance audit of Pull Request #1 review submissions,
Sourcery findings, unresolved-thread evidence, mergeability, and accessible
branch-governance settings after successful CI on the latest commit.

## Branch and pull request verification

- Local branch: `docs/ci-pr-evidence`.
- Local `HEAD`: `f66d4a33dc35ba0f1cea486c7eb6f0d838aeeb84`.
- Git index: empty.
- Pull Request: [#1](https://github.com/imend35/ai-bap/pull/1).
- PR state: open, unmerged, and not a draft.
- PR base/head: `main` ← `docs/ci-pr-evidence`.
- PR head SHA: `f66d4a33dc35ba0f1cea486c7eb6f0d838aeeb84`.
- GitHub API mergeability: `mergeable=true`, `mergeable_state=clean`.

Technical mergeability is a GitHub compatibility result only. It is not an
approval, a branch-protection determination, a security sign-off, or release
authorization.

## CI evidence

The current PR head has directly verified successful pull-request CI evidence:

- Workflow: `Continuous Integration`.
- Run: <https://github.com/imend35/ai-bap/actions/runs/39927087481>.
- Event: `pull_request`.
- Status/conclusion: `completed` / `success`.
- Backend quality: success, including ephemeral-test-database migration,
  backend test, and backend lint steps.
- Frontend quality: success, including frontend test, production-build, and
  frontend-lint steps.

See `docs/codex-reports/adm_8.10.124.md` for the run-level evidence and its
test-count limitation.

## Review submission states and approvers

The public GitHub REST reviews endpoint returned one submitted review:

| Review ID | Reviewer | State | Commit |
| --- | --- | --- | --- |
| `5618370708` | `sourcery-ai[bot]` | `COMMENTED` | `7b1302e7a67a25ac42fc722a84d072bf29951cbb` |

The endpoint returned **zero `APPROVED` reviews**. A `COMMENTED` bot review is
not a GitHub approval and must not be treated as independent human approval.

## Review-thread identifiers and state limits

The REST API exposes these review-comment identifiers associated with the
Sourcery review:

| REST review-comment ID | File | Line context | Snapshot classification |
| --- | --- | --- | --- |
| `4351542516` | `docs/codex-reports/adm_8.10.72.md` | current line 88 | Reported by the supplied snapshot as unresolved; see evidence review below. |
| `4351542524` | `docs/project-rubric-gap-analysis.md` | original line 35 | Supplied snapshot: resolved. |
| `4351542536` | `docs/project-rubric-gap-analysis.md` | original line 35 | Supplied snapshot: resolved. |

These REST comment IDs are not GitHub GraphQL review-thread node IDs. The
GitHub GraphQL query needed to retrieve exact thread IDs and `isResolved`
states returned HTTP `403`. Therefore the current live resolution state and
exact GraphQL thread identifiers are **NOT_VERIFIABLE** through the available
read-only access. The two rubric-analysis resolutions are recorded from the
provided review-thread snapshot; no live-resolution inference is made.

## Evidence for the remaining historical-report finding

The remaining comment points to `adm_8.10.72.md:88`, which says that
`git diff --check` and `git status --short` were pending *after* the report and
the rubric update were written. In the same committed report:

- `adm_8.10.72.md:98-104` records the subsequent final local validation as
  passed and confirms the report existed.
- `adm_8.10.72.md:91-96` recommends the then-future pull-request CI run.
- `docs/codex-reports/adm_8.10.76.md` documents the later successful
  pull-request CI evidence.
- `docs/codex-reports/adm_8.10.118.md` revalidated the Sourcery finding as
  resolved: the earlier pending language is a chronological execution-state
  record, not a current conflicting status.

This is a documentation-history matter, not a security or runtime defect. The
smallest safe action is no corrective commit: request that a Human Product
Owner review this evidence and, if accepted, manually resolve the existing
Sourcery conversation in GitHub. This audit did not resolve it.

## Branch protection and ruleset verification limits

| Governance setting | Result | Classification |
| --- | --- | --- |
| `main` branch-protection endpoint | HTTP `401` | NOT_VERIFIABLE — access is required; absence cannot be inferred. |
| Repository rulesets endpoint | HTTP `200`; zero repository-level rulesets returned | VERIFIED only for repository-level rulesets exposed by this endpoint. This does not prove there are no organization-level rulesets or other inaccessible protection controls. |
| Required checks/approvals | Not derivable from the available access | NOT_VERIFIABLE. |

Manual GitHub UI checks required before merge consideration:

1. In PR #1, confirm required checks, reviewer requirements, unresolved
   conversations, and merge-box restrictions.
2. In repository Settings, inspect branch protection and rulesets for `main`.
3. If applicable, inspect organization-level rulesets and required-review
   policies.
4. Obtain and record explicit Human Product Owner/human reviewer approval.

## Files inspected or modified

Inspected:

- `AGENTS.md`
- Local branch, `HEAD`, index, remote URL, and full working-tree status
- Committed `docs/codex-reports/adm_8.10.72.md` around the cited finding
- Worktree `docs/codex-reports/adm_8.10.118.md`
- Public GitHub PR, review, review-comment, mergeability, branch-protection,
  ruleset, and GraphQL capability metadata

Created:

- `docs/codex-reports/adm_8.10.125.md`

No PR review, comment, thread, approval, branch setting, Git index, commit,
push, merge, deployment, or source file was changed.

## Security and release implications

The reviewed remaining finding does not expose secrets or change application
security. However, successful CI plus a clean mergeability state is
insufficient for a release decision because no GitHub `APPROVED` review was
available and required-review/protection policy could not be fully inspected.
The Sourcery review-size limitation and its non-approval state leave human
review coverage as a release-governance requirement.

## Working-tree preservation

The empty index was preserved. The pre-existing modified
`docs/codex-reports/adm_8.10.76.md` and all pre-existing untracked reports
remain untouched. This report is itself untracked.

## Blockers and recommended single next action

Blockers for merge authorization are the absence of recorded human approval,
the NOT_VERIFIABLE protection/required-review policy, and the NOT_VERIFIABLE
live thread-resolution state. The remaining historical-report thread has
evidence of being addressed and does not require a corrective commit.

**Recommended next action:** a Human Product Owner performs the required GitHub
UI governance review, explicitly reviews the historical-thread evidence, and
records an approval or remediation decision.

## GO / NO-GO

**GO** for initiating that human review and, if the Human Product Owner accepts
the evidence, resolving the remaining historical Sourcery conversation manually.

**NO-GO** for merge or release authorization until human approval and the
applicable GitHub protection/ruleset requirements are verified in the UI.
