# ADIM 8.10.64 — Isolated Full-Stack Docker Runtime Verification

## Step Name and Objective

Build and verify the complete AI BAP Docker Compose application in a separate, disposable environment without modifying existing local application data, containers, or volumes.

## Isolation Preflight Results

- Required context was read: `AGENTS.md`, `compose.yaml`, `.env.example`, `README.md`, and `docs/isolated-test-database.md`.
- Existing active projects included `ai-bap`, `ai-bap-test`, and `ai-bap-legacy-migration-test`; none was stopped, modified, or reused.
- Existing `ai-bap_postgres_data`, isolated-test, and legacy-test volumes were identified and excluded from the test plan.
- The default application uses host ports 5433, 8000, and 8080 (with 8000 occupied by another local service). The isolated plan selected unused loopback ports 55434, 58000, and 58001.
- No explicit container names or external Docker resources are declared in `compose.yaml`.
- The project name `ai-bap-rubric-test` did not exist before the attempt.
- The disposable physical volume name `ai-bap-rubric-test_postgres_data` did not exist before the attempt.

## Isolated Test Configuration

- Compose project: `ai-bap-rubric-test`.
- Disposable database volume: `ai-bap-rubric-test_postgres_data`.
- Loopback ports: PostgreSQL 55434, FastAPI 58000, frontend 58001.
- A temporary environment file outside the repository used generated test-only database and JWT values. Values were never printed.
- A temporary override outside the repository mapped the service volume key to the isolated physical volume and replaced all host-port mappings.
- Resolved Compose validation confirmed the expected project, volume, and all three isolated ports.

## Commands Executed and Actual Results

- Read-only Docker inventory and port inspection: PASS. Existing application containers, isolated test containers, legacy-test containers, volumes, and occupied ports were identified.
- Initial temporary-environment Compose validation: FAIL. The generated temporary file lacked line separators; no Docker resource was created.
- Corrected temporary-environment validation: FAIL. The first override referred to an undefined Compose volume key; no Docker resource was created.
- Corrected override validation: PASS. `docker compose --project-name ai-bap-rubric-test ... config --quiet` exited 0 and resolved the isolated project, volume, and ports.
- Isolated build/start: FAIL. Docker Desktop could not resolve `registry-1.docker.io`, so metadata for `python:3.13-slim`, `node:22-alpine`, and `nginx:1.27-alpine` could not be fetched. Compose exited 1 before starting services.
- Post-failure resource inspection: PASS. Project container count was 0; disposable volume did not exist; existing `ai-bap_postgres_data` remained present.
- Temporary test environment and override cleanup: PASS. Only the two explicitly created temporary files were removed.

## Services Built and Started

No images completed build and no `ai-bap-rubric-test` containers started. The intended isolated services were `db`, `migrate`, `api`, and `frontend`.

## Health-Check and Smoke-Test Results

| Verification | Result | Evidence |
| --- | --- | --- |
| Isolated Compose configuration | PASS | Project, volume, and ports resolved as planned. |
| Image build | FAIL | External Docker registry DNS/proxy resolution failed. |
| PostgreSQL readiness | NOT RUN | No database container started. |
| Fresh-database initialization | NOT RUN | No database container started. |
| FastAPI startup and `/api/v1/health` | NOT RUN | API image/service did not start. |
| Frontend nginx HTTP response | NOT RUN | Frontend image/service did not start. |
| Same-origin `/api/` reverse proxy | NOT RUN | Frontend and API did not start. |
| Database connectivity | NOT RUN | No disposable database was created. |
| Synthetic end-to-end API smoke flow | NOT RUN | Runtime prerequisites were unavailable. |

## Database Safety Confirmation

- No production or development database connection was made.
- No existing container or volume was stopped, removed, reset, or migrated.
- The test volume was not created; therefore no volume deletion was necessary.
- The existing default application volume remains untouched.
- No database write, migration, or synthetic API data creation occurred.

## Issues and Remaining Tasks

- Docker Desktop requires working DNS/proxy access to `registry-1.docker.io` or pre-pulled compatible base images before the images can build.
- Runtime verification remains blocked by this external image-registry connectivity issue, not by a demonstrated application failure.
- The initial temporary-file formatting and override-key errors were corrected before the build attempt; static isolated Compose validation passed.

## Recommended Next Step

Restore Docker Desktop registry DNS/proxy connectivity or preload the required base images, then repeat the same isolated `ai-bap-rubric-test` procedure with unique ports and the dedicated disposable volume. Run service health, frontend/API proxy, and non-sensitive synthetic smoke checks only after images build successfully.
