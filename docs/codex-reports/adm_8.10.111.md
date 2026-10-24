ADIM 8.10.112 — Controlled Security Hardening Local Commit

Role:
Act as a senior Git release engineer and application security reviewer for AI BAP.

Authorization:
The project owner explicitly approved creating ONE local commit containing ONLY the six files listed below.
This authorization does NOT include pushing, merging, deploying, provisioning, rebasing, or modifying unrelated files.

Expected branch:
docs/ci-pr-evidence

Expected starting HEAD:
47b7f20a1476375c057eef71d47a2c1a53d04a2b

Exact authorized staging manifest:
1. backend/app/initial_admin_bootstrap.py
2. backend/tests/test_bootstrap_admin.py
3. backend/tests/test_initial_admin_bootstrap.py
4. docker/backend/bootstrap_initial_admin_from_environment.py
5. docs/codex-reports/adm_8.10.108.md
6. docs/codex-reports/adm_8.10.110.md

Required commit message:
fix: harden initial administrator bootstrap failures

Execution:
1. Verify the current branch and starting HEAD match the expected values.
2. Verify the Git index is empty. Stop if it is not.
3. Confirm the exact six authorized paths exist and review their changes.
4. Verify the intended implementation/test changes and evidence reports contain no real secrets.
5. Run git diff --check and relevant safe static checks.
6. Stage ONLY the six authorized files using explicit pathspecs.
7. Verify the staged file list matches the authorized manifest EXACTLY.
8. Review the staged diff and check for whitespace errors or accidental sensitive content.
9. If any verification fails, stop without committing and report the blocker.
10. If all checks pass, create exactly ONE local commit using the required message.
11. Verify the new commit hash, parent, message, and exact committed file list.
12. Confirm all unrelated working-tree changes remain untouched.
13. Do NOT push, merge, deploy, provision, rebase, or change GitHub settings.

Mandatory Codex Report

Create:
docs/codex-reports/adm_8.10.112.md

Include verified facts, changes, exact committed files, commit hash, checks, preserved unrelated changes, blockers, recommended next action, and GO / NO-GO.

Do not stage the newly created ADIM 8.10.112 report.