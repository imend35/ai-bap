# ADIM 8.10.155 — Playwright Configuration and Isolated E2E Test Implementation

## 1. Objective

I implemented a single maintainable Playwright test for an authenticated, isolated React-to-FastAPI project workflow. I did not launch Chrome, start Docker, or execute the browser test.

## 2. Git and working-tree baseline

- Branch: `docs/ci-pr-evidence`.
- HEAD: `2afe0d4d88188ad0a8de14c590ca95d0536b1241`.
- Git index: empty.
- Existing modifications to `frontend/package.json` and `frontend/package-lock.json` from ADIM 8.10.154, the modified ADIM 8.10.76 report, and pre-existing untracked reports were preserved.

## 3. Existing UI and API workflow findings

- The sign-in form uses accessible `Email address`, `Password`, and `Sign In` controls and calls the actual login API followed by profile verification.
- Business analysts are permitted to create projects. The authenticated interface exposes `Projects`, `New Project`, labelled project fields, and a `Create Project` action.
- New public registrations produce a least-privileged active business-analyst account, suitable only for a disposable isolated database.
- The frontend keeps its access token in memory. A page reload deliberately returns to sign-in; the E2E test re-authenticates through the normal UI before verifying the persisted project.
- Compose binds frontend/API/database ports to loopback addresses, and nginx proxies `/api/` to the API service through the Compose network.

## 4. Playwright configuration

`frontend/playwright.config.ts` now:

- Requires `AI_BAP_E2E_BASE_URL` and parses it as a URL.
- Accepts only `http` URLs whose host is `127.0.0.1`, `localhost`, or `::1`.
- Requires `AI_BAP_E2E_ISOLATED=true` exactly.
- Uses Chrome's supported Playwright channel by default, or an explicit `AI_BAP_E2E_BROWSER_EXECUTABLE_PATH` override; no machine-specific path is committed.
- Uses one worker, no retries, and disables screenshots, traces, and video.
- Registers only tests under `frontend/e2e`.

The new `test:e2e` package script runs Playwright. The existing Vitest script excludes only `e2e/**`, because Vitest otherwise discovers the Playwright `.spec.ts` file. No Vitest configuration file changed and the existing unit-test scope remains intact.

## 5. E2E scenario implementation

`frontend/e2e/authenticated-project.spec.ts` implements one test that, when run against an approved isolated stack:

1. Signs in with environment-provided synthetic credentials through the actual frontend.
2. Navigates to Projects.
3. Creates a timestamp-named synthetic project via the UI.
4. Confirms the success notice and project text in the UI.
5. Reloads the page, observes the expected sign-in state, signs in again, and confirms the same project remains visible.

The timestamped project name avoids collisions across disposable runs. The test uses accessible labels and roles already present in the UI; no application selectors or business logic changed.

## 6. Loopback and isolation safeguards

- The browser base URL fails closed unless it is explicitly supplied and loopback-only.
- The test cannot start unless `AI_BAP_E2E_ISOLATED` is literal `true`.
- The test requires `AI_BAP_E2E_EMAIL` and `AI_BAP_E2E_PASSWORD` only at test runtime.
- No test credential, token, connection string, or browser path is committed.
- The configuration intentionally contains no Docker lifecycle or database cleanup commands. A separate execution procedure must verify unique Compose ownership and cleanup before running the test.

## 7. Synthetic credential handling

The test reads only `AI_BAP_E2E_EMAIL` and `AI_BAP_E2E_PASSWORD` at runtime and validates their presence without outputting their values. The future executor must create the least-privileged account solely in the newly created isolated database and must never point the test at a shared or persistent environment.

## 8. Static checks and existing test results

Executed from `frontend` without launching a browser:

```powershell
$env:AI_BAP_E2E_BASE_URL='http://127.0.0.1:18081'
$env:AI_BAP_E2E_ISOLATED='true'
npm run test:e2e -- --list
npm run test -- --run
npm run lint
npm run build
```

Results:

- Playwright list-only validation: **1 test in 1 file**; no browser test was run.
- Missing-configuration validation: the configuration rejected a run with required isolation settings absent.
- Vitest: **4 passed**, 1 file passed.
- oxlint: exit code 0 with the pre-existing 16 non-blocking `react(set-state-in-effect)` warnings in `src/App.tsx`.
- Production build: passed.

An initial static validation revealed that Vitest's default discovery attempted to load the Playwright `.spec.ts` file. I corrected this by excluding only `e2e/**` in the existing Vitest package script, then reran the checks successfully.

## 9. Exact changed-file inventory

| Path | Change |
| --- | --- |
| `frontend/package.json` | Added `test:e2e` and excluded Playwright's `e2e/**` directory from the existing Vitest command. The Playwright dependency was pre-existing work from ADIM 8.10.154. |
| `frontend/playwright.config.ts` | Added fail-closed loopback/isolation configuration. |
| `frontend/e2e/authenticated-project.spec.ts` | Added one authenticated project creation/reload scenario. |
| `docs/codex-reports/adm_8.10.155.md` | Added this untracked implementation report. |

`frontend/package-lock.json` was not modified by this step.

## 10. Risks and blockers

- The browser test has not been executed; browser channel compatibility and end-to-end behavior remain unverified.
- The configured Chrome channel depends on local Chrome availability at execution time; the optional executable-path variable offers an explicit operator override.
- The test verifies browser persistence after re-authentication because the application intentionally does not persist access tokens through reload.
- PostgreSQL-level persistence verification and exact Compose cleanup are intentionally outside this source-only configuration step and must be performed by the future isolated execution procedure.

## 11. Recommended single next action

Authorize one controlled isolated Docker Compose E2E execution using a unique project name, loopback ports, synthetic runtime values, a synthetic analyst account, and the documented `npm run test:e2e` command.

## 12. GO / NO-GO for isolated E2E execution

**GO, with controlled execution authorization.** The test is configured to reject non-loopback or non-isolated targets and does not retain sensitive artifacts by default. Runtime execution, including Docker startup and cleanup, remains separately required and was not performed here.
