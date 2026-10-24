# ADIM 8.10.105 — GitHub Pull Request & CI Verification

## Step name and objective

Verify the GitHub pull-request association and Continuous Integration (CI)
outcome for the pushed `docs/ci-pr-evidence` branch at commit
`47b7f20a1476375c057eef71d47a2c1a53d04a2b`, without changing GitHub or Git
state.

## Summary of completed work

- Confirmed locally that the current branch is `docs/ci-pr-evidence` and that
  `HEAD` is the expected commit.
- Confirmed the local remote-tracking ref `origin/docs/ci-pr-evidence` also
  points to that commit. The configured origin URL is the intended GitHub
  repository; no credential-bearing URL was recorded.
- Reviewed the CI workflow configuration: it defines a `Continuous
  Integration` workflow for pushes to `main` and pull requests targeting
  `main`, with separate frontend and backend jobs.
- Recorded previously available repository evidence that an earlier PR CI run
  for the feature branch completed successfully. That evidence does not prove
  a workflow run for the latest commit.
- Live GitHub, PR, workflow, and branch-protection verification were blocked:
  the local Git HTTPS metadata query could not connect to GitHub and the
  read-only browser returned cache-miss errors for GitHub pages.

## Files inspected or modified

Inspected:

- `AGENTS.md`
- `.github/workflows/ci.yml`
- `docs/codex-reports/adm_8.10.90.md`
- Local Git references, branch metadata, status, and diffs

Created:

- `docs/codex-reports/adm_8.10.105.md`

No existing file was modified by this step.

## Commands executed and actual results

| Command or check | Result |
| --- | --- |
| `git branch --show-current` and `git rev-parse HEAD` | PASS — branch and local `HEAD` match the expected branch and commit. |
| `git branch -vv`, `git show-ref`, and local history inspection | PASS — local remote-tracking ref is at the expected commit; `origin/main` is recorded at `1e4333738947f131816901b9fdb71e4fff61d4f2`. |
| `git ls-remote origin refs/heads/docs/ci-pr-evidence refs/heads/main` | BLOCKED — HTTPS connection to GitHub failed in this environment. No Git state changed. |
| Read-only GitHub PR, Actions, and commit page requests | BLOCKED — the browser reported cache misses. |
| `git diff --check` | PASS for repository content; Git emitted only a pre-existing LF-to-CRLF conversion warning for `docs/codex-reports/adm_8.10.76.md`. |

## PR and CI findings

| Item | Status |
| --- | --- |
| Live remote feature-branch SHA | NOT LIVE-VERIFIED in this environment; local tracking ref equals the expected SHA. |
| Open PR from `docs/ci-pr-evidence` to `main` | NOT LIVE-VERIFIED. Historical project evidence identifies PR #1, but its present open/review state was not independently confirmed. |
| PR number, URL, head SHA, base branch, review status | NOT LIVE-VERIFIED. |
| CI run for `47b7f20a1476375c057eef71d47a2c1a53d04a2b` | NOT LIVE-VERIFIED. Push success must not be treated as CI success. |
| Frontend and backend job conclusions for the latest commit | NOT LIVE-VERIFIED. |
| Workflow configuration | VERIFIED LOCALLY — frontend quality and backend quality jobs are configured; backend runs guarded Alembic migration, the full pytest command, and Ruff. |
| Required checks and branch protection | NOT AVAILABLE through local Git and not verified from GitHub. |

The prior ADIM 8.10.90 report contains evidence of successful PR CI for an
earlier feature-branch commit (run `39841863406`). It must not be substituted
for a run associated with the current commit.

## Validation and test results

No application tests, migrations, Docker actions, deployments, or GitHub
mutations were run. Git metadata and workflow configuration were inspected
read-only.

## Security checks

- No secrets, credentials, tokens, database URLs, or workflow variable values
  were displayed or added to the report.
- No Git staging, commit, push, merge, rebase, deployment, provisioning, or
  repository-settings change occurred.
- Existing working-tree changes were preserved.

## Issues and remaining tasks

The availability of GitHub is the remaining verification blocker. A human
operator or a future environment with authenticated/read-only GitHub access
must confirm the live feature-branch SHA, PR #1 association and review state,
the latest `pull_request` workflow run, both job conclusions, and any required
branch checks before merge consideration.

## Recommended next step

GO for a read-only GitHub verification when connectivity is available. Do not
merge or deploy until the workflow run explicitly associated with
`47b7f20a1476375c057eef71d47a2c1a53d04a2b` is confirmed successful and any
required review/check policy is satisfied.
