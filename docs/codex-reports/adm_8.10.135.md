# ADIM 8.10.135 — Guarded Migration Security Test Execution

## Objective

Execute the focused migration-security tests from ADIM 8.10.134 only when the existing isolated PostgreSQL environment and all fail-closed test prerequisites are positively verified. This was a test-only step; no source code, database resource, container lifecycle, or Git state was changed.

## Repository state

- Branch: `docs/ci-pr-evidence`.
- `HEAD`: `f66d4a33dc35ba0f1cea486c7eb6f0d838aeeb84`.
- Git index: empty.
- Pre-existing changes from ADIM 8.10.134 remain present: the migration script, focused tests, and prior reports are still unstaged.
- Existing modified and untracked Codex reports were preserved.

## Test-environment safety verification

The repository guard in `backend/tests/conftest.py` invokes `configure_test_database_environment()` before test modules import. `backend/app/test_database_safety.py` requires all of the following conditions:

- test mode enabled;
- an explicit isolated-database confirmation;
- the documented host, port, database, and user tuple; and
- matching `POSTGRES_PASSWORD` and `AI_BAP_TEST_POSTGRES_PASSWORD` values.

The process-local presence-only inspection found that all required variable names were absent. No value was printed, inferred, generated, retrieved, or substituted.

## Database isolation evidence

Read-only Docker metadata inspection found an existing healthy `ai-bap-test` Compose resource:

- service container: `ai-bap-test-db-test-1`;
- Compose project label: `ai-bap-test`;
- Compose configuration: `compose.test.yaml` with the documented non-secret test variables file;
- loopback-only publication: `127.0.0.1:55432` to PostgreSQL port `5432`;
- dedicated named volume: `ai-bap-test_ai_bap_test_data`, labelled for the `ai-bap-test` project;
- container mount destination: `/var/lib/postgresql/data`.

This is independent structural evidence that the running resource matches the documented isolated test topology. It is not sufficient to authorize tests by itself: the process lacks the matching required test-only credentials and safety confirmations.

## Commands executed

| Command or check | Result |
| --- | --- |
| Read `AGENTS.md`, `docs/isolated-test-database.md`, `backend/tests/conftest.py`, and `backend/app/test_database_safety.py` | PASS |
| Branch, `HEAD`, index, and `git status --short` inspection | PASS — expected branch and committed head; empty index; unrelated pending files preserved |
| Presence-only inspection of the eight required guarded variable names | BLOCKED — all eight were absent; no values disclosed |
| Read-only Docker container, volume, label, port-binding, and mount inspection | PASS — structurally isolated `ai-bap-test` topology verified; no database connection was made |
| `uv run --no-sync pytest -q tests/test_migrate_production.py tests/test_render_free_deployment_configuration.py` | NOT RUN — blocked before execution because the required guarded environment values, including the test-only password, are absent in this process |
| `uv run --no-sync ruff check tests/test_migrate_production.py tests/test_render_free_deployment_configuration.py ../docker/backend/migrate_production.py ../docker/backend/start_api_free.py` | PASS — `All checks passed!` |
| `git diff --check` | PASS; only LF-to-CRLF working-copy warnings were emitted |

## Test results

No pytest test count, failure, or skip count exists because pytest was not authorized to start. The fail-closed guard was respected; no database was connected to, migrated, initialized, reset, truncated, or otherwise modified.

## Failures or blockers

The sole blocker is the absence of the documented test-only environment values in this Codex process. The existing Docker resource is healthy and structurally isolated, but isolation cannot be inferred from the resource alone, and credentials must not be recovered or replaced.

The documented safe operator procedure is to enter the existing test-only password interactively in the same PowerShell process, set the required non-secret confirmations and target tuple from `docs/isolated-test-database.md`, then invoke the focused pytest command. The password must not be pasted into chat or stored in a repository file.

## Working-tree preservation

No application or test file was modified in this step. This report is the only new ADIM 8.10.135 file and remains untracked. No file was staged, committed, pushed, merged, deployed, or provisioned.

## Recommended single next action

An authorized operator with the existing test-only password should run the documented guarded PowerShell setup and the focused pytest command in the same shell, then record the exact count and outcome.

## GO / NO-GO

- **NO-GO** for executing the guarded pytest command from this Codex process: required credentials and confirmations are unavailable.
- **GO (conditional)** for the documented operator-side focused test run after all guard prerequisites are present and verified in that shell.
