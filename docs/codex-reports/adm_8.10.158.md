# ADIM 8.10.158 — Controlled Isolated Playwright E2E Rerun

## 1. Objective

I prepared and attempted a rerun of the corrected authenticated Playwright project-flow test against a new isolated Docker Compose project. The run stopped at the image-build stage because Docker Desktop could not resolve Docker Hub. No browser, database, or application test execution occurred.

## 2. Git and working-tree baseline

- Branch: `docs/ci-pr-evidence`.
- HEAD: `2afe0d4d88188ad0a8de14c590ca95d0536b1241`.
- Git index: empty.
- Existing modified frontend dependency files, E2E configuration/test files, the modified ADIM 8.10.76 report, and existing untracked reports were preserved.

## 3. Disposable Compose identity and isolation

- Proposed unique Compose project: `ai-bap-e2e-158-4d8a`.
- Proposed loopback-only ports: PostgreSQL `55437`, API `18003`, frontend `18083`.
- Preflight found all selected ports free.
- No containers, volumes, or networks carried the selected project label before the attempt.
- The Compose configuration validated successfully with newly generated process-local database credentials and JWT material. No values were displayed or persisted.

## 4. Service health and migration evidence

**BLOCKED before startup.** Docker image build failed while attempting to refresh base-image metadata. Docker Desktop reported DNS resolution failure for `registry-1.docker.io` while resolving the required `node`, `nginx`, and `python` base images.

Because build did not complete:

- PostgreSQL health: not run.
- Migration service: not run.
- Backend and frontend health: not run.
- Direct API, frontend root, and same-origin proxy checks: not run.

I did not change Docker Desktop DNS, proxy, network, image, or application configuration and did not attempt an unapproved workaround.

## 5. Synthetic account preparation

**NOT RUN.** No database was created or started, so no synthetic account was registered.

## 6. Chrome browser execution

**NOT RUN.** The stack did not reach a runnable frontend state; Playwright and Chrome were not launched.

## 7. UI login result

**BLOCKED** by the Docker base-image registry DNS failure.

## 8. UI project creation result

**BLOCKED** by the Docker base-image registry DNS failure.

## 9. Reload and re-authentication result

**BLOCKED** by the Docker base-image registry DNS failure.

## 10. PostgreSQL persistence result

**BLOCKED** by the Docker base-image registry DNS failure. No database or project was created.

## 11. Cleanup and unrelated-resource preservation

Post-failure inspection found no containers, volumes, or networks labelled `ai-bap-e2e-158-4d8a`; the build failed before resource creation. Therefore no `down -v` command was necessary or executed.

The existing `ai-bap-rubric-test` containers and persistent volume were inspected and remained unchanged.

## 12. PASS / FAIL / BLOCKED matrix

| Check | Result | Evidence |
| --- | --- | --- |
| New project identity and port isolation | PASS | Unique label, absent resources, and free loopback ports verified. |
| Resolved Compose validation | PASS | `docker compose ... config --quiet` passed with process-local test values. |
| Docker image build | FAIL | Docker Desktop could not resolve `registry-1.docker.io` base-image metadata. |
| Stack startup, migration, and health checks | BLOCKED | Build failure occurred first. |
| Synthetic-account registration | BLOCKED | Disposable database never started. |
| Local Chrome / Playwright | BLOCKED | Frontend never started. |
| UI login, project creation, reload, retrieval | BLOCKED | Browser test was not started. |
| PostgreSQL persistence query | BLOCKED | Disposable database never started. |
| Project-resource cleanup | PASS | No labelled resources were created; existing resources unchanged. |

## 13. Rubric impact assessment

ADIM 8.10.157 corrected the confirmed Playwright locator, but this ADIM contributes no new successful authenticated E2E evidence because the infrastructure could not be rebuilt. ADIM 8.10.156 remains the verified evidence for isolated startup, Chrome launch, and UI login only; it does not establish successful project creation or persistence evidence.

## 14. Recommended single next action

Restore Docker Desktop registry DNS connectivity through an operator-approved local Docker/Desktop networking action, then rerun this ADIM with a new project name and fresh isolation preflight.

## 15. GO / NO-GO

**NO-GO for the isolated E2E rerun.** The corrected test was not executed because Docker could not resolve required public base-image metadata. No application, test, Docker, or Git configuration was changed.
