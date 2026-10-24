# ADIM 8.10.116 — GitHub Merge Governance Audit

## Step name and objective

Perform a read-only merge-governance and security audit for PR #1 without
merging, changing GitHub settings, or modifying unrelated working-tree content.

## Verified facts

- Local branch: `docs/ci-pr-evidence`.
- Local and live remote feature-branch SHA:
  `3e384f432f61217c972f32c2134166c9705e94d9`.
- Live `main` SHA observed by `git ls-remote`:
  `1e4333738947f131816901b9fdb71e4fff61d4f2`.
- The Git index is empty. Existing modified/untracked Codex reports remain
  outside this audit.
- Independently verified evidence supplied for this step states that PR #1 is
  open, targets `main` from `docs/ci-pr-evidence`, and has the expected head.
- Supplied evidence also states that Backend quality and Frontend quality both
  concluded `SUCCESS`.
- Sourcery review was skipped because the PR exceeds its 150,000-character
  review limit. The available Sourcery bot review is `COMMENTED`, not a verified
  human approval.

## Governance and review assessment

| Area | Status | Evidence and interpretation |
| --- | --- | --- |
| PR state, base, head, and unmerged state | VERIFIED from independently supplied GitHub evidence | PR #1 is open from `docs/ci-pr-evidence` to `main`, at the expected head. |
| Backend quality | VERIFIED from independently supplied GitHub evidence | Successful; do not infer deployment readiness from CI. |
| Frontend quality | VERIFIED from independently supplied GitHub evidence | Successful; do not infer deployment readiness from CI. |
| Sourcery automated review | VERIFIED SKIPPED | The review-size limit leaves an automated-review coverage gap. A skip is not an approval and is not a failure of the code itself. |
| Human approval | NOT VERIFIED | Available review evidence identifies a bot `COMMENTED` review only. No human approval was verified. |
| Requested reviewers | NOT ACCESSIBLE | No authenticated GitHub review metadata was available in this environment. |
| Unresolved conversations | NOT ACCESSIBLE | REST review comments alone cannot reliably identify resolved conversation threads; no authenticated GraphQL/UI access was available. |
| Required checks / branch protection | UNKNOWN | The independently reported branch-protection API response was 403 `Resource not accessible by integration`. This is access denial, not proof that protection is absent. |
| Repository rulesets | UNKNOWN | Not available through the current access path. |
| Mergeability | NOT ACCESSIBLE | No usable live PR mergeability metadata was returned. Even a future `mergeable=true` result would indicate Git applicability, not security approval. |

## Read-only access attempts

- `git ls-remote` successfully confirmed the live feature and `main` branch
  references.
- The GitHub CLI is unavailable in this environment.
- A sanitized read-only GitHub REST inspection attempt did not produce usable PR,
  review, check, protection, or ruleset metadata. No credentials or payloads
  were exposed, and no GitHub state was changed.

## CI and security implications

The verified frontend/backend CI results provide useful automated validation for
the pushed code. They do not satisfy governance requirements by themselves.
The skipped Sourcery review increases the importance of the focused manual
security review recorded in ADIM 8.10.107 and a Human Product Owner/human
reviewer decision. It does not automatically require splitting the PR, but the
broad PR scope and unavailable policy data mean a merge should not proceed on
CI alone.

## Exact manual GitHub UI checks required

Before any separately authorized merge, a Human Product Owner should perform
and record these read-only checks in GitHub:

1. Open PR #1 and confirm **Open**, base `main`, head
   `docs/ci-pr-evidence`, and head SHA `3e384f4`.
2. In the **Checks** tab, confirm the workflow run for this exact head has both
   Frontend quality and Backend quality as successful, with no pending or
   failed required check.
3. In the **Files changed** and **Conversation** tabs, resolve or explicitly
   document every outstanding review thread; confirm no unresolved Sourcery or
   human concern remains.
4. In **Review changes**, verify the required human approval count and that an
   eligible reviewer has approved. A bot comment is not a human approval.
5. In repository **Settings → Branches** and **Settings → Rules → Rulesets**,
   inspect the policy applying to `main`: required status checks, required
   approvals, stale-approval dismissal, conversation resolution, signed-commit
   requirements, linear-history requirements, and administrator bypass policy.
6. Review the merge box for out-of-date checks, conflicts, blocked merge state,
   and any required deployment/environment gate. Treat its green mergeability
   indicator only as merge mechanics, not as security sign-off.

## Files inspected or modified

Inspected:

- `AGENTS.md`
- Local Git branch, index, status, remote URL, and live remote branch refs
- Available GitHub-access capability

Created:

- `docs/codex-reports/adm_8.10.116.md`

No other file was modified by this audit.

## Commands executed and actual results

| Command or check | Result |
| --- | --- |
| Branch, `HEAD`, index, and status inspection | PASS — feature branch and expected head; empty index. |
| `git ls-remote origin refs/heads/docs/ci-pr-evidence refs/heads/main` | PASS — live refs recorded above. |
| GitHub CLI availability | NOT AVAILABLE. |
| Sanitized read-only GitHub REST inspection | NOT ACCESSIBLE — no usable metadata returned. |

## Blockers and GO / NO-GO

**NO-GO for merge at this time.** The blocking governance evidence is not a
code failure: human approval, unresolved-conversation state, branch protection,
rulesets, required checks, and mergeability are unknown or inaccessible here.
The Sourcery skip is a review-coverage gap that requires documented manual
review, not a presumed pass.

**GO** only for a separately authorized human GitHub UI governance review using
the checklist above. Merge should occur only after the exact-head CI run,
applicable protection/ruleset policy, required human approvals, and conversation
resolution have all been positively verified.

## Recommended next step

Have the Human Product Owner complete and capture the six GitHub UI checks,
then request a final, separately authorized merge-readiness confirmation. Do
not merge, deploy, or change repository settings until then.
