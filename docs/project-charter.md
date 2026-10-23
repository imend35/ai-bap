# AI BAP — Project Charter

**Project name:** AI BAP
**Full name:** AI-Powered Business Analysis Platform
**Version:** 1.0
**Status:** Active development
**Project type:** AI-assisted full-stack web application
**Tagline:** From Requirements to Intelligent Delivery

## 1. Project Overview

I am developing AI BAP as a traceable workspace for business-analysis and
delivery work. It connects projects, requirements, user stories, tasks, and
sprints while preserving the relationship between the original need and its
delivery work.

The current implementation includes a React and TypeScript frontend, a FastAPI
backend, PostgreSQL persistence, Alembic migrations, a checked-in OpenAPI
contract, JWT authentication, and role-based authorization.

## 2. Problem Statement

Business requirements are often scattered across documents and delivery tools.
That separation can make approval history, traceability, and delivery progress
difficult to inspect. I am addressing this problem with a single workspace for
structured requirements, reviewable user stories, delivery planning, and
project-level visibility.

## 3. Product Vision

My vision remains a practical, traceable workspace that supports the path from
an initial business requirement to an actionable delivery item. AI can assist
with drafting, but people remain responsible for reviewing and approving
content. I do not treat AI output as automatically approved work.

## 4. Objectives

### Completed or implemented

1. I implemented a working React/TypeScript frontend, FastAPI backend, and
   PostgreSQL persistence layer.
2. I maintain a versioned OpenAPI contract for the implemented API.
3. I implemented JWT authentication, Argon2id password hashing, and server-side
   role authorization for `admin`, `business_analyst`, and `reviewer` users.
4. I implemented projects, requirements, user stories, tasks, sprints,
   dashboards, and requirement-to-story-to-task traceability.
5. I implemented user-story review, approval, rejection, and audit history.
6. I implemented administrator-only project archive and restore actions,
   archive-aware reads, and read-only protection for archived project work.
7. I added PostgreSQL migrations, backend tests, isolated-test-database guards,
   and backend/frontend quality checks.

### Planned enhancements

1. Add frontend automated tests and CI quality gates.
2. Deliver a complete containerized frontend/backend runtime and deployment
   workflow; the current main Compose file starts PostgreSQL only.
3. Expand observability and operational evidence.
4. Continue documenting reusable AI-development and agent-extension evidence.

## 5. Target Users

- Business Analysts who capture and refine requirements.
- Product Owners who prioritize work and assess value.
- Scrum Masters who coordinate sprint delivery.
- Developers who implement traceable tasks.
- Reviewers and QA Engineers who approve stories and inspect acceptance
  criteria, audit history, and traceability.

## 6. Current Scope

### Implemented

- Authenticated user registration, login, profile retrieval, and administrator
  user management.
- Role-protected project, requirement, user-story, task, and sprint workflows.
- Project archive/restore lifecycle with preserved project status, archive actor
  metadata, idempotent actions, and archived-project write protection.
- Paginated project, dashboard, and traceability reads, including archived
  project visibility for authorized readers.
- User-story approval/rejection decisions and persisted audit records.
- Optional OpenAI-backed user-story draft generation when an API key is
  configured; generated drafts still require human review.

### Out of scope or not yet evidenced

- Public deployment.
- CI/CD workflows.
- Frontend automated tests.
- Enterprise SSO, Jira synchronization, real-time collaboration, and advanced
  capacity forecasting.

## 7. Delivery Principles

- **Specification and contract alignment:** I maintain product requirements and
  the OpenAPI contract alongside implementation.
- **Human control:** A reviewer explicitly approves or rejects user stories.
- **Evidence-based reporting:** I distinguish verified behavior from planned
  work and do not present build, test, or deployment results without evidence.
- **Security by design:** I use environment-based secrets, server-side role
  checks, validated input, and an isolated test database procedure.
- **Reproducibility:** I document development setup, migrations, and
  verification commands in the root README and operational documents.

## 8. Technology Stack

| Area | Current implementation |
| --- | --- |
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI, Pydantic Settings |
| Database | PostgreSQL, SQLAlchemy, Alembic |
| API contract | OpenAPI 3.1 |
| Backend tests | Pytest and HTTPX |
| Backend linting | Ruff |
| Frontend quality | Vitest, React Testing Library, TypeScript/Vite build, and Oxlint |
| Authentication | JWT and Argon2id password hashing |
| Containers | Full-stack local Docker Compose and isolated test database configuration |
| AI drafting | Optional OpenAI SDK integration configured by environment |

Frontend automated tests and GitHub Actions CI are implemented. The
push-triggered CI run for commit `1e4333738947f131816901b9fdb71e4fff61d4f2`
and the pull-request-triggered CI run for commit
`d88973895dced732e6aa7f00e4da5847ed0ba3d4` completed successfully. The
full-stack Compose configuration exists, but its runtime has not yet been
verified. Continuous deployment and public deployment are not implemented.

## 9. Current Acceptance Position

The current codebase has documented backend test and Ruff success, and a
passing frontend production build. Oxlint has no errors but retains 16 warnings
that require a separately scoped frontend state-management refactor. I will
consider the project ready for final review only after the submission artifacts,
documentation, and remaining limitations are reviewed together.

## 10. Risks and Mitigations

| Risk | Current mitigation |
| --- | --- |
| Unauthorized writes | JWT authentication and route-level role checks protect API operations. |
| Archived historical data changes | Archive-aware service checks reject related mutations until restore. |
| Test data reaches development data | The isolated PostgreSQL test procedure validates a separate database target before tests run. |
| Secrets leak into source control | `.env` and common secret files are ignored; documentation uses placeholders only. |
| External AI availability | Draft generation is optional and returns a controlled error when no API key is configured. |
| Incomplete delivery automation | CI is verified for push and pull-request runs; continuous deployment, public deployment, and full-stack Compose runtime verification remain limitations. |

## 11. Deliverables

I maintain the product specification, architecture document, README, OpenAPI
contract, backend and frontend source, Alembic migrations, backend tests,
Docker configuration, and operational guidance in this repository. Implemented
frontend tests and CI are documented as completed deliverables. Deployment,
continuous delivery, and agent-extension artifacts are not presented as
completed deliverables.

## 12. Next Step

My next priority is final submission preparation: review the complete working
tree, retain only intended artifacts, verify the isolated full-stack Compose
runtime, and validate the documented setup from a clean environment.
