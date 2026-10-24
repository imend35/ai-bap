# ADIM 8.10.156 — Controlled Isolated Playwright E2E Execution

## 1. Objective

I executed the configured authenticated Playwright project-flow test against a newly created disposable Docker Compose stack and then removed only that stack's verified resources.

## 2. Git baseline

- Branch: `docs/ci-pr-evidence`.
- HEAD: `2afe0d4d88188ad0a8de14c590ca95d0536b1241`.
- Git index: empty before and after execution.
- Pre-existing modified frontend dependency files, the modified ADIM 8.10.76 report, E2E configuration/test files, and untracked Codex reports were preserved.

## 3. Disposable Compose identity and isolation

- Compose project: `ai-bap-e2e-156-7c9f`.
- Loopback-only ports: PostgreSQL `55436`, API `18002`, frontend `18082`.
- Before startup, no container, volume, or network carried this Compose-project label, and all three ports were unused.
- `docker compose -p ai-bap-e2e-156-7c9f config --quiet` passed with fresh process-local database credentials and JWT material.
- The resulting PostgreSQL volume and default network were inspected before cleanup. Their Compose labels identified only `ai-bap-e2e-156-7c9f` as owner.
- The separate `ai-bap-rubric-test` stack was inspected and remained unchanged throughout.

## 4. Service health and migration evidence

- Backend, migration, and frontend images built successfully.
- PostgreSQL became healthy.
- Migration service exited with code `0`.
- FastAPI became healthy.
- Frontend became healthy.
- Direct backend health: HTTP 200.
- Frontend root: HTTP 200.
- Same-origin frontend proxy health: HTTP 200.

## 5. Synthetic account preparation

I created a new random, least-privileged synthetic business-analyst account only in the disposable database. The successful registration returned HTTP 201. No account identifier, password, JWT, database URL, or connection value is retained in this report.

An earlier fixed synthetic address returned HTTP 409 because it was already present in the same disposable database after an interrupted command had progressed farther than its captured output. I did not modify that account; I used a newly generated synthetic address instead. Both accounts were removed with the disposable volume during cleanup.

## 6. Chrome browser execution

Playwright was given the explicit path of the already installed local Google Chrome executable through `AI_BAP_E2E_BROWSER_EXECUTABLE_PATH`. The test produced a real rendered page snapshot showing the authenticated frontend workspace and project form, which verifies Chrome launched and interacted with the local isolated frontend. No screenshots, videos, or traces were configured; the automatically generated failure-context artifact was removed after diagnosis.

## 7. UI login result

**PASS.** The browser test completed UI login with the synthetic account. The rendered authenticated workspace displayed the synthetic business-analyst identity and the Projects navigation control.

## 8. UI project creation result

**FAIL.** The test reached the Create New Project form and successfully filled the Project Name field. It then timed out looking for a field labelled `Project Description`.

The rendered UI labels that textarea as `Description`, not `Project Description`. This is a test-locator defect at `frontend/e2e/authenticated-project.spec.ts:35`, not a backend, migration, authorization, or Docker isolation failure. No application or test code was changed in this execution-only step.

## 9. Reload and re-authentication result

**BLOCKED.** The scenario halted before project submission because of the incorrect description locator. The reload, normal re-authentication, and project retrieval assertions were not reached.

## 10. PostgreSQL persistence result

**BLOCKED.** A count-only query in the labelled disposable PostgreSQL container found `0` projects with the synthetic E2E project prefix. This matches the halted UI flow: no project was submitted. No project row or user data was printed.

## 11. Cleanup and unrelated-resource preservation

- Before cleanup, I verified the disposable volume and network labels and the active project containers.
- `docker compose -p ai-bap-e2e-156-7c9f down -v` removed only this run's frontend, API, migration, and database containers, its default network, and `ai-bap-e2e-156-7c9f_postgres_data`.
- Post-cleanup checks found no containers, volumes, or networks with that project label.
- The `ai-bap-rubric-test` stack remained present and unchanged.
- The generated `frontend/test-results` directory was verified as created by this failed run and removed so that no browser failure artifact remains in the working tree.

## 12. PASS / FAIL / BLOCKED matrix

| Check | Result | Evidence |
| --- | --- | --- |
| Isolation preflight and Compose validation | PASS | Unique project, free loopback ports, no project-resource reuse, resolved configuration passed. |
| Database health and migration | PASS | PostgreSQL healthy; migration exited 0. |
| API, frontend, and proxy health | PASS | All required HTTP checks returned 200. |
| Synthetic account registration | PASS | Isolated registration returned 201. |
| Local Chrome launch | PASS | Real rendered authenticated page snapshot produced by Playwright using explicit local Chrome path. |
| UI login | PASS | Authenticated workspace reached. |
| Project form navigation and name entry | PASS | Projects page and Create New Project form reached; name field filled. |
| UI project creation | FAIL | Incorrect `Project Description` locator timed out; UI label is `Description`. |
| Reload and re-authentication | BLOCKED | Not reached after creation-locator failure. |
| Project persistence verification | BLOCKED | No project was created; count-only query returned 0. |
| Disposable Docker cleanup | PASS | Exact labelled resources removed; separate stack unchanged. |

## 13. Rubric impact

This is verified evidence that the isolated full stack can build, migrate, serve the actual frontend/API path, launch local Chrome, and complete browser UI login. It does **not** yet verify browser project creation, persistence across reload/re-authentication, an authenticated end-to-end success path, public deployment, production HTTPS, CD, observability, alerting, or on-call response.

## 14. Recommended single next action

Authorize a minimal correction of the Playwright test locator from `Project Description` to the UI's accessible `Description` label, then repeat the same controlled isolated execution.

## 15. GO / NO-GO

**NO-GO for claiming authenticated E2E project-flow completion.** The infrastructure, Chrome launch, and UI authentication portions passed, but the project-flow test requires the narrowly scoped locator correction and a successful rerun.
