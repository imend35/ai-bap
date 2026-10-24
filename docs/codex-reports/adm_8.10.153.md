# ADIM 8.10.153 — Browser Automation Capability Assessment

## 1. Objective

I assessed the safest available path for a real Chromium-based authenticated end-to-end test of the existing React, FastAPI, and PostgreSQL stack. This was a read-only assessment; I did not install packages, start Docker, or change application code.

## 2. Git and working-tree state

- Current branch: `docs/ci-pr-evidence`.
- Current local HEAD: `2afe0d4d88188ad0a8de14c590ca95d0536b1241`.
- The Git index was empty.
- The pre-existing modified `docs/codex-reports/adm_8.10.76.md` and pre-existing untracked Codex reports were preserved.
- This assessment adds only this untracked report.

## 3. Existing frontend test tooling

`frontend/package.json` defines Vitest, jsdom, React Testing Library, user-event, and jest-dom. The test configuration uses Vitest with `jsdom`; it supports mocked component tests, not a real Chromium browser.

`docs/testing-strategy.md` likewise describes mocked browser `fetch` responses and states that the current frontend suite does not use a real account, token, API, or Docker service. No project Playwright, Puppeteer, Cypress, Selenium, or WebDriver dependency, configuration file, CLI, or test suite is present.

## 4. Node.js and package-manager availability

- Node.js: `v26.8.1`.
- npm: `11.12.1`.
- pnpm: `10.34.7`.
- Yarn: not installed.
- The frontend lockfile is npm lockfile version 3.

## 5. Browser automation availability

- Playwright CLI: absent from `frontend/node_modules/.bin`.
- Puppeteer CLI: absent from `frontend/node_modules/.bin`.
- `@playwright/test`, `playwright`, `playwright-core`, `puppeteer`, and `puppeteer-core` are not installed project dependencies.
- The Vitest lockfile includes optional peer references to browser adapters, but the Playwright adapter is not installed.
- The Codex in-app browser provider was unavailable during ADIM 8.10.152 and could not be opened.

Therefore, no currently installed automation framework can drive the available browser binaries.

## 6. Chromium/Chrome availability

The host has compatible Chromium-based browser executables:

- Google Chrome is installed locally.
- Microsoft Edge is installed locally.

Their versions were inspected locally. No Playwright-managed browser cache was identified. The existing locally installed Chrome is the preferred test target because using an explicit executable path avoids a separate browser download.

## 7. Installation requirements

A real browser test requires one approved frontend development dependency installation. The smallest practical option is `@playwright/test`, installed with npm so that `frontend/package.json` and `frontend/package-lock.json` remain consistent.

No Playwright browser download is needed if the resulting test configuration launches the already installed Chrome executable explicitly. Installation remains subject to Human Product Owner approval because it changes project dependencies and the lockfile.

## 8. Recommended E2E architecture

1. Create a unique Compose project, such as `ai-bap-e2e-<run-id>`, with a fresh Docker-managed PostgreSQL volume and a unique network.
2. Select unused loopback-only ports for PostgreSQL, API, and frontend; never reuse the default, `ai-bap-test`, or `ai-bap-rubric-test` resources.
3. Set synthetic, process-local database/JWT values and enable the documented fresh isolated initializer only for the new disposable database.
4. Validate the resolved Compose configuration, labels, resource absence, and port availability before startup.
5. Build/start only that project; verify database, migration, API health, frontend HTTP, and same-origin proxy health.
6. Seed one least-privileged synthetic account only in the disposable database when required because the frontend currently has no registration flow.
7. Run Playwright against the frontend URL using the installed local Chrome executable: sign in through the UI, navigate to Projects, create one synthetic project, assert it appears in the UI, reload, and assert retrieval.
8. Query only the labelled disposable PostgreSQL container for a boolean persistence assertion about the synthetic project.
9. Inspect project labels and resource names, then run `docker compose -p <project> down -v` only for the confirmed disposable project; confirm unrelated stacks remain untouched.

## 9. Security and isolation safeguards

- Use only synthetic credentials and data, never local, cloud, or production secrets.
- Keep all published ports bound to `127.0.0.1`.
- Do not log account passwords, JWTs, database URLs, or SQL rows containing user data.
- Verify Compose ownership labels before cleanup; never use broad Docker pruning.
- Treat browser screenshots and Playwright traces as sensitive test artifacts; disable or redact them unless specifically needed for failure diagnosis.
- Fail closed if the target database, volume, network, or credentials cannot be shown to belong to the test project.

## 10. Risks and blockers

- **Blocking now:** no installed browser automation package or available Codex browser provider.
- **Dependency risk:** `@playwright/test` compatibility should be confirmed against Node 26 before installation; its lockfile update must be generated by npm, never edited manually.
- **Runtime risk:** the environment must permit local Chrome launch and CDP/automation; that can be verified only after approved installation.
- **Application constraint:** the UI lacks registration, so the test must safely pre-seed a least-privileged synthetic user in the isolated database before UI login.

## 11. Recommended next action

Obtain approval to add `@playwright/test` as a frontend development dependency and configure it to launch the already installed local Chrome executable for the isolated E2E journey.

## 12. GO / NO-GO

**NO-GO for execution today:** the required automation package is absent. **GO for a narrowly scoped dependency-installation and E2E-configuration step** once explicitly approved; the installed Chrome executable and isolated Compose design make that the smallest safe path.
