# ADIM 8.10.152 — Isolated Authenticated End-to-End Smoke Test

## Objective

I attempted one complete authenticated journey through the React frontend, FastAPI backend, and a disposable PostgreSQL database, without affecting existing containers, volumes, databases, or Git state.

## Environment and isolation verification

- Repository state before the test: branch `docs/ci-pr-evidence`, HEAD `2afe0d4d88188ad0a8de14c590ca95d0536b1241`, with an empty Git index. Pre-existing modified and untracked Codex reports were preserved.
- I used the unique Compose project `ai-bap-e2e-152` with loopback-only ports `55435`, `18001`, and `18081`.
- Before startup, no containers, volumes, or networks carried the `ai-bap-e2e-152` Compose-project label; the selected ports were free.
- `docker compose -p ai-bap-e2e-152 config --quiet` completed successfully.
- The test project created its own `ai-bap-e2e-152_postgres_data` volume and `ai-bap-e2e-152_default` network. Their inspected labels identified `ai-bap-e2e-152` as the owning Compose project.
- The pre-existing `ai-bap-rubric-test` resources were separately identified and were not used or altered.

## Synthetic account and data strategy

I used a new least-privileged, synthetic business-analyst account only inside the isolated database. The account was seeded through the documented registration API because the current frontend exposes sign-in but no public registration screen. No account identifier, password, JWT, database URL, or connection value is recorded here.

## Stack startup and health evidence

- The backend, migration, and frontend images built successfully.
- PostgreSQL, FastAPI, and frontend services became healthy.
- The migration service completed with exit code `0`.
- Direct backend health check: HTTP 200.
- Frontend root response: HTTP 200.
- Same-origin frontend proxy health check: HTTP 200.

## Browser, UI, persistence, and reload evidence

Browser automation was unavailable in this execution environment: the available in-app browser provider could not be opened. In accordance with the task requirement, I did not substitute API-only testing for browser E2E verification.

- The synthetic account registration in the isolated stack succeeded (HTTP 201), but browser authentication was not executed.
- No project was created through the UI.
- No database persistence query was executed for a UI-created project.
- No browser reload/retrieval check was executed.

## Cleanup and resource preservation

After inspecting the disposable project's container, volume, and network ownership labels, I ran `docker compose -p ai-bap-e2e-152 down -v`. Cleanup removed only that project's four containers, dedicated volume, and network. Post-cleanup checks found no remaining resources with that project label. The separately existing `ai-bap-rubric-test` services and volume remained present and healthy/unchanged.

## PASS / FAIL / BLOCKED matrix

| Check | Result | Evidence |
| --- | --- | --- |
| Compose isolation preflight | PASS | Unique project, dedicated volume/network, free loopback ports, and no resource reuse. |
| Image build and isolated startup | PASS | Backend, migration, and frontend images built; required services started. |
| PostgreSQL health | PASS | Compose health status reported healthy. |
| Alembic migration | PASS | Migration service exited with code 0. |
| Backend health endpoint | PASS | `GET /api/v1/health` returned HTTP 200. |
| Frontend availability | PASS | `GET /` returned HTTP 200. |
| Same-origin API proxy | PASS | `GET /api/v1/health` through the frontend returned HTTP 200. |
| Synthetic-account preparation | PASS | Isolated registration request returned HTTP 201. |
| Browser authentication | BLOCKED | No usable browser automation provider was available. |
| Project creation through the UI | BLOCKED | Depends on browser automation; no API substitute was used. |
| PostgreSQL persistence of UI-created project | BLOCKED | No UI project was created. |
| Reload and UI retrieval | BLOCKED | Depends on browser automation. |
| Disposable resource cleanup | PASS | Only `ai-bap-e2e-152` resources were removed; pre-existing resources remained untouched. |

## Rubric impact

This run adds verified local, isolated full-stack startup and health evidence, including migration completion and frontend proxy routing. It does **not** demonstrate an authenticated browser user journey, UI project creation, persisted UI data, public deployment, production HTTPS, continuous deployment, observability, alerting, or an on-call response.

## Recommended next action and final status

**NO-GO for authenticated E2E evidence:** repeat this test in an environment with an available browser automation provider, using the same isolated-project safeguards, and verify login, UI project creation, database persistence, and reload. The infrastructure-only isolated smoke checks are complete and safely cleaned up.
