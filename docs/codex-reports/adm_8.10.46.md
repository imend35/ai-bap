# ADIM 8.10.46 — Fix Frontend TypeScript Build Errors

## Step name and objective

Resolve the two TS2322 errors caused by passing reset callbacks with an optional boolean parameter directly to React button `onClick` handlers, without changing frontend behavior.

## Summary of work completed

- Inspected `resetTaskForm(force = false)` and `resetProjectForm(force = false)` and their call sites.
- Replaced the two direct event-handler references with zero-argument callbacks:
  - `onClick={() => resetTaskForm()}`
  - `onClick={() => resetProjectForm()}`
- The reset functions and their optional `force` parameter were not changed. Programmatic forced resets continue to call each function with `true`.
- No unrelated frontend, backend, migration, database, or configuration files were changed by this step.

## Files inspected or modified

Modified:

- `frontend/src/App.tsx`

Created:

- `docs/codex-reports/adm_8.10.46.md`

## Commands executed and results

1. `npm run build`
   - PASS. `tsc -b && vite build` completed successfully.
2. `npm run lint`
   - PASS (exit status zero). Oxlint reported 17 existing warnings in `src/App.tsx`; they were intentionally not addressed in this step.
3. `git diff --check`
   - PASS. No whitespace errors. Git emitted existing LF-to-CRLF advisory warnings only.

## Test results

- TypeScript production build: PASS
- Frontend lint: PASS with 17 warnings
- `git diff --check`: PASS
- Automated tests: NOT RUN (not requested)

## Issues and remaining tasks

The remaining lint warnings were outside this step's scope:

- 16 `react(set-state-in-effect)` warnings in `src/App.tsx`
- 1 `eslint(no-unsafe-finally)` warning in `src/App.tsx:1442`

## Recommended next step

Address the existing Oxlint warnings in a separately scoped frontend cleanup task, preserving current state-management behavior.
