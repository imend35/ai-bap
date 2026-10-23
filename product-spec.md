# AI BAP — Product Specification

**Product:** AI BAP — AI-Powered Business Analysis Platform
**Version:** 1.0
**Status:** Implemented MVP with documented limitations

## 1. Product Vision

I am building AI BAP to help business-analysis and delivery teams transform
business requirements into structured, reviewable user stories and traceable
tasks. The product preserves human responsibility for review and approval,
including when an optional AI draft generator is used.

## 2. Problem Statement

Requirements, review decisions, and delivery tasks are often disconnected. AI
BAP provides one authenticated workspace for recording requirements, managing
their downstream work, reviewing user stories, and inspecting dashboard and
traceability data.

## 3. Users, Roles, and Access Model

The implemented application has authenticated users and the following roles:

- **Administrator (`admin`):** administers user accounts and performs project
  archive and restore operations. Administrators also have access to other
  authorized business workflows.
- **Business Analyst (`business_analyst`):** creates and updates permitted
  project, requirement, user-story, task, and sprint content.
- **Reviewer (`reviewer`):** reads authorized project data and approves or
  rejects user stories in review.

Permissions are enforced in the backend with JWT identity and route-level role
checks. The OpenAPI contract is the authoritative operation-by-operation
reference.

## 4. Functional Requirements

### FR-001 — Project Management

Authorized users can create, list, view, and update projects according to their
role. Administrators can archive and restore a project.

- Default project lists return active projects; `archived=true` returns archived
  projects with filtering applied before totals and pagination.
- Archive and restore actions are idempotent and preserve the project workflow
  status.
- Archived projects remain readable to authorized users, including project
  dashboard and traceability reads.
- An archived project is read-only. Project updates and related requirement,
  user-story, task, sprint, approval/rejection, and AI-draft mutations are
  rejected until the project is restored.

### FR-002 — Requirement Management

Authorized users can create, list, view, and update requirements belonging to a
project. Requirement records include validated title, description, priority,
status, a stable readable record number, creator metadata, and timestamps.

### FR-003 — Optional AI-Assisted Story Drafting

Authorized users can request a user-story draft for a requirement through the
implemented generation endpoint. The backend has an OpenAI SDK adapter that
requires an explicitly configured API key and validates the returned JSON
shape. Without configuration or on provider failure, it returns a controlled
error and does not modify stored requirements.

The application does not treat generated content as approved automatically. A
human must review and explicitly submit, approve, or reject user-story work.

### FR-004 — User Story Management and Review

Authorized users can create, list, view, and update user stories linked to a
requirement. User stories move through the implemented draft, in-review,
approved, and rejected states.

Administrators and reviewers can approve or reject only stories in review. The
application persists an audit record for each decision, including immutable
actor and story identity snapshots for historical continuity.

### FR-005 — Task Management

Authorized users can create, list, view, and update tasks linked to user
stories. Implemented task states are To Do, In Progress, In Review, and Done.
Tasks may be assigned to a sprint where permitted by the API validation rules.

### FR-006 — Sprint Management

Authorized users can create, list, view, and update project sprints. Sprints
have validated start and end dates and the implemented planned, active,
completed, and cancelled statuses.

### FR-007 — Project Dashboard

Authorized users can retrieve project dashboard counts for requirements,
approved user stories, tasks by status, and active sprints. Values are derived
from persisted records.

### FR-008 — Traceability

Authorized users can retrieve a paginated Requirement → User Story → Task
hierarchy for a project. This provides a read-only traceability view of the
implemented relationships.

### FR-009 — User-Story Decision Audit

Authorized readers can retrieve approval and rejection audit history for a user
story. This requirement documents the implemented decision-audit endpoint; it
does not claim a separately persisted external AI-provider audit log.

## 5. Core User Journeys

### US-001 — Capture a Requirement

As a Business Analyst, I create a project and capture a validated requirement
so that the source business need has a structured, traceable record.

### US-002 — Review a User Story

As a Reviewer, I inspect a user story in review and explicitly approve or
reject it so that the decision and actor identity are recorded.

### US-003 — Track Delivery

As a delivery user, I create tasks linked to user stories, update their status,
and assign eligible tasks to sprints so that delivery progress is visible.

### US-004 — Inspect Traceability

As a reviewer or QA user, I inspect the requirement-to-story-to-task hierarchy
and project dashboard so that I can assess delivery coverage and status.

### US-005 — Preserve Archived History

As an Administrator, I archive a project without changing its workflow status.
Authorized users can still read its history, but write operations remain blocked
until I restore it.

## 6. Non-Functional Requirements

- **Security:** The backend validates input, hashes passwords, issues JWTs,
  applies route-level role checks, and keeps secrets in environment variables.
- **Data integrity:** PostgreSQL constraints, foreign keys, migrations,
  archive-state checks, and readable record-number triggers support persistence
  integrity.
- **Testability:** The backend has unit and API integration tests and a guarded
  isolated PostgreSQL test database procedure.
- **Contract consistency:** `openapi.yaml` documents the versioned API contract
  and has focused alignment tests.
- **Reproducibility:** The root README documents local PostgreSQL, Alembic,
  backend, frontend, and isolated-test setup.
- **Accessibility and performance:** These remain areas for continued
  verification; no accessibility audit or performance benchmark is claimed.

## 7. Current Architecture and Delivery Position

The implemented application uses React, TypeScript, and Vite in the frontend;
FastAPI, SQLAlchemy, and Alembic in the backend; and PostgreSQL for persistence.
The repository includes a full-stack Docker Compose configuration for PostgreSQL,
the FastAPI backend, and the React frontend. Its isolated runtime has not yet
been verified end to end.

The repository has backend automated tests and recorded quality-check results.
Frontend automated tests and GitHub Actions CI are implemented. The
push-triggered CI run for commit `1e4333738947f131816901b9fdb71e4fff61d4f2`
and the pull-request-triggered CI run for commit
`d88973895dced732e6aa7f00e4da5847ed0ba3d4` both completed successfully. CI is
configured for pull requests targeting `main`. Continuous deployment and public
deployment are not implemented.

## 8. Data Relationships

- A project has requirements and sprints.
- A requirement has user stories.
- A user story has tasks and review-decision audit records.
- A task may be assigned to a sprint.
- Users create records and, where applicable, perform archive and review
  actions recorded in response and audit data.

## 9. Business Rules

1. Protected API operations require a valid JWT.
2. The backend enforces authorization according to the authenticated role.
3. A user story belongs to one requirement, and a task belongs to one user
   story.
4. Approval and rejection require a user story to be in review.
5. Archived projects remain readable but reject protected mutations until
   restored.
6. Record numbers are database-generated and immutable after assignment.
7. Sprint end dates cannot precede sprint start dates.

## 10. Current Limitations and Future Work

The MVP does not currently provide public deployment evidence, continuous
deployment, enterprise SSO, Jira synchronization, real-time collaboration, or
advanced capacity forecasting. A full application Docker Compose topology is
implemented, but its runtime has not yet been verified. Future work includes
deployment documentation, observability, and further validation of optional AI
provider behavior.
