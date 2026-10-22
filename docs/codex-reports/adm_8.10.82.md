# ADIM 8.10.82 — Docker Runtime Evidence Report

## Step Name and Objective

Create permanent evidence for the successfully completed ADIM 8.10.81 isolated
full-stack Docker Compose runtime test. This report is documentation-only and
does not change the application, Docker resources, or database state.

## Scope

This report records verified results for the disposable Compose project
`ai-bap-rubric-test`. It does not recreate the runtime test or infer results
that were not observed.

## Retrospective: ADIM 8.10.81 — Isolated Full-Stack Docker Runtime Test

### Safety Preconditions

- The test used the unique Compose project `ai-bap-rubric-test`.
- The project used the disposable PostgreSQL volume
  `ai-bap-rubric-test_postgres_data` and network
  `ai-bap-rubric-test_default`.
- Published ports were loopback-only: `55434`, `18000`, and `18080`.
- Existing AI BAP containers and the existing persistent volume remained
  unchanged.
- The isolated stack was left running after verification.

### Build and Startup Evidence

- Backend, migration, and frontend images built successfully.
- PostgreSQL started and became healthy.
- The Alembic migration service completed with exit code `0`.
- FastAPI started and became healthy.
- Frontend Nginx started and became healthy.

### Service Health Results

| Service | Verified result |
| --- | --- |
| PostgreSQL | Healthy |
| Migration service | Completed successfully; exit code `0` |
| FastAPI | Healthy |
| Frontend Nginx | Healthy |

### HTTP Smoke-Test Results

| Endpoint | Verified result |
| --- | --- |
| `http://127.0.0.1:18000/api/v1/health` | HTTP `200` |
| `http://127.0.0.1:18080/` | HTTP `200` |
| `http://127.0.0.1:18080/api/v1/health` | HTTP `200`; same-origin API proxy verified |

### Non-Blocking Execution Note

The initial verbose build attempt was interrupted before Compose created the
service resources. The successful retry built the images and started the
isolated stack. A project-scoped network left by the interrupted attempt was
reused; no non-project Docker resource was affected.

## Resource Isolation Verification

- Compose project: `ai-bap-rubric-test`
- Disposable volume: `ai-bap-rubric-test_postgres_data`
- Project network: `ai-bap-rubric-test_default`
- Host bindings: loopback ports `55434`, `18000`, and `18080`
- Existing AI BAP containers and the existing persistent volume: unchanged

## Commands Executed and Results

For this documentation-only ADIM:

- `Get-Content AGENTS.md`: completed.
- `git status --short`: confirmed that the only pre-existing pending
  modification was `docs/codex-reports/adm_8.10.76.md`.
- `git diff --check`: PASS after this report was created.

The ADIM 8.10.81 Docker commands are not re-run by this report. The build,
startup, health, and HTTP results above are the verified evidence retained from
that completed isolated runtime test.

## Validation and Test Results

- Isolated full-stack build and startup: PASS.
- PostgreSQL, migration, FastAPI, and frontend health: PASS.
- Direct backend health, frontend HTTP, and same-origin proxy smoke tests:
  PASS.
- No automated application test suite was run as part of ADIM 8.10.81.
- No Docker, database, or application operation was run as part of this
  documentation-only ADIM.

## Known Limitations and Remaining Tasks

This evidence does **not** prove:

- Public deployment.
- Production HTTPS.
- Continuous deployment.
- Observability or alerting.
- Authenticated end-to-end application workflows.

The isolated stack remains running and requires a separate explicit approval
before it is stopped or its disposable resources are removed.

## Rubric Relevance

The verified isolated Compose build, migration, health checks, and browser-path
HTTP smoke checks provide evidence for the full-stack local runtime and
containerization portions of the project rubric. They do not provide deployment
or operational-observability evidence.

## Final GO / NO-GO Assessment

**GO** for using the verified local full-stack Compose runtime as evidence for
containerization and as a basis for future public-deployment preparation.

**NO-GO** for claiming public deployment, production readiness, continuous
delivery, observability, alerting, or authenticated end-to-end workflow
verification without separately approved and recorded evidence.

## Recommended Next Step

With separate approval, capture a controlled authenticated application journey
in the isolated stack or proceed with a production-readiness plan covering
deployment, HTTPS, secret management, observability, and rollback.
