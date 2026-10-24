# ADIM 8.10.129 — Controlled Pull Request Merge Preparation

## 1. Objective and owner authorization scope

Prepare an auditable, fail-closed procedure for a future merge of Pull Request
#1. The Human Product Owner authorized preparation only. This step did not
approve, resolve, merge, commit, push, rebase, deploy, provision, or change
GitHub settings.

## 2. Local and remote repository state

- Local branch: `docs/ci-pr-evidence`.
- Local `HEAD`: `f66d4a33dc35ba0f1cea486c7eb6f0d838aeeb84`.
- Git index: empty.
- Live feature-branch SHA:
  `f66d4a33dc35ba0f1cea486c7eb6f0d838aeeb84`.
- Live `main` SHA:
  `1e4333738947f131816901b9fdb71e4fff61d4f2`.

The local working tree contains pre-existing report changes and untracked
reports. They were not staged or altered.

## 3. PR and commit verification

Public GitHub API evidence for [PR #1](https://github.com/imend35/ai-bap/pull/1):

- State: open, unmerged, not draft.
- Base/head: `main` ← `docs/ci-pr-evidence`.
- Base SHA: `1e4333738947f131816901b9fdb71e4fff61d4f2`.
- Head SHA: `f66d4a33dc35ba0f1cea486c7eb6f0d838aeeb84`.
- Technical mergeability: `true`; state: `clean`.
- Commit count: 7.
- Changed files: 51 (36 added, 15 modified, 0 deleted).
- Aggregate diff: 4,446 additions and 176 deletions.

The seven commits are the documented CI evidence, documentation alignment,
Render deployment preparation, Render Free bootstrap, bootstrap hardening, and
Compose-runtime evidence changes. No unexpected deleted path was found.

## 4. CI and skipped-check analysis

The exact PR head has successful CI evidence:

- Workflow: `Continuous Integration`.
- Run: <https://github.com/imend35/ai-bap/actions/runs/39927087481>.
- Event: `pull_request`.
- Status/conclusion: `completed` / `success`.
- `Backend quality`: completed / success.
- `Frontend quality`: completed / success.

The Checks API reports three checks:

| Check | Conclusion | Assessment |
| --- | --- | --- |
| Frontend quality | success | Verified required-quality evidence for the source head. |
| Backend quality | success | Verified required-quality evidence for the source head. |
| Sourcery review | skipped | Review automation did not execute because the PR exceeds Sourcery's 150,000-diff-character review limit. |

The Sourcery check output explicitly identifies the size limit. This is an
expected conditional skip, not a test failure, but it is release-relevant: it
removes automated review coverage for a broad 51-file PR. It must be offset by
an explicit human review of the complete diff; it must not be silently treated
as a successful security review.

The legacy commit-status endpoint returned `pending` with zero legacy status
entries while the Checks API reports the two successful Actions checks above.
The cause and any required-status interpretation are **NOT_VERIFIABLE** with
the available governance access. The future merge procedure must check the
GitHub UI merge box and required-check policy immediately before merging.

## 5. Changed-file and security risk assessment

The PR scope is materially broader than a documentation update. It includes:

- Render Blueprint/environment documentation and deployment descriptors.
- Backend configuration and initial-administrator bootstrap implementation.
- Bootstrap, deployment-configuration, and isolated integration tests.
- Docker startup/migration wrapper scripts.
- Frontend API-base configuration adjustment.
- Product, architecture, test, deployment, rubric, and evidence reports.

No file deletion was reported. The source scope is consistent with the seven
commits and prior documented ADIM work, but the 51-file size, security-sensitive
bootstrap path, and skipped Sourcery coverage are merge risks requiring manual
owner review. Earlier focused security review evidence does not substitute for
the owner’s review of the final aggregate diff.

## 6. Merge strategy recommendation

**Recommended method: GitHub UI “Create a merge commit.”**

Rationale:

- It preserves the seven reviewed, purpose-specific commits and their audit
  chronology instead of collapsing release evidence into one squash commit.
- It records an explicit integration point from `docs/ci-pr-evidence` to
  `main` without rewriting either branch.
- It avoids rebase-based SHA changes, preserving links from CI and evidence
  reports to the reviewed source commits.

Expected history implication: `main` receives the seven existing commits plus a
new merge commit whose SHA is unknown until GitHub creates it. Do not use
squash or rebase unless separately authorized after a new review of their
history implications.

## 7. GitHub Actions and deployment side-effect analysis

The repository contains one workflow, `.github/workflows/ci.yml`. It runs on:

- `pull_request` targeting `main`.
- `push` to `main`.

Therefore a merge will trigger a new CI run on `main`, using its ephemeral CI
database migration/test path and frontend/backend quality jobs. The workflow
contains no deployment job and no deployment credentials.

No GitHub Actions deployment workflow was found. Render descriptors exist in
the PR, including a production migration command, but external Render service
state and any platform-side repository auto-deploy setting are
**NOT_VERIFIABLE** from this audit. A merge is not authorization to provision
or deploy, and no public deployment is evidenced.

## 8. Pre-merge verification checklist

Immediately before any future merge, the authorized operator must verify in the
GitHub UI and read-only Git/API views:

1. PR #1 remains open, unmerged, and targets `main` from
   `docs/ci-pr-evidence`.
2. Source head remains exactly
   `f66d4a33dc35ba0f1cea486c7eb6f0d838aeeb84`.
3. Target `main` remains
   `1e4333738947f131816901b9fdb71e4fff61d4f2`. If it changed, stop and repeat
   source-vs-target scope/CI review.
4. The two GitHub Actions quality checks are successful for the exact source
   head, and no new failed or pending required check exists.
5. Sourcery remains a known size-limit skip and has been compensated by an
   explicit owner diff review; it must not have changed to a failure.
6. The GitHub UI confirms no unresolved review conversations and no new
   blocking review or comment.
7. The UI confirms the currently applicable branch-protection/ruleset and
   required-approval requirements are satisfied.
8. The PR file/commit list remains the reviewed 7-commit, 51-file scope with
   no unexpected additions, deletions, or source-head change.
9. The operator has explicit Human Product Owner authorization for this exact
   merge after all gates are observed.

Any false, changed, failed, pending, or **NOT_VERIFIABLE** critical gate stops
the merge. Do not attempt a workaround, override, force push, or policy change.

## 9. Future merge execution procedure

After all checklist gates pass and a separate merge authorization is received:

1. Refresh PR #1 in GitHub and repeat the checklist above.
2. Select **Create a merge commit** in the GitHub UI.
3. Confirm the source and target branches once more in the confirmation dialog.
4. Create the merge once. Do not select squash, rebase, auto-merge, or branch
  deletion.
5. Record the resulting merge commit SHA and timestamp from GitHub.

## 10. Post-merge verification and rollback contingency

After a future merge:

1. Verify PR #1 reports merged and `main` references the new merge commit.
2. Verify the `push`-to-`main` CI run starts, then record its exact conclusion;
   do not substitute PR CI for this post-merge run.
3. Confirm no GitHub Actions deployment workflow or external deployment was
   triggered without separate authorization.
4. If a merge-related defect is found, stop release activity. Use a separately
   authorized revert through a new PR or GitHub’s Revert action; do not reset,
   force-push, or rewrite `main`. For a merge commit, a local equivalent would
   require a reviewed `git revert -m 1 <merge-commit>`, not an immediate action.

## 11. Working-tree preservation

No local file was changed except this untracked report. The Git index remained
empty. The pre-existing modified `docs/codex-reports/adm_8.10.76.md` and all
pre-existing untracked Codex reports remain preserved and excluded from this
preparation work.

## 12. Blockers and NOT_VERIFIABLE findings

- Branch-protection API access previously returned HTTP `401`; required-review
  and required-check policy is **NOT_VERIFIABLE** until inspected in the GitHub
  UI.
- GitHub GraphQL thread-resolution access returned HTTP `403`; the supplied
  all-threads-resolved context requires UI confirmation at merge time.
- External Render connection/auto-deploy state is **NOT_VERIFIABLE**; no
  GitHub deployment job exists, but external platform behavior must not be
  assumed.
- No independent human `APPROVED` review is recorded. Whether one is required
  is **NOT_VERIFIABLE** until branch policy is checked in the UI.

## 13. Recommended single next action

The Human Product Owner should perform the pre-merge checklist in the GitHub
UI—especially branch/ruleset policy, required checks, and conversation state—
then provide explicit, separate authorization only if every gate passes.

## 14. GO / NO-GO for controlled merge execution

**NO-GO now**: this step prepared the procedure only, and critical governance
settings and live conversation state are not independently accessible here.

**Conditional GO later**: a controlled one-time GitHub UI merge commit is
appropriate only after the owner’s final UI verification and explicit merge
authorization. Merge remains distinct from deployment.
