# AI BAP — Project Charter

**Project name:** AI BAP  
**Full name:** AI-Powered Business Analysis Platform  
**Version:** 1.0 (Draft)  
**Date:** October 14, 2026  
**Project type:** AI-assisted full-stack web application  
**Tagline:** From Requirements to Intelligent Delivery

## 1. Project Overview

I am developing AI BAP to help business analysts and software delivery teams manage requirements, transform them into structured user stories, and track their implementation through an integrated workflow. I intend to combine my business analysis experience with AI-assisted software development, API design, testing, and DevOps practices.

## 2. Problem Statement

Business requirements are often scattered across documents and task-management tools. Incomplete acceptance criteria and disconnected delivery tasks can make traceability and collaboration difficult. I want to provide a single workspace that helps teams structure requirements, review AI-generated drafts, and connect requirements to stories and tasks.

## 3. Product Vision

I envision AI BAP as a practical, traceable workspace that supports the path from an initial business requirement to an actionable, testable delivery item. AI will assist with drafting, while people remain responsible for reviewing and approving requirements and stories.

## 4. Objectives

1. I will build a working full-stack application with a React and TypeScript frontend, a FastAPI backend, and persistent storage.
2. I will document the product requirements and define an OpenAPI contract before implementing dependent functionality.
3. I will implement requirements, user stories, acceptance criteria, tasks, and sprint workflows.
4. I will add AI-assisted user story drafting with explicit human approval.
5. I will provide traceability from requirements to stories and tasks.
6. I will test, containerize, and deploy the application and document how to reproduce it.
7. I will document my AI-assisted development process, security reviews, and operational checks.
8. I will implement and document an agent extension pack aligned with the course project criteria.

## 5. Target Users

- Business Analysts who structure and validate requirements.
- Product Owners who prioritize stories and define value.
- Scrum Masters who coordinate sprint execution.
- Developers who implement traceable tasks.
- QA Engineers who review acceptance criteria and testability.

## 6. MVP Scope

**In scope:** Project management; requirement creation and editing; AI-assisted user story drafts; acceptance criteria; human review and approval; story and task management; basic sprint planning; requirement-to-story-to-task traceability; summary dashboard; AI generation audit history.

**Out of scope for the MVP:** Jira synchronization; enterprise SSO; real-time collaborative editing; advanced capacity forecasting; autonomous production code changes; complex organization-wide permissions.

## 7. Delivery Principles

- **Specification first:** I will describe behavior and acceptance criteria before implementation.
- **Human in control:** AI-generated content will remain a draft until I explicitly approve it.
- **Evidence-based reporting:** I will distinguish planned functionality from tested and deployed functionality.
- **Security by design:** I will protect credentials, validate inputs, and limit agent permissions.
- **Reproducibility:** I will document setup, tests, deployment, and environment configuration.

## 8. Proposed Technology Stack

| Area | Proposed technology |
| --- | --- |
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI |
| Database | PostgreSQL, SQLAlchemy, Alembic |
| API contract | OpenAPI 3.x |
| Backend tests | Pytest, HTTPX |
| Frontend tests | Vitest |
| Containers | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| AI development assistant | Codex CLI |
| Observability | OpenTelemetry; monitoring stack to be finalized |
| Security | Static analysis, dependency scanning, secret hygiene |

These are design choices, not claims that the components are already implemented.

## 9. Success Criteria

I will consider the MVP ready for final review when:

- A reviewer can create a project and a requirement, request an AI-generated story draft, review it, and approve or reject it.
- An approved story can be linked to tasks and a sprint, with traceability visible in the UI.
- Critical automated tests pass and the API implementation is checked against its contract.
- The full local application can be started using documented Docker Compose commands.
- A working deployment or verifiable deployment evidence is available.
- CI runs tests, and the deployment workflow is documented and verified.
- AI development records, agent extensions, security findings, and operational evidence are included in the repository.
- Setup, test, deployment, and review instructions are complete enough for a peer reviewer to reproduce the project.

My target is to satisfy every applicable item in the current 2026 draft rubric. I understand that the course requirements and scoring may change.

## 10. Risks and Mitigations

| Risk | My mitigation |
| --- | --- |
| Scope becomes too large | I will prioritize a vertical end-to-end MVP before enhancements. |
| AI produces incorrect or unsupported details | I will require human review, preserve the source requirement, and record generation status. |
| LLM provider is unavailable or costly | I will use a configurable provider and deterministic test doubles. |
| Secrets or private data leak | I will use environment variables, sample data, and security checks. |
| Deployment differs from local behavior | I will use containers, environment-specific configuration, and deployment smoke tests. |
| Course rubric changes | I will recheck the official requirements before final submission. |

## 11. Deliverables

I plan to deliver a public source repository containing the product specification, project instructions, frontend and backend code, OpenAPI contract, database migrations, automated tests, Docker configuration, CI/CD workflows, agent extension pack, security and operations evidence, and complete setup and deployment documentation.

## 12. Current Status and Next Step

**Status:** Planning — Project Charter v1.0 draft.

**Next step:** I will write `product-spec.md`, define measurable acceptance criteria, and then initialize the repository and implementation skeleton.
