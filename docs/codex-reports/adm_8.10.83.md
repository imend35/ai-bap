# ADIM 8.10.83 — Public Deployment Architecture Assessment

## Objective

Assess the fastest safe path to a publicly accessible AI BAP demonstration for
the October 27, 2026 capstone deadline without deploying, changing cloud
infrastructure, or modifying application configuration.

## Files and Configurations Inspected

- `AGENTS.md`
- `compose.yaml`
- `docker/backend/Dockerfile`
- `docker/frontend/Dockerfile`
- `docker/frontend/nginx.conf`
- `docker/backend/initialize_fresh_database.py`
- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/database.py`
- `backend/alembic.ini`
- `frontend/src/App.tsx`
- `.env.example` (variable names only)
- `README.md`
- Current isolated Compose-project status, read only

## Current Architecture and Readiness Findings

- The validated local Compose topology includes PostgreSQL, a one-shot
  migration service, FastAPI, and an Nginx-served React build.
- FastAPI exposes `GET /api/v1/health`, listens on all interfaces in its
  container, and reads database, JWT, and CORS settings from environment
  variables.
- The frontend accepts `VITE_API_BASE_URL`; an empty build-time value uses the
  current same-origin API path. The Nginx configuration proxies `/api/` to the
  Compose-only service hostname `api`.
- The local fresh-database initializer applies Alembic only when the `public`
  schema has no tables. It deliberately skips existing databases, so it is not
  a safe recurring production-migration solution.
- The existing isolated project `ai-bap-rubric-test` remains healthy and was
  only inspected. No Docker resources were changed in this assessment.

## Deployment Options Evaluated

### 1. Render

**Fit:** Strong primary option.

- Render supports Dockerfile-based web services, managed PostgreSQL, private
  service networking, public URLs, custom domains, and managed TLS. Docker
  services can use pre-deploy commands for controlled migrations.
- The backend can deploy from `docker/backend/Dockerfile`. The frontend can be
  deployed as a static site or a separate Docker web service. For the fastest
  path, build the frontend with `VITE_API_BASE_URL` set to the backend's public
  HTTPS URL and configure the backend CORS allowlist to the frontend URL.
- Render requires a public web service to listen on `0.0.0.0` and a configured
  HTTP port. The current backend already uses `0.0.0.0`; the platform `PORT`
  must be set compatibly with the current container command or the command must
  be made port-aware.
- Setup complexity: medium. It needs a Render account, a managed database, two
  services, environment variables, a deliberate migration job, and a demo
  administrator bootstrap.
- Free-tier and low-cost feasibility, quotas, sleep behavior, and managed
  database pricing require confirmation in the current Render account before
  selection.

### 2. Railway

**Fit:** Viable fallback.

- Railway supports custom Dockerfile paths, managed PostgreSQL, private
  networking, public domains, and Compose-to-service guidance.
- It can host separate backend and frontend services built from the existing
  Dockerfiles. A managed PostgreSQL service should replace the Compose `db`
  service; do not expose database public access for the demo.
- As with Render, build the frontend with the public backend URL and set a
  precise backend CORS allowlist. The Compose `depends_on` ordering is not a
  production readiness guarantee and must not be relied on for migrations.
- Setup complexity: medium. Its service decomposition is close to the existing
  Compose design, but environment-variable mapping, public domains, migration
  execution, and account pricing need dashboard confirmation.
- Current plan pricing, quotas, and trial availability are not asserted here.

### 3. Small VPS with Docker Compose

**Fit:** Technically compatible but higher operational risk.

- This option most closely matches the validated local Compose stack and can
  use the existing backend/frontend images plus a persistent PostgreSQL volume.
- It requires server provisioning, patching, firewall rules, a reverse proxy,
  certificate management, backup/restore planning, monitoring, and a secure
  method for secret delivery. PostgreSQL must remain private to the Docker
  network and must not be published publicly.
- Setup complexity: high under the deadline. A VPS is a reasonable recovery
  option only if managed-platform configuration becomes unavailable and the
  operator is prepared to own HTTPS and operating-system security.
- Provider pricing and available plans require external confirmation.

## Recommended Architecture

### Primary: Render Managed PostgreSQL + Docker Backend + Static Frontend

1. Provision managed PostgreSQL in the same Render region as the backend.
2. Deploy FastAPI as a Docker web service from `docker/backend/Dockerfile`.
3. Deploy the React build as a Render static site, or as a separate Docker web
   service if preserving the existing Nginx image is preferred.
4. Build the frontend with `VITE_API_BASE_URL` set to the backend public HTTPS
   URL. This bypasses the Compose-only `api` hostname in the static Nginx
   configuration without changing frontend application logic.
5. Set `CORS_ORIGINS` to the exact frontend HTTPS origin. Do not use a wildcard.
6. Keep PostgreSQL private; expose only frontend and backend HTTPS services.
7. Run Alembic once in a controlled pre-deploy or one-off job against the
   managed database, then deploy the backend after success.

This approach minimizes application changes, provides platform TLS and public
URLs, retains managed database separation, and avoids operating a public VPS.

### Fallback: Railway Managed PostgreSQL + Separate Docker Services

Use a Railway managed PostgreSQL service and two Docker services from the
existing backend/frontend Dockerfiles. Apply the same build-time frontend API
URL, exact CORS allowlist, private-database, and controlled-migration rules.

## Required Changes and Platform Configuration

### Required Repository Changes

1. Add a reproducible deployment descriptor, preferably `render.yaml`, after
   platform choice is approved.
2. Add an explicit production migration command or narrowly scoped migration
   job. Do not use `initialize_fresh_database.py` for recurring migrations.
3. Make the backend runtime port configurable from the platform `PORT`, or
   explicitly configure the platform to route to the existing container port.
4. Add deployment documentation covering configuration, migration order,
   rollback, public URLs, and post-deploy smoke checks.

### Required Platform Variables (Names Only)

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `JWT_SECRET_KEY`
- `CORS_ORIGINS`
- `VITE_API_BASE_URL` (frontend build-time value)
- `PORT` (where required by the selected platform)
- `OPENAI_API_KEY` and `OPENAI_MODEL` only if optional AI drafting is enabled

### Migration and Initialization Strategy

- Create a fresh managed database.
- Run `alembic upgrade head` in one controlled platform job or pre-deploy step.
- Record the applied revision and job result.
- Deploy the API only after migration success.
- For future revisions, rerun the controlled migration step; do not reset the
  database, reuse the local fresh-database initializer, or rely on startup
  races.

### Health Checks and Demo Smoke Test

- Backend health check: `/api/v1/health`.
- Frontend: public HTTPS root returns the React application.
- Browser request: frontend login and authenticated API request succeed.
- Create only disposable demonstration data; verify one project workflow.
- Confirm database has no public endpoint and CORS rejects unapproved origins.

### Rollback and Recovery

- Keep the prior successful Docker image/deploy available for rollback.
- Never roll back application code across schema changes without an approved
  migration compatibility review.
- Confirm managed PostgreSQL backup, restore, and retention capabilities in the
  selected platform plan before public use.

## Security Considerations

- Store all production values in platform secret management; never commit `.env`
  files, database URLs, passwords, JWT keys, or provider keys.
- Use a high-entropy production `JWT_SECRET_KEY` and rotate it through an
  approved maintenance procedure.
- Restrict `CORS_ORIGINS` to the deployed frontend HTTPS origin.
- Keep PostgreSQL on a private network; do not publish a database port.
- Enable platform HTTPS and avoid serving credentials over plain HTTP.
- Keep optional AI provider credentials absent unless the feature is required
  for the demonstration.

## Validation Findings

- The isolated full-stack Compose runtime was previously verified: PostgreSQL,
  migrations, FastAPI, Nginx, direct backend health, frontend HTTP, and the
  same-origin proxy all succeeded.
- Docker runtime evidence validates local container compatibility, not public
  hosting, TLS, managed-database connectivity, or production migrations.
- Official platform documentation confirms relevant Docker, managed database,
  TLS, custom-domain, and private-network capabilities. Pricing and plan limits
  remain external confirmation items.

## Blockers

### Mandatory Before Public Demo

1. Human selection and account access for Render or Railway.
2. A managed PostgreSQL instance and secure platform-secret configuration.
3. A controlled production migration procedure.
4. Public backend/frontend URLs with exact CORS configuration.
5. A secure administrator bootstrap and browser smoke test.

### Optional Improvements

- Custom domain.
- Deployment automation/CD.
- Observability, alerting, backups beyond the selected managed-plan baseline,
  and a rollback drill.

## Rubric Relevance

A managed-platform deployment can provide the required public application and
deployment evidence. It does not by itself satisfy continuous deployment,
observability, alerting, or on-call-agent criteria.

## Final Recommendation

Choose **Render** as the fastest safe path, with managed PostgreSQL, a Docker
FastAPI web service, and a static frontend configured with the backend public
HTTPS URL. Use **Railway** as the fallback if its account setup or current plan
is more accessible. Avoid a VPS unless managed platforms are unavailable,
because server, HTTPS, firewall, backup, and patch-management work increases
deadline risk.

## Source References

- [Render Docker deployment](https://render.com/docs/docker)
- [Render web-service ports and HTTPS](https://render.com/docs/web-services)
- [Render managed PostgreSQL](https://render.com/docs/postgresql)
- [Railway Dockerfiles](https://docs.railway.com/builds/dockerfiles)
- [Railway Docker Compose deployment guide](https://docs.railway.com/guides/docker-compose)
- [Railway PostgreSQL](https://docs.railway.com/databases/postgresql)
- [DigitalOcean firewall guidance](https://docs.digitalocean.com/products/networking/firewalls/getting-started/quickstart/)
