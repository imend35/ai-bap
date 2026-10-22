# AI BAP — Final Project Rubric Gap Analysis

**Assessment date:** October 22, 2026<br>
**Authoritative rubric:** [Project.md](Project.md)<br>
**Assessment basis:** Repository evidence inspected locally. This assessment does not treat documentation alone as proof that a runtime, deployment, automation workflow, or test result exists.

## Conservative Current Score

**9 / 24 points (conservative estimate).**

The repository has a well-specified, authenticated React/FastAPI/PostgreSQL application with verified frontend and backend test execution. It is not yet positioned as a production-ready course submission because the rubric's operational requirements—full-system containerization, CI/CD, deployment, observability, alerting, and an on-call agent—are not implemented or evidenced. The mandatory three peer reviews are also a separate passing requirement.

## Evidence Summary

- `README.md` documents the problem, features, setup, limitations, and recorded validation evidence.
- `product-spec.md`, `docs/project-charter.md`, `docs/architecture.md`, and `openapi.yaml` describe implemented product behavior and API contracts.
- `backend/app/main.py` registers the FastAPI API groups; `backend/app/database.py` configures SQLAlchemy; migrations establish PostgreSQL persistence.
- `frontend/src/App.tsx` calls the versioned backend API using `VITE_API_BASE_URL`.
- `backend/tests/` contains API-integration and unit/contract-style test files. `frontend/src/App.test.tsx` provides Vitest coverage for authentication and protected-project behavior, and `scripts/test-all.ps1` completed with 515 passing tests.
- `compose.yaml` runs PostgreSQL only. `compose.test.yaml` is an isolated test-database topology. The only tracked Dockerfile supports migration rehearsal, not the full application runtime.
- No `.github/workflows/` files, deployment configuration, or source evidence of OpenTelemetry, metrics UI, alerting, or responder-agent automation were found.

## Rubric Assessment

| # | Criterion | Evidence paths | Existing implementation | Missing requirement / evidence | Status | Conservative points | Specific next action |
| --- | --- | --- | --- | --- | --- | ---: | --- |
| 1 | Problem Description | `README.md`; `product-spec.md`; `docs/project-charter.md` | README clearly states the requirements-to-delivery traceability problem, scope, behavior, and limitations. | None found for the documented criterion. | PASS | 2 | Keep README aligned with the working demo. |
| 2 | Product Specification | `product-spec.md`; `openapi.yaml`; `docs/codex-reports/` | Written specification, functional requirements, business rules, and API contract exist. | No public task tracker, acceptance-criteria issue set, or evidence that agents used the tracker was found. | PARTIAL | 1 | Create a public GitHub Project/Issues board with acceptance criteria; link issues, PRs, and agent evidence. |
| 3 | Agent Team Specification | `AGENTS.md`; `docs/codex-reports/` | AGENTS.md identifies Codex use and general development/reporting expectations. | No defined multi-agent roles, responsibilities, handoffs, collaboration workflow, or escalation process. | PARTIAL | 1 | Add a modular agent-team/process document defining roles, inputs/outputs, review gates, and tracker workflow. |
| 4 | Context Management | `AGENTS.md`; `product-spec.md`; `docs/project-charter.md` | AGENTS.md describes the project and points to the product specification and charter. | It does not link a complete modular context package for process, agent team, operations, and ownership. | PARTIAL | 1 | Extend AGENTS.md to point to modular process/team/operations documents after they are created. |
| 5 | Application | `frontend/src/App.tsx`; `backend/app/main.py`; `backend/app/database.py`; `backend/migrations/`; `openapi.yaml` | React frontend calls FastAPI endpoints; backend registers domain routers and persists via PostgreSQL. | No single command starts the frontend, backend, and database together; this audit did not execute an end-to-end smoke test. | PARTIAL | 1 | Add full application Compose topology and a documented, executed end-to-end smoke test. |
| 6 | Testing | `backend/tests/`; `frontend/src/App.test.tsx`; `scripts/test-all.ps1`; `docs/codex-reports/adm_8.10.66.md` | Frontend Vitest tests and backend unit/integration tests run through the documented unified runner. The latest verified execution passed 4 frontend tests and 511 backend tests (515 total, 0 failed). | Broaden frontend workflow coverage beyond the initial authentication/project path. | PASS | 2 | Retain the fail-closed isolated database preflight and add focused UI coverage for remaining workflows. |
| 7 | Containerization | `compose.yaml`; `compose.test.yaml`; `docker/migration-rehearsal/Dockerfile` | PostgreSQL and isolated test database Compose configurations exist; a migration-rehearsal Dockerfile exists. | No frontend/backend container images or full-system Compose command. | PARTIAL | 1 | Add frontend and backend Dockerfiles plus one full-stack Compose file with health checks and environment templates. |
| 8 | Deployment | `README.md`; `docs/architecture.md`; tracked-file inventory | Repository explicitly states no public deployment evidence. | No reachable public URL, deployment configuration, or clear deployment demo evidence. | MISSING | 0 | Deploy the containerized application and document the public URL and a repeatable demo. |
| 9 | CI/CD | `.github/workflows/` inventory; `README.md` | No workflow files were found. | No pull-request CI, automated deployment, development deployment, or manual production deployment path. | MISSING | 0 | Add PR CI first; then add dev CD and a protected manual production deployment workflow. |
| 10 | Observability | source scan; `docs/architecture.md` | Standard application logging may exist through dependencies, but no correlated telemetry system was evidenced. | No instrumented key journey with correlated structured logs, metrics, traces, collector/storage, or UI. | MISSING | 0 | Instrument one journey with trace ID correlation; provision collector and a viewable telemetry UI while excluding sensitive data. |
| 11 | Alerting on User Impact | source/configuration scan | No alert definition was found. | No user-impact SLO/error alert and no trigger demonstration. | MISSING | 0 | Define and test one alert tied to a failed user journey, such as login or project-load error rate. |
| 12 | On-Call Agent | source/configuration scan; `AGENTS.md` | No responder implementation was found. | No alert receiver, diagnosis workflow, controlled remediation, or evidence of a responder agent. | MISSING | 0 | Implement a scoped responder that consumes the alert, gathers safe diagnostics, proposes/executes an approved remediation, and records evidence. |

## Critical Check Results

| Check | Result | Evidence / limitation |
| --- | --- | --- |
| Entire application starts with one command | NO | `compose.yaml` starts PostgreSQL only; README requires separate backend and frontend commands. |
| Frontend, backend, and database are structurally connected | PARTIAL / NOT EXECUTED | Source wiring exists in `frontend/src/App.tsx`, `backend/app/main.py`, and `backend/app/database.py`; no live end-to-end run occurred in this audit. |
| Unit and integration tests run with one command | YES | `scripts/test-all.ps1` completed with 4 frontend and 511 backend tests passing (515 total, 0 failed). |
| Frontend tests exist | YES | `frontend/src/App.test.tsx` runs through the Vitest script and covers initial authentication/project behavior. |
| Docker Compose starts the entire application | NO | Main Compose configuration has only PostgreSQL. |
| Public deployment exists and is accessible | NO EVIDENCE | Repository documents that it is not publicly deployed. |
| CI runs automatically on pull requests | NO | No GitHub Actions workflow directory/files found. |
| CD supports deployment | NO | No deployment pipeline/configuration found. |
| Metrics, structured logs, and traces are viewable in a UI | NO | No observability stack or UI configuration found. |
| At least one user-impact alert can fire | NO | No alert configuration or trigger evidence found. |
| On-call agent receives, diagnoses, and recovers from an alert | NO | No responder-agent implementation or runbook evidence found. |
| Public tracker with acceptance criteria and agent evidence | NO EVIDENCE | No local link or tracker evidence; remote state was not inspected in this audit. |
| Agent team roles and collaboration procedures documented | NO | AGENTS.md has general instructions but no defined agent team/process. |

## Assessment Notes

- The unified runner result—4 frontend tests plus 511 backend tests passing in 41.78 seconds—is verified execution evidence recorded in `docs/codex-reports/adm_8.10.66.md`. Other historical quality claims in this assessment were not rerun for the original audit.
- The optional OpenAI drafting adapter is an application feature; it does not satisfy the rubric's on-call-agent requirement.
- A passing score requires at least 10 points, but the three peer reviews are mandatory regardless of numeric score.

## Priority Order

1. Establish public tracker evidence, agent-team/process documentation, and complete the three peer reviews. These are low-risk, high-value submission requirements.
2. Deliver and verify a single-command full-stack container runtime and end-to-end smoke path.
3. Extend frontend coverage and ensure PR CI provides repeatable automatic verification.
4. Deploy the containerized app and capture accessible demonstration evidence.
5. Implement one observable user journey, one user-impact alert, and a scoped on-call responder agent.
