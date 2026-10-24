# ADIM 8.10.164 — Controlled Docker Build Connectivity Verification

## 1. Objective

I verified that Docker BuildKit can build the existing AI BAP backend and frontend Dockerfiles after the Docker Hub DNS failure that blocked ADIM 8.10.158. The verification used uniquely tagged temporary images only. It did not start containers or modify Docker, application, or Git configuration.


## 2. Git and working-tree baseline

- Branch: `docs/ci-pr-evidence`
- HEAD: `2afe0d4d88188ad0a8de14c590ca95d0536b1241`
- Git index: empty before and after the build.
- Existing pending work was preserved, including the modified ADIM 8.10.76 report, frontend package metadata, earlier untracked Codex reports, and untracked Playwright files.

## 3. Docker builder and registry status

Docker Desktop was available through the `desktop-linux` context.

| Check | Result |
| --- | --- |
| Docker client/server | `29.1.3` / `29.1.3` |
| Active Buildx builder | `desktop-linux` |
| BuildKit status | Running (`v0.26.2`) |
| Backend base-image metadata | Accessible for `python:3.13-slim` and `ghcr.io/astral-sh/uv:0.6.10` |
| Frontend base-image metadata | Accessible for `node:22-alpine` and `nginx:1.27-alpine` |

The base-image metadata resolution is direct BuildKit evidence that the earlier Docker Desktop registry DNS failure is no longer reproduced in this verification.

## 4. Build configuration inspected

- Backend: `docker/backend/Dockerfile`, built with repository-root context (`.`), matching `compose.yaml`.
- Frontend: `docker/frontend/Dockerfile`, built with repository-root context (`.`), matching `compose.yaml`.
- No Dockerfile, build argument, Compose, or source-code change was made.

## 5. Temporary-image isolation

The following tags were checked and confirmed absent before building:

- `ai-bap-adim-164-backend:verification`
- `ai-bap-adim-164-frontend:verification`

They were created only by this task and were inspected by exact tag before removal.

## 6. Backend build result

**PASS.**

Command executed:

```powershell
docker buildx build --load --tag ai-bap-adim-164-backend:verification --file docker/backend/Dockerfile .
```

BuildKit resolved the pinned uv and Python base-image metadata, completed the existing backend build stages, and loaded the uniquely tagged image. Some application layers were served from the local BuildKit cache; that is expected and does not weaken the verified registry metadata access.

## 7. Frontend build result

**PASS.**

Command executed:

```powershell
docker buildx build --load --tag ai-bap-adim-164-frontend:verification --file docker/frontend/Dockerfile .
```

BuildKit resolved the Node and Nginx base-image metadata. The existing `npm ci` stage was cached, and the production frontend build executed successfully (`tsc -b && vite build`) before the image was loaded under the temporary tag.

## 8. Base-image layer accessibility

| Required base image | BuildKit result |
| --- | --- |
| `ghcr.io/astral-sh/uv:0.6.10` | Metadata and image reference resolved |
| `python:3.13-slim` | Metadata and image reference resolved |
| `node:22-alpine` | Metadata and image reference resolved |
| `nginx:1.27-alpine` | Metadata and image reference resolved |

This verifies metadata accessibility and successful use by the existing BuildKit build. It does not independently establish that every future image download will succeed under every network condition.

## 9. Cleanup verification

After successful inspection, I removed only the two exact temporary image tags:

- `ai-bap-adim-164-backend:verification`: removed.
- `ai-bap-adim-164-frontend:verification`: removed.

Post-cleanup inspection confirmed both tags were absent. No Docker prune operation, shared-layer removal request, cache removal, or pre-existing tag removal was performed.

## 10. Unrelated-resource preservation

Docker resource counts were unchanged before and after the builds:

| Resource type | Before | After |
| --- | ---: | ---: |
| Containers | 12 | 12 |
| Volumes | 27 | 27 |
| Networks | 8 | 8 |

No containers were started or stopped. No volumes or networks were created, modified, or removed.

## 11. PASS / FAIL / BLOCKED matrix

| Verification | Status | Evidence |
| --- | --- | --- |
| Docker Desktop and Buildx availability | PASS | Engine and `desktop-linux` BuildKit builder were running. |
| Temporary-tag preflight | PASS | Both selected tags were absent before build. |
| Backend BuildKit build | PASS | Existing backend Dockerfile built and loaded successfully. |
| Frontend BuildKit build | PASS | Existing frontend Dockerfile built and loaded successfully. |
| Required base-image metadata access | PASS | uv, Python, Node, and Nginx references resolved. |
| Temporary-tag cleanup | PASS | Both verified task-owned tags were removed. |
| Existing Docker-resource preservation | PASS | Container, volume, and network counts did not change. |
| Browser E2E execution | NOT RUN | Explicitly outside this build-connectivity verification. |

## 12. Recommended single next action

**Authorize a new isolated Playwright E2E rerun using a new unique Compose project, fresh loopback ports, synthetic credentials, and verified cleanup.**

## 13. GO / NO-GO for isolated E2E rerun

**GO.** BuildKit registry access and both required application image builds are now verified. A future E2E run must still independently establish Compose-project isolation, disposable-database ownership, synthetic credentials, service health, and safe cleanup before starting any containers.
