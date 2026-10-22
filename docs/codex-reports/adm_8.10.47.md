# ADIM 8.10.47 — Resolve Frontend Oxlint Warnings Safely

## Step name and objective

Investigate the 17 Oxlint warnings in `frontend/src/App.tsx` and resolve only
warnings that could be fixed without changing frontend behavior.

## Summary of completed work

- Inspected all reported warning locations and their shared data-loading,
  reset, and request-generation safeguards.
- Resolved the `eslint(no-unsafe-finally)` warning in the audit-history handler
  by replacing a `return` in `finally` with a guarded loading-state update.
- Preserved the request-generation behavior: only the current audit request can
  clear the audit loading indicator.
- Retained 16 `react(set-state-in-effect)` warnings because they represent
  required dependency-driven loads or page-exit invalidation. Removing them
  safely would require a larger loading-state architecture refactor and
  frontend regression tests.

## Files inspected or modified

Inspected:

- `frontend/src/App.tsx`
- `frontend/package.json`

Modified:

- `frontend/src/App.tsx`

This retrospective reconstruction replaces a misfiled ADIM 8.10.48 instruction
block that had occupied this report path.

## Commands executed and actual results

1. `npm run lint` before the change.
   - Result: PASS with 17 warnings: 16 `react(set-state-in-effect)` warnings
     and 1 `eslint(no-unsafe-finally)` warning.
2. Frontend test inventory search and `frontend/package.json` inspection.
   - Result: no frontend test files and no test script were configured.
3. `npm run lint` after the change.
   - Result: PASS with 16 retained `react(set-state-in-effect)` warnings; the
     `no-unsafe-finally` warning was resolved.
4. `npm run build`.
   - Result: PASS. `tsc -b && vite build` completed successfully.
5. `git diff --check` and focused `git diff -- src/App.tsx` review.
   - Result: PASS with no whitespace errors; existing line-ending advisory
     warnings were emitted.

## Validation and test results

- Oxlint: PASS with 16 warnings remaining (17 before the change).
- TypeScript/Vite production build: PASS.
- `git diff --check`: PASS.
- Frontend automated tests: NOT RUN; no test script or test files were present.

## Issues and remaining tasks

- The 16 retained warnings concern user-story, project, dashboard,
  traceability, delivery, and requirement loading effects or page-exit cleanup.
- A safe resolution requires a separately scoped state-management refactor with
  frontend regression coverage. No lint suppression, artificial deferral, or
  behavior-changing event-only replacement was added.

## Recommended next step

Add frontend test coverage, then plan a dedicated loading-state refactor to
address the remaining Oxlint warnings without breaking initial loading,
refreshes, pagination, or stale-response protection.
