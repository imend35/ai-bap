# AI BAP — AI-Powered Business Analysis Platform

AI BAP is a full-stack business-analysis workspace that I built to connect
projects, requirements, user stories, delivery tasks, and sprints in one
traceable workflow. It uses a React frontend, a FastAPI backend, PostgreSQL,
SQLAlchemy, Alembic, and an OpenAPI contract.

The application is under active development and is available as a short-term
public demonstration on Render Free. The demo is for evaluation with synthetic
data, not a production service. GitHub Actions validates the frontend and
backend on pushes and pull requests to `main`; deployments are manually
controlled and continuous deployment is not configured.

## Live Demo

- **Frontend:** [ai-bap-frontend-free.onrender.com](https://ai-bap-frontend-free.onrender.com)
- **API health:** [ai-bap-api-free.onrender.com/api/v1/health](https://ai-bap-api-free.onrender.com/api/v1/health)
- **Repository:** [github.com/imend35/ai-bap](https://github.com/imend35/ai-bap)

The demo uses a Render Free static frontend, FastAPI web service, and
PostgreSQL database. Free web services spin down after 15 minutes without
incoming HTTP or WebSocket traffic; the first request after inactivity may
take about a minute while the service starts. See [Render's current Free
instance limitations](https://render.com/docs/free) before evaluating.

## Reviewer Quick Start

1. Open the [live frontend](https://ai-bap-frontend-free.onrender.com). If the
   API has been idle, allow time for its Render Free instance to wake.
2. Check the [API health endpoint](https://ai-bap-api-free.onrender.com/api/v1/health).
3. Sign in only with evaluator credentials supplied privately by the project
   owner. No public demo credentials are published here. Public registration is
   disabled; do not assume anonymous access or attempt to create an account.
4. Use synthetic project and requirement data only. From an authorized session,
   review the project dashboard, requirements, story workflow, tasks, sprints,
   and traceability views available to that account's role.
5. In the inspected local implementation, the backend denies live AI-generation
   requests for the exact identities `banlyst@example.com` and
   `reviwer@example.com`, and the frontend disables their Generate control.
   Regression tests for this behavior are present in the repository, but their
   execution is not verified here, and the restriction's deployment and
   enforcement on Render have not been verified. Do not assume these accounts
   are active or usable. Business Analysts can still create User Stories
   manually, and Reviewers can review and approve or reject them. Both roles can
   inspect saved stories and acceptance criteria. The current data model does
   not record reliable AI-generation provenance, so particular saved stories
   are not identified as AI-generated. Authorized non-demo Business Analysts
   and administrators retain the AI-generation workflow when the configured
   provider is reachable; generated content is an unsaved draft that must be
   reviewed before saving.

**Complete User Guide:** For detailed instructions covering every screen, button, role, and end-to-end workflow, see the [AI BAP User Guide](docs/USER_GUIDE.md).

## Project Overview

I use AI BAP to turn business requirements into reviewable delivery work while
preserving a visible path from requirement to user story to task. The API and
UI support project-level dashboard and traceability views, as well as a
controlled user-story review workflow.

The product scope is defined in [product-spec.md](product-spec.md). The
implementation contract is [openapi.yaml](openapi.yaml).

## Problem Statement and Solution

Business requirements often live separately from delivery tasks, making review,
approval, and traceability difficult. AI BAP provides a structured workspace
for capturing requirements, creating and reviewing user stories, assigning
tasks and sprints, and inspecting the resulting delivery chain.

An optional OpenAI-backed adapter generates a user-story draft from a
requirement without persisting it. The reviewer must inspect and edit the draft,
then explicitly confirm human review before saving. The saved story begins in
Draft status; approval or rejection is a separate protected review action.

## Implemented Features

- JWT registration, login, and current-user profile endpoints.
- Role-protected administrator user management.
- Project creation, listing, detail, update, archive, and restore operations.
- Archive-aware project lists, dashboards, and traceability reads.
- Read-only protection for archived projects and their related write
  operations; projects must be restored before work can change again.
- Requirement, user-story, task, and sprint CRUD workflows.
- User-story review, approval, rejection, and immutable approval-audit
  identity snapshots.
- Requirement → user story → task traceability and project dashboard counts.
- PostgreSQL-backed immutable readable record numbers and creator metadata.
- OpenAPI contract-alignment tests and guarded isolated PostgreSQL test
  database support.

## Authentication, Authorization, and User Roles

The backend issues signed JWT bearer tokens after successful login. Passwords
are hashed with Argon2id; password hashes and JWT signing secrets are never
returned by the API.

The implemented roles are:

- `admin`: manages administrator accounts and can archive or restore projects.
- `business_analyst`: creates and updates business-analysis and delivery
  content where the route permits it.
- `reviewer`: reads authorized project data and performs user-story approval
  and rejection decisions.

The backend enforces route-level permissions with `require_roles`; UI controls
are not the security boundary. See the operation-specific requirements in
[openapi.yaml](openapi.yaml).

## Architecture and Technology Stack

| Area | Implementation |
| --- | --- |
| Frontend | React 19, TypeScript, Vite |
| Backend | Python 3.13+, FastAPI, Pydantic Settings |
| Persistence | PostgreSQL 16, SQLAlchemy 2.x |
| Schema migrations | Alembic |
| Authentication | JWT with PyJWT; Argon2id password hashing |
| API contract | OpenAPI 3.1 in `openapi.yaml` |
| Backend quality | Pytest, HTTPX, Ruff |
| Frontend quality | Vitest, React Testing Library, TypeScript build, Oxlint |
| Optional AI integration | OpenAI Python SDK, configured by environment |

The main [compose.yaml](compose.yaml) runs the frontend, FastAPI backend, and
PostgreSQL as one local Compose application. The direct backend and Vite
commands below remain useful for focused development.

## Repository Structure

```text
ai-bap/
├── backend/
│   ├── app/                 # FastAPI routes, models, schemas, and services
│   ├── migrations/          # Alembic environment and revisions
│   ├── scripts/             # Guarded database and bootstrap helpers
│   ├── tests/               # Unit and API integration tests
│   └── pyproject.toml
├── frontend/
│   ├── src/                 # React application
│   └── package.json
├── docker/                  # Test and migration-rehearsal support files
├── docs/                    # Architecture and operational documentation
├── compose.yaml             # Full local frontend, API, and PostgreSQL stack
├── compose.test.yaml        # Isolated PostgreSQL test service
├── openapi.yaml             # Checked-in API contract
└── product-spec.md          # Product scope and acceptance criteria
```

## Prerequisites

- Python 3.13 or later
- [uv](https://docs.astral.sh/uv/)
- Node.js and npm
- Docker Desktop with Docker Compose, for the complete local stack

## Environment Configuration

Copy the root example file before starting the development database:

```powershell
Copy-Item .env.example .env
```

Set non-placeholder local database values in `.env`, then add the required
backend JWT setting. Use a securely generated value; never commit `.env`.

```dotenv
JWT_SECRET_KEY=<a-local-secret-of-at-least-32-characters>
```

The backend reads PostgreSQL settings and `JWT_SECRET_KEY` from the root
`.env`. The optional AI generator additionally reads `OPENAI_API_KEY` and
optionally `OPENAI_MODEL`; without an API key, AI draft generation returns a
controlled configuration error. The frontend defaults to
`http://127.0.0.1:8000` and can be pointed elsewhere with
`VITE_API_BASE_URL`.

## Full-Stack Docker Compose Setup

Copy the safe example before the first local startup and replace its placeholder
database password and JWT signing key. Never commit `.env`.

```powershell
Copy-Item .env.example .env
docker compose up --build -d
```

The command starts four local services: PostgreSQL (`db`), the one-shot
fresh-database initializer (`migrate`), FastAPI (`api`), and nginx-hosted React
assets (`frontend`). Open `http://localhost:8080`; the API health endpoint is
available at `http://127.0.0.1:8000/api/v1/health`. Browser `/api/...` requests
are proxied by nginx to FastAPI, so the containerized UI uses same-origin API
routing.

The full stack was also verified in a separate disposable Compose project with
isolated loopback ports and a new PostgreSQL volume. That evidence is local
runtime verification, not a public deployment; see
[the Docker runtime report](docs/codex-reports/adm_8.10.82.md).

All published ports bind to loopback only. PostgreSQL defaults to host port
`5433`, FastAPI to `8000`, and the frontend to `8080`; change only the
non-secret port values in `.env` when needed.

### Fresh database initialization safety

The `migrate` service applies Alembic only when the Compose database has an
empty `public` schema and `AI_BAP_INITIALIZE_FRESH_DATABASE=true`. If it sees
any existing public table, it exits without applying a migration. This prevents
the Compose startup path from upgrading an existing persistent database.

For an existing database, review its target and run the documented Alembic
procedure manually. Do not use the development database for automated
integration tests; use the isolated test procedure below instead.

### Health checks and shutdown

```powershell
docker compose ps
Invoke-WebRequest http://127.0.0.1:8000/api/v1/health
docker compose down
```

`docker compose down` stops the stack but retains the named PostgreSQL volume.
Do not add `--volumes` unless intentionally discarding a disposable local
database.

### Troubleshooting

- If `migrate` reports an existing database, it intentionally made no schema
  change. Review the target and use the manual Alembic workflow.
- If a loopback port is busy, set `POSTGRES_PORT`, `API_PORT`, or
  `FRONTEND_PORT` to an unused local port in `.env` and restart.
- Use `docker compose logs migrate`, `docker compose logs api`, or
  `docker compose logs frontend` for non-sensitive diagnostics. Never copy
  credentials into issue comments or reports.

## Alembic Database Migrations

Install the backend environment, then inspect and apply migrations from the
`backend` directory:

```powershell
Set-Location backend
uv sync --extra dev
uv run alembic current
uv run alembic upgrade head
```

The current migration chain includes the record-number formatting correction
revision `c8d9e0f1a2b3`. Alembic obtains its connection configuration from the
application settings, so `alembic upgrade head` must be run only after the
development database target has been verified.

### Isolated test database

Database-backed tests use a separate Compose project, database, volume, port,
and test-only credentials. Follow
[docs/isolated-test-database.md](docs/isolated-test-database.md) exactly.
That procedure sets fail-closed environment checks before the test suite or
guarded test Alembic wrapper is used:

```powershell
Set-Location backend
uv run python scripts/run_isolated_test_alembic.py upgrade head
```

This command is for the confirmed isolated test target only; it is not a
replacement for development-database migrations.

## Running the FastAPI Backend

With the development database migrated and the backend environment installed:

```powershell
Set-Location backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend exposes its health endpoint at
`http://127.0.0.1:8000/api/v1/health`.

## Running the React Frontend

In a second terminal:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Vite prints the local frontend URL, normally `http://localhost:5173`. The
default backend CORS configuration permits the standard Vite localhost origins.

## API Documentation

The checked-in [openapi.yaml](openapi.yaml) is the API contract. When the
backend is running, FastAPI also provides interactive documentation at
`http://127.0.0.1:8000/docs` and the runtime schema at
`http://127.0.0.1:8000/openapi.json`.

Implemented API groups include health, authentication, administrator users,
projects, requirements, user stories, user-story approvals/audit history,
tasks, and sprints. Consult the contract for request bodies, responses,
authorization requirements, pagination, and error responses.

## Testing and Code Quality

Backend database tests require the isolated environment described above. From
`backend`, the verification commands are:

```powershell
uv run --no-sync pytest -q --tb=short
uv run --no-sync ruff check app tests migrations/versions
```

Frontend verification commands, from `frontend`, are:

```powershell
npm run build
npm run lint
```

A local backend verification recorded **589 tests passed**. This is local
execution evidence, not a claim about the latest GitHub Actions result; check
the workflow run and its head commit before attributing a CI result to a
particular revision. Frontend Vitest tests use mocked API responses, and the
TypeScript/Vite production build and Oxlint are part of the frontend checks.
A previously recorded lint run reported 16 warnings and no errors; consult the
current run output for the present warning count.

### Unified test execution

From the repository root, run:

```powershell
.\scripts\test-all.ps1
```

The runner executes the mocked frontend Vitest suite first. It then runs
backend Pytest only when the current shell has the exact isolated PostgreSQL
test configuration described in
[docs/isolated-test-database.md](docs/isolated-test-database.md). If that
explicit setup is unavailable, it reports the backend phase as `SKIPPED` and
exits nonzero rather than using the development database or reporting overall
success. It never starts Docker or runs migrations.

Run frontend tests independently from `frontend`:

```powershell
npm run test -- --run
```

See [docs/testing-strategy.md](docs/testing-strategy.md) for frontend mocking,
backend database safety, runner exit behavior, and current coverage limits.

### Continuous integration

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on pushes and pull
requests targeting `main`. The frontend job runs `npm ci`, Vitest, the Vite
production build, and Oxlint. The backend job creates an ephemeral PostgreSQL
16 service mapped to the exact tuple required by the fail-closed test guard,
applies Alembic through the guarded test wrapper, then runs Pytest and Ruff.
It uses only synthetic CI credentials and never targets a development database.

For remote results, inspect the [GitHub Actions workflow runs](https://github.com/imend35/ai-bap/actions)
and confirm that each run's head SHA matches the revision being evaluated.
Historical successful runs do not establish the status of a newer commit. The
local 589-test result above is not presented as a GitHub Actions result.

## Render Free Deployment

The live demo uses the separate [`render.free.yaml`](render.free.yaml)
configuration for managed PostgreSQL, a Docker-based FastAPI web service, and
a static frontend. Automatic deployment triggers are disabled; a repository
change should not be interpreted as an automatic demo update. The paid
[`render.yaml`](render.yaml) is a separate configuration. See the
[Render Free deployment guide](docs/deployment-render-free.md) for configuration,
migration safeguards, CORS, registration policy, administrator bootstrap,
validation, and recovery limits.

## Security Considerations

- Keep `.env`, test-only passwords, JWT secrets, API keys, private keys, and
  database backups out of version control.
- Use only the isolated test database procedure for database-backed tests.
- Use the interactive administrator bootstrap process described in
  [docs/bootstrap-admin.md](docs/bootstrap-admin.md) rather than passing
  administrator passwords on a command line.
- The backend validates external input, hashes passwords, checks JWT identity,
  enforces server-side roles, and protects archived projects from writes.
- Public self-registration is disabled in the Render Free configuration;
  protected features require authorized login. Never place evaluator
  credentials in this README, the frontend bundle, or public URLs.
- Treat user requirements and AI output as untrusted input. Generated stories
  are not saved until a human has reviewed and explicitly confirmed them.

## Evaluation Evidence

- [Agent team specification](docs/agent-team.md) and
  [agent workflow](docs/agent-workflow.md)
- [Product specification](product-spec.md),
  [project charter](docs/project-charter.md), and
  [architecture](docs/architecture.md)
- [Task tracker plan](docs/github-issues-plan.md) and
  [GitHub Issue #2](https://github.com/imend35/ai-bap/issues/2)
- [Agent development instructions](AGENTS.md)
- [Backend tests](backend/tests/) and the
  [frontend test suite](frontend/src/App.test.tsx)
- [API contract](openapi.yaml)
- Docker configuration: [full-stack Compose](compose.yaml),
  [isolated test Compose](compose.test.yaml), and
  [disposable regression Compose](compose.regression-test.yaml)
- Render configuration and instructions:
  [Free Blueprint](render.free.yaml) and
  [deployment guide](docs/deployment-render-free.md)
- [GitHub Actions CI workflow](.github/workflows/ci.yml)

## Known Limitations

- The Render Free demo is intended for evaluation, not production use. Free
  services may restart or spin down, and the associated free database has
  provider-specific retention limits; see the deployment guide and current
  Render documentation.
- CI provides validation; automatic continuous deployment is not configured.
- Correlated end-to-end observability, user-impact alerting, and an on-call
  responder agent are not established and are not claimed.
- A prior Oxlint run reported 16 warnings and no errors. Review current output
  before treating that count as current.
- Full-stack Compose has local runtime evidence, but that is not production
  deployment evidence.
- The optional AI draft generator depends on an explicitly configured OpenAI
  API key and external provider availability.

## Future Improvements

- Expand frontend component and workflow tests.
- Add and maintain deployment-specific smoke tests; any continuous-deployment
  strategy requires separate review and evidence.
- Refactor frontend loading state with regression coverage to address lint
  warnings after confirming the current findings.
- Improve correlated observability, user-impact alerting, and on-call
  procedures before making operational-readiness claims.
