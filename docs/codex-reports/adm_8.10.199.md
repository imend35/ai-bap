# ADIM 8.10.199 — Docker Engine Connectivity & Test Environment Preflight

## 1. Step Name and Objective

I diagnosed the Docker Engine access failure observed in ADIM 8.10.198 and identified Ruff availability, without changing Docker, WSL, Python environments, repository code, test configuration, or databases.

## 2. Human Product Owner Authorization

This was read-only diagnostics plus creation of this one report. No service, distribution, container, database, environment setting, dependency, Git/GitHub resource, or cloud resource was changed.

## 3. Summary of Findings

- Docker Desktop is installed and running; the Docker Engine is healthy and reachable from the authorized elevated diagnostic context.
- The earlier failure was an execution-context access limitation: the sandbox could not read the user's Docker CLI configuration and was denied access to the Docker named pipe. It was not evidence that Docker Desktop or the Engine was stopped.
- The active accessible context is `desktop-linux`; the sandbox-visible fallback was `default`, whose endpoint is `npipe:////./pipe/docker_engine`. The Docker CLI configuration directory was inaccessible from the sandbox.
- The dedicated `ai-bap-test` PostgreSQL container already exists, is healthy, and binds only to `127.0.0.1:55432`. It uses the existing persistent volume `ai-bap-test_ai_bap_test_data`. This step did not connect to or modify it.
- Ruff is absent from the system Python and PATH but is present in the existing `backend/.venv` at version 0.17.0. No installation is needed to make the executable available.

## 4. Files and Configuration Inspected

- `AGENTS.md`
- `docs/codex-reports/adm_8.10.197.md`
- `docs/codex-reports/adm_8.10.198.md`
- `compose.test.yaml`
- `docker/compose-test.variables` (non-secret project selector only)
- `docs/isolated-test-database.md`
- `docs/testing-strategy.md`
- `backend/app/test_database_safety.py`
- `backend/tests/conftest.py`
- `backend/tests/test_test_database_safety.py`
- `backend/pyproject.toml`
- Existing Git metadata and read-only Docker, Windows, WSL, Python, and Ruff environment information.

## 5. Windows and Docker CLI Environment

| Check | Observed result |
|---|---|
| Operating system | Microsoft Windows 11 Home Single Language, version `10.0.26200`, build `26200`, 64-bit. |
| Shell | PowerShell `7.6.8`. |
| Docker CLI | `C:\Program Files\Docker\Docker\resources\bin\docker.exe`, version `29.1.3`, Windows/amd64 client. |
| Docker Desktop | Installed; engine reports Docker Desktop `4.57.0 (215387)`. |
| Docker service | `com.docker.service`, Running, Automatic. |
| Docker processes | `Docker Desktop`, `com.docker.backend`, `com.docker.service`, and `com.docker.build` processes were present. |
| Overrides | No `DOCKER_HOST` or `DOCKER_CONTEXT` environment variable was present. No Docker-related environment variable values were printed. |

## 6. Docker Engine Connectivity Results

The initial sandboxed diagnostics returned:

- Docker CLI warning: access denied opening the Docker configuration file.
- Docker Engine error: `permission denied while trying to connect to the docker API at npipe:////./pipe/docker_engine`.
- `docker info`, container, volume, and network queries could not complete in that sandbox context.

The same authorized read-only queries in the elevated diagnostic context succeeded. `docker version` reported both client and server version `29.1.3`; `docker info` reported Docker Desktop, Linux/amd64, WSL2 kernel `6.6.87.2-microsoft-standard-WSL2`, 12 containers (8 running, 4 stopped), and 36 images. Read-only container, volume, and network listings completed. No lifecycle command was run.

## 7. Docker Context and Endpoint Analysis

`docker context ls` in the accessible context showed:

- `desktop-linux` — active (`*`), endpoint `npipe:////./pipe/dockerDesktopLinuxEngine`.
- `default` — endpoint `npipe:////./pipe/docker_engine`.

`docker context show` and `docker context inspect default` in the sandbox showed `default`, because the sandbox could not read the Docker CLI configuration. In the authorized elevated context, `docker version` identified the active context as `desktop-linux`, and the Engine was reachable. No override variable was present to redirect the CLI.

**Conclusion:** the issue was access to the user-scoped Docker config/named pipe from the sandboxed process, not an incorrect Docker installation or an inactive Engine. The normal host context is healthy when queried with the authorized access boundary. No context was switched or edited.

## 8. WSL Status

Read-only `wsl --status` reported default distribution `OracleLinux_8_10` and default WSL version 2. `wsl --list --verbose` showed `OracleLinux_8_10` and `docker-desktop` running under WSL 2; `Ubuntu` was stopped under WSL 2. Docker Engine's reported WSL2 kernel and successful engine query confirm Docker Desktop's backend was operational. The sandboxed WSL queries returned access denied; the elevated read-only queries succeeded. No distribution was started or modified.

## 9. PostgreSQL Test Environment Findings

The repository guard requires test mode and explicit confirmation plus the exact isolated target `127.0.0.1:55432`, database `ai_bap_test`, user `ai_bap_test_user`, and matching process-local test-only password variables. `compose.test.yaml` defines project `ai-bap-test`, PostgreSQL 16, a loopback-only port mapping, and named volume `ai_bap_test_data`. The documentation explicitly separates this database from application Compose and `.env` configuration.

Read-only Docker inspection identified the existing container `ai-bap-test-db-test-1` with Compose labels `project=ai-bap-test` and `service=db-test`, a healthy/running state, the dedicated named volume `ai-bap-test_ai_bap_test_data`, and host mapping `127.0.0.1:55432` to container port `5432`. Windows also reported the listener on `127.0.0.1:55432` (PID 19244, matching a Docker backend process). Other unrelated containers and volumes were only listed; none were changed.

This confirms an isolated test topology, but it is an **existing persistent database volume**, not an ephemeral container-only store. ADIM 8.10.199 did not inspect database contents, retrieve credentials, connect, migrate, or run tests. Given ADIM 8.10.198's prohibition on modifying existing persistent databases, a future test run still needs explicit authorization to use this existing test database or an approved alternative lifecycle/port plan. There is no basis to characterize it as disposable storage for this step.

## 10. Ruff Environment Findings

- Default `python`: Python `3.13.11` at the system Python installation.
- `python -m pip show ruff`: Ruff not installed in that environment.
- `Get-Command ruff`: no Ruff executable on the current process PATH.
- `backend/.venv/Scripts/python.exe`: exists and reports Python `3.13.11`.
- `backend/.venv/Scripts/ruff.exe`: exists; the project virtual environment reports Ruff `0.17.0` through `pip show`.
- `backend/pyproject.toml` declares `ruff>=0.11,<1.0` in the optional `dev` dependency group.

**Conclusion:** Ruff was unavailable because the earlier command used system Python rather than the already-populated backend virtual environment. No install or environment modification is required; a separately authorized validation can invoke `backend/.venv/Scripts/ruff.exe` directly (or use the existing venv's Python module).

## 11. Root Cause Assessment

| Category | Assessment |
|---|---|
| Docker Desktop not running | Ruled out: Docker Desktop processes and service were present; Engine queries succeeded. |
| Docker Engine not initialized | Ruled out: server returned version/info and resource listings. |
| Incorrect Docker context | Not a host-level fault; `desktop-linux` is active and healthy in the accessible context. The sandbox saw `default` because configuration access was denied. |
| Invalid endpoint override | Ruled out: no `DOCKER_HOST`/`DOCKER_CONTEXT` override was present. The sandbox's fallback default pipe was inaccessible to that process. |
| WSL backend issue | Not indicated: Docker reports the WSL2 kernel; Docker Desktop and its WSL distribution are running. |
| Windows service/permissions | Confirmed execution-context permission boundary: sandbox access to Docker config and named pipe was denied; authorized elevated read-only access succeeded. No service repair is indicated. |
| Docker installation problem | Ruled out by successful server connection and version/inventory queries. |
| Overall confidence | High for the sandbox-access explanation; this does not establish permission behavior in every future shell/session. |

## 12. Readiness Matrix

| Criterion | Status | Evidence |
|---|---|---|
| AC-01 Docker CLI availability | PASS | CLI version `29.1.3`; executable path confirmed. |
| AC-02 Docker Desktop installation state | PASS | Docker Desktop `4.57.0`; service/processes present. |
| AC-03 Docker Engine connectivity | PASS (authorized elevated context) | Server version/info and resource listings succeeded; sandbox context remains denied. |
| AC-04 Current Docker context correctness | PASS with context qualification | `desktop-linux` is active and functional in accessible context; sandbox fallback showed `default` due config access restrictions. |
| AC-05 Docker endpoint override safety | PASS | No `DOCKER_HOST` or `DOCKER_CONTEXT` override. |
| AC-06 WSL environment status | PASS | WSL 2, OracleLinux and Docker distributions running; Docker WSL2 backend responds. |
| AC-07 Test database target identified | PASS | Guard and Compose specify loopback `55432`, `ai_bap_test`, test-only user. Existing container owns port. |
| AC-08 Existing database safety checks reviewed | PASS | Fail-closed guard, isolated Compose file, labels, loopback binding, and dedicated named volume reviewed. No connection made. |
| AC-09 Ruff availability identified | PASS | Present in `backend/.venv` at `0.17.0`; absent from system Python/PATH. |
| AC-10 No application/test code changed | PASS | No source, test, or configuration file changed. |
| AC-11 No Docker/database resource mutated | PASS | Only read-only CLI and host queries ran. |
| AC-12 No Git/GitHub/cloud mutation | PASS | No Git state mutation, GitHub operation, provisioning, or deployment occurred. |

## 13. Smallest Safe Corrective Action

No Docker repair or restart is indicated. For any separately authorized database-test step, run the Docker/test commands in an execution context permitted to read the Docker Desktop configuration and access the `desktop-linux` named pipe; do not change Docker context or Windows/WSL settings. Invoke Ruff from the existing backend virtual environment.

Before database-backed tests, obtain separate owner direction on the existing `ai-bap-test` persistent volume: either explicitly authorize test writes to that dedicated database, or authorize a replacement/alternative isolated topology and the required port/guard arrangement. This diagnostic authorization did not permit either choice, and the current test port is occupied by the existing test container.

## 14. Preservation Verification

Repository remained on `docs/ci-pr-evidence` at `f6fff10898fc9a7c3d56a303fba7f50a1b1715e2`; the Git index remained empty. All pre-existing tracked modifications and untracked reports/Playwright files remained present. Only this report was created. No code, tests, environment files, Docker context, Docker service, WSL distribution, container, volume, network, image, database, GitHub resource, or cloud resource was changed. No deployment occurred.

## 15. GO / NO-GO Decision

**GO for Docker engine availability and Ruff environment identification. NO-GO for resuming database-backed tests under the previous ADIM 8.10.198 limits** until the owner clarifies whether the existing persistent `ai-bap-test` database may be modified or approves a safe alternative. The earlier Docker error was specific to sandbox access, and the project Ruff executable is already installed.

## 16. Recommended SINGLE Next Step

Obtain explicit Human Product Owner direction on the database lifecycle boundary—whether the existing labelled `ai-bap-test` database may be used for test writes or an alternate disposable topology should be authorized—before scheduling any DB-backed regression run.
