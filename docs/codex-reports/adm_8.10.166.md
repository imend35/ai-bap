# ADIM 8.10.166 — Project Creation Success Message Lifecycle Diagnostics

## 1. Objective

I performed a static, read-only diagnosis of why the isolated Playwright project-flow test did not observe `Project created successfully.` after the project was persisted in ADIM 8.10.165. I did not start Docker, run browser tests, or modify application or test code.

## 2. Git baseline

- Branch: `docs/ci-pr-evidence`
- HEAD: `2afe0d4d88188ad0a8de14c590ca95d0536b1241`
- Git index: empty.
- Existing modified and untracked files, including frontend Playwright work and earlier Codex reports, were preserved.

## 3. Project creation control flow

The project form submits through `handleCreateProject` in `frontend/src/App.tsx:2019-2047`.

1. The handler prevents native form submission and sets `isSaving` to `true`.
2. It clears `error` and `success` at `frontend/src/App.tsx:2021-2023`.
3. It performs the authenticated `POST /api/v1/projects` request at `frontend/src/App.tsx:2025-2032`.
4. On a successful response it resets the form state and hides the project form at `frontend/src/App.tsx:2033-2037`.
5. It resets the project offset, awaits `loadProjects(0, projectArchiveFilter)`, and then sets the success state at `frontend/src/App.tsx:2038-2040`.
6. It clears `isSaving` in `finally` at `frontend/src/App.tsx:2045-2046`.

ADIM 8.10.165 independently showed a persisted project in the disposable database. That runtime evidence is consistent with the POST request completing successfully.

## 4. Success-message state lifecycle

`success` is initialized as an empty string at `frontend/src/App.tsx:417`. The project-creation handler sets it to `Project created successfully.` only after the project-list refresh completes.

`loadProjects` at `frontend/src/App.tsx:699-743` sets `isLoading`, clears only `error`, fetches the project page, updates project state, and finally clears `isLoading`. It neither clears nor replaces `success`.

The source includes explicit `setSuccess("")` calls for logout, navigation buttons, create actions, project edit startup, and other workflows. No static source path invoked by the creation handler clears the newly set message after `frontend/src/App.tsx:2040`.

## 5. Rendered DOM and accessibility analysis

The status region is always rendered above the selected page content when `success` is non-empty:

```tsx
{success && (
  <div className="success-message" role="status">
    ✓ {success}
  </div>
)}
```

Source: `frontend/src/App.tsx:3072-3076`.

Therefore, when project creation succeeds, the rendered element's text content is:

```text
✓ Project created successfully.
```

It has an accessible live-status role (`role="status"`). The status region is outside the conditional Projects-page block, so hiding the project form does not remove it. The success-message CSS at `frontend/src/App.css:228-233` supplies ordinary visual styling and does not statically indicate hiding or removal.

## 6. Playwright assertion analysis

The test at `frontend/e2e/authenticated-project.spec.ts:40-42` uses:

```ts
await expect(
  page.getByText("Project created successfully.", { exact: true }),
).toBeVisible();
```

With `exact: true`, the locator requires the rendered text to equal the supplied string. The source-rendered text contains the leading checkmark and space. The assertion therefore does not match the status element even when `success` has the expected application message.

This directly explains both pieces of ADIM 8.10.165 evidence: the persisted project confirms the create request completed, and the exact unprefixed-text locator could not find the rendered status element.

## 7. Confirmed findings

| Finding | Evidence |
| --- | --- |
| The application sets the project-created success state after the list refresh. | `frontend/src/App.tsx:2038-2040` |
| The project-list refresh does not clear the success state. | `frontend/src/App.tsx:699-743` |
| The rendered status includes a leading `✓ ` prefix. | `frontend/src/App.tsx:3072-3076` |
| The E2E assertion requires an exact string without that prefix. | `frontend/e2e/authenticated-project.spec.ts:40-42` |
| The isolated test persisted a project before failing at this assertion. | ADIM 8.10.165 count-only database evidence |

## 8. Unverified hypotheses

The following are not needed to explain the observed failure and were not tested at runtime:

- Whether the live-region announcement timing differs across browsers or accessibility trees.
- Whether a separate concurrent UI action can clear `success` after a successful creation.
- Whether a failed list refresh can affect the visible state in circumstances other than the ADIM 8.10.165 run.

No static evidence supports treating any of these as the root cause of this failure.

## 9. Root-cause conclusion

**Confirmed root cause: the test's exact-text locator omits the checkmark prefix deliberately rendered by the application status region.** This is a test-locator defect, not evidence that project creation, backend persistence, or the application success-state assignment failed.

## 10. Smallest recommended correction

Change only the success-message assertion to query the semantic live-status region with a regular expression that accepts the visual prefix while preserving the expected message content:

```ts
await expect(
  page.getByRole("status", { name: /Project created successfully\./ }),
).toBeVisible();
```

This does not increase a timeout, weaken the message requirement, or modify application behavior. It asserts the accessible status element rather than a mismatched exact text node.

## 11. Validation plan

After separately authorizing the narrowly scoped test edit:

1. Run Playwright list-only validation with non-secret loopback configuration.
2. Run the existing frontend Vitest suite, lint, and production build.
3. Authorize a new disposable Compose E2E run with a fresh project label, fresh loopback ports, synthetic credentials, and ownership-verified cleanup.
4. Verify the success status, project visibility, reload, normal reauthentication, post-reload retrieval, and count-only database persistence.

## 12. Git and resource preservation

No Docker resource, browser, application file, test file, dependency, Git index entry, branch, or configuration was changed. This report is the only new file from this task and remains untracked.

## 13. PASS / FAIL / BLOCKED matrix

| Diagnostic check | Result |
| --- | --- |
| Static project-creation flow trace | PASS |
| Static success-state lifecycle trace | PASS |
| Rendered status text and role analysis | PASS |
| Exact Playwright locator comparison | PASS |
| Root-cause identification | PASS |
| Browser confirmation of corrected locator | BLOCKED — explicitly outside this diagnostic step |

## 14. Recommended single next action

**Authorize the single assertion-locator change in `frontend/e2e/authenticated-project.spec.ts` from exact unprefixed text to the accessible `status` role locator above.**

## 15. GO / NO-GO for implementation

**GO.** The proposed test-only correction is minimal, directly supported by source and execution evidence, and preserves the meaningful visible-success requirement. A separate isolated browser E2E rerun is still required before claiming end-to-end completion.
