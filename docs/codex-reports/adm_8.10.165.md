# ADIM 8.10.165 — Isolated Authenticated Playwright E2E Rerun

## 1. Objective

I reran the corrected authenticated Playwright project-flow test against a new disposable Docker Compose environment after verifying BuildKit registry connectivity. I used only loopback ports, fresh process-local synthetic values, and a project-specific managed PostgreSQL volume.

## 2. Git and Docker baseline

- Branch: `docs/ci-pr-evidence`
- HEAD: `2afe0d4d88188ad0a8de14c590ca95d0536b1241`
- Git index: empty before and after the run.
- Pre-existing modified and untracked work was preserved.
- The pre-existing `ai-bap-rubric-test` stack baseline was four containers, one volume, and one network.

## 3. Isolation preflight

The completed execution used the new Compose project `ai-bap-e2e-165-8b6d`.

| Isolation check | Result |
| --- | --- |
| Project-labelled containers, volumes, and networks existed before startup | No |
| PostgreSQL loopback port | `55439`, free before startup |
| API loopback port | `18005`, free before startup |
| Frontend loopback port | `18085`, free before startup |
| Resolved database volume | `ai-bap-e2e-165-8b6d_postgres_data` |
| Volume type | Managed, non-external Compose volume |
| Explicit container names | None |
| Host networking or privileged services | None |

The Compose configuration used the standard application build contexts without a Compose or application-file modification.

## 4. Disposable stack configuration

I supplied fresh process-local values for the isolated PostgreSQL database, database user and password, JWT key, loopback ports, and the `AI_BAP_INITIALIZE_FRESH_DATABASE` confirmation. I also created a newly generated synthetic least-privileged business-analyst account for the browser test. No credential, JWT, database URL, account address, or password is retained in this report.

An initial disposable project, `ai-bap-e2e-165-4e7b`, was started and then cleaned up after an execution-wrapper error queried the one-shot migration service without including exited containers. No browser test was run in that project. Its labelled containers, network, and volume were ownership-verified and removed before the final run.

## 5. Build and service readiness

**PASS.** For `ai-bap-e2e-165-8b6d`, Docker Compose rebuilt the backend, migration, and frontend images and created only the project-labelled network and volume.

| Check | Result |
| --- | --- |
| PostgreSQL health | Healthy |
| Migration service | Exit code 0 |
| FastAPI health | Healthy |
| Frontend Nginx health | Healthy |
| `http://127.0.0.1:18005/api/v1/health` | HTTP 200 |
| `http://127.0.0.1:18085/` | HTTP 200 |
| `http://127.0.0.1:18085/api/v1/health` | HTTP 200 |

## 6. Database migration and synthetic account

The fresh Compose migration service completed successfully against only the disposable project database. The synthetic business-analyst registration request returned HTTP 201 from the isolated API. The account was removed together with the disposable database volume during cleanup.

## 7. Playwright execution

The existing `npm run test:e2e` command launched Playwright with the already installed local Google Chrome executable and the required loopback-only `AI_BAP_E2E_*` environment variables.

The test used the corrected exact accessible locator:

```ts
page.getByLabel("Description", { exact: true })
```

## 8. E2E checkpoint results

| Checkpoint | Result | Evidence |
| --- | --- | --- |
| Chrome browser launch | PASS | Playwright executed the rendered browser test. |
| UI authentication | PASS | The test reached the authenticated Projects workflow. |
| Projects navigation | PASS | The test advanced to the Projects page and new-project flow. |
| Project form interaction | PASS | Project name and corrected `Description` textarea locator were filled. |
| Project submission and persistence | PASS | A count-only query found one project matching the synthetic E2E prefix in the disposable PostgreSQL database. |
| UI success confirmation | FAIL | The expected exact success text was not visible within Playwright's five-second timeout. |
| Browser reload | BLOCKED | The test stopped at the failed success-confirmation assertion. |
| Reauthentication after reload | BLOCKED | Not reached. |
| Persisted-project retrieval after reload | BLOCKED | Not reached, despite direct database persistence evidence. |

## 9. Failure analysis

Playwright failed at `frontend/e2e/authenticated-project.spec.ts:42` while waiting for the exact text `Project created successfully.`. Source inspection confirms that `frontend/src/App.tsx:2040` sets that same success message after project creation and refresh. The test did not reach its reload assertions.

The count-only database query returned `1` for the E2E project-name prefix in the fresh disposable database. Therefore, the form submission reached the backend and created a persisted project. The available execution evidence does not establish why the success message was not rendered or visible within the test timeout. No test or application change was made in response.

## 10. Isolated-resource cleanup

Before cleanup, I verified that all four project containers, the database volume, and the default network carried the `ai-bap-e2e-165-8b6d` Compose-project ownership label. I then executed project-scoped cleanup only.

| Resource | Post-cleanup result |
| --- | --- |
| Project containers | 0 remaining |
| `ai-bap-e2e-165-8b6d_postgres_data` | Removed |
| `ai-bap-e2e-165-8b6d_default` | Removed |
| Project API, migration, and frontend image tags | Removed after exact task-ownership verification |
| Generated Playwright failure-artifact directory | Removed after confirming it was generated by this run |

No Docker prune command, shared-layer deletion, cache deletion, or broad cleanup was used.

## 11. Unrelated-resource preservation

After cleanup, `ai-bap-rubric-test` still had four containers, one volume, and one network—the same baseline observed before execution. No other Docker resource was intentionally changed.

## 12. Git preservation

No file tracked by Git was modified. The index remains empty. The only task output is this new untracked report; all pre-existing working-tree changes remain pending.

## 13. PASS / FAIL / BLOCKED matrix

| Verification | Status |
| --- | --- |
| Compose isolation preflight | PASS |
| Build and service readiness | PASS |
| Fresh-database migration | PASS |
| Synthetic-account registration | PASS |
| Local Chrome browser execution | PASS |
| UI authentication and form interaction | PASS |
| Project persistence in isolated PostgreSQL | PASS |
| UI success confirmation | FAIL |
| Reload, reauthentication, and post-reload retrieval | BLOCKED |
| Project-scoped Docker and generated-artifact cleanup | PASS |
| Pre-existing Docker-resource preservation | PASS |

## 14. Recommended single next action

**Authorize a narrowly scoped diagnostic review of the project-creation success-message lifecycle and the Playwright assertion timing, then make and validate the smallest evidence-based test or UI correction.**

## 15. GO / NO-GO conclusion

**NO-GO for claiming a complete authenticated browser E2E journey.** The isolated environment, browser authentication, corrected project form interaction, and database persistence are verified. The required visible success confirmation and reload/re-authentication/retrieval path remain unverified because the test stopped at the success-message assertion.
