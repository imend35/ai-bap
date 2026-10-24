# ADIM 8.10.167 — Fix Playwright Success Status Assertion

## 1. Objective

I corrected the authenticated Playwright test's project-creation success-message assertion without changing application behavior, API behavior, styling, dependencies, or assertion timeouts.

## 2. Git baseline

- Branch: `docs/ci-pr-evidence`
- HEAD: `2afe0d4d88188ad0a8de14c590ca95d0536b1241`
- Git index: empty before and after the change.
- Existing modified and untracked work was preserved.

## 3. Root cause

`frontend/src/App.tsx:3072-3076` renders a live status region with a leading checkmark:

```tsx
<div className="success-message" role="status">
  ✓ {success}
</div>
```

The former Playwright locator required the unprefixed string to be the exact rendered text. It could not match `✓ Project created successfully.` even though the application had set the success state.

## 4. Exact assertion change

I changed only the project-creation success assertion in `frontend/e2e/authenticated-project.spec.ts`:

```diff
 await expect(
-  page.getByText("Project created successfully.", { exact: true }),
-).toBeVisible();
+  page.getByRole("status"),
+).toContainText("Project created successfully.");
```

The new assertion targets the semantic live-status region and still requires the full expected message text. It accepts the deliberately rendered checkmark prefix without weakening the success condition.

## 5. Diff verification

- The only source change in this task is the intended assertion replacement above.
- Project creation, authentication, reload, reauthentication, and persisted-project assertions were left unchanged.
- No React, API, CSS, dependency, or configuration file was modified.

## 6. Playwright listing result

Command:

```powershell
$env:AI_BAP_E2E_BASE_URL = "http://127.0.0.1:18085"
$env:AI_BAP_E2E_ISOLATED = "true"
npm run test:e2e -- --list
```

**PASS.** Playwright listed one test in one file. This list-only command did not launch Chrome or execute the E2E scenario.

## 7. Vitest result

Command:

```powershell
npm run test -- --run
```

**PASS.** One test file and four tests passed.

## 8. Lint result

Command:

```powershell
npm run lint
```

**PASS with warnings.** Oxlint exited 0 and reported 16 pre-existing `react(set-state-in-effect)` warnings in `src/App.tsx`. No lint errors were reported.

## 9. Production build result

Command:

```powershell
npm run build
```

**PASS.** TypeScript and the Vite production build completed successfully.

## 10. Git preservation

No staging, commit, push, branch change, Docker operation, browser E2E execution, or dependency change occurred. This report remains untracked along with the pre-existing untracked E2E files and reports.

## 11. PASS / FAIL / BLOCKED matrix

| Check | Result |
| --- | --- |
| Semantic status assertion correction | PASS |
| Playwright list-only discovery | PASS |
| Existing Vitest suite | PASS — 4 tests |
| Frontend lint | PASS — 16 warnings, 0 errors |
| Frontend production build | PASS |
| Browser E2E execution | NOT RUN — explicitly excluded by this task |

## 12. Recommended single next action

**Authorize a new isolated Playwright E2E rerun with a fresh Compose project, synthetic credentials, loopback ports, count-only persistence verification, and ownership-verified cleanup.**

## 13. GO / NO-GO for isolated E2E rerun

**GO.** The test-only correction is source-supported and all allowed static checks passed. The complete browser workflow remains unverified until the separately authorized isolated rerun completes.
