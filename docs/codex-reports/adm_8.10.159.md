# ADIM 8.10.159 — Docker Registry DNS Connectivity Diagnostics

## 1. Objective

I performed read-only diagnostics after ADIM 8.10.158 could not build the new isolated E2E Compose stack because Docker Desktop reported that it could not resolve `registry-1.docker.io`. No Docker, Windows network, proxy, VPN, application, or Git configuration was changed.

## 2. Git and working-tree baseline

- Branch: `docs/ci-pr-evidence`
- HEAD: `2afe0d4d88188ad0a8de14c590ca95d0536b1241`
- Git index: empty.
- Pre-existing pending work was preserved, including the modified ADIM 8.10.76 report, Playwright dependency metadata, earlier untracked Codex reports, and the untracked Playwright configuration and E2E test files.

## 3. Build-failure evidence

ADIM 8.10.158 stopped before Compose created resources. Docker Desktop failed while resolving base-image metadata for `python:3.13-slim`, `node:22-alpine`, and `nginx:1.27-alpine`, reporting a lookup failure for `registry-1.docker.io` on port 443. The isolated project `ai-bap-e2e-158-4d8a` therefore created no containers, networks, or volumes. The pre-existing `ai-bap-rubric-test` resources were not changed.

## 4. Docker engine and context status

Read-only Docker checks found:

| Check | Result |
| --- | --- |
| Docker client/server | `29.1.3` / `29.1.3` |
| Active context | `desktop-linux` |
| Engine operating system | Docker Desktop |
| Storage driver | `overlayfs` |
| Default bridge network | Present |
| Docker-reported HTTP, HTTPS, and no-proxy configuration | Configured (values intentionally not inspected or recorded) |

Docker Desktop was available for read-only engine queries. No containers were started, stopped, inspected for secrets, or otherwise changed.

## 5. Windows host DNS diagnostics

Windows successfully resolved all required host names to IPv4 addresses:

| Host | DNS | TCP port 443 |
| --- | --- | --- |
| `registry-1.docker.io` | Resolved | Reachable |
| `auth.docker.io` | Resolved | Reachable |
| `production.cloudflare.docker.com` | Resolved | Reachable |

This excludes a contemporaneous Windows host DNS failure for these endpoints. It does not prove that Docker Desktop uses the same DNS path.

## 6. Docker Hub HTTPS connectivity

Non-authenticated host HTTPS requests produced these status codes:

| Endpoint | Result | Interpretation |
| --- | --- | --- |
| `https://registry-1.docker.io/v2/` | HTTP 401 | Expected Docker Registry v2 authentication challenge; endpoint was reachable. |
| `https://auth.docker.io/` | HTTP 404 | Reachable endpoint; this root path is not a token request. |
| `https://production.cloudflare.docker.com/` | HTTP 403 | Reachable endpoint; access is denied for the unauthenticated root request. |

These outcomes are connectivity evidence only. No credentials, authentication headers, image manifests, or layers were requested.

## 7. Docker Desktop network and proxy findings

- Docker Desktop reports HTTP proxy, HTTPS proxy, and no-proxy configuration as present; their values were not read or disclosed.
- Process-level `HTTP_PROXY`, `HTTPS_PROXY`, and `NO_PROXY` variables were absent.
- Windows WinHTTP reported direct access (no configured WinHTTP proxy).
- No active adapter matched the inspected common VPN adapter patterns. This is not conclusive evidence that no VPN, endpoint-security filter, or corporate network policy is present.
- The ADIM 8.10.158 message said Docker Desktop had no HTTPS proxy while it failed DNS lookup. That message reflects the failing build path; it does not reconcile or expose Docker Desktop’s configured proxy values.

## 8. Local base-image inventory

The exact relevant image references were inspected without pulling or building:

| Image reference | Local availability |
| --- | --- |
| `postgres:16` | Present |
| `python:3.13-slim` | Absent |
| `node:22-alpine` | Absent |
| `nginx:1.27-alpine` | Absent |
| `ghcr.io/astral-sh/uv:0.6.10` | Absent |

`postgres:16` is referenced by `compose.yaml`; the Python, Node, Nginx, and uv references are used by the backend and frontend Dockerfiles. The migration-rehearsal Dockerfile accepts its base-image references as arguments, so its exact runtime values were not inferred here.

## 9. Offline-build feasibility

**NO-GO for an offline E2E build.** Only PostgreSQL is locally available. The required Python, Node, Nginx, and uv base images are absent. Even if all tags had been present, tag availability alone would not prove that all required build cache layers and package artifacts were available. No offline build was attempted.

## 10. Most likely root cause

**Most likely failure domain: Docker Desktop DNS/networking or its configured proxy path.**

Windows host DNS, TCP connectivity, and unauthenticated HTTPS access to Docker Hub endpoints all succeeded after the failure. In contrast, Docker Desktop’s earlier build path failed specifically at name resolution. Docker Hub availability and a general Windows DNS outage are therefore unlikely explanations. The diagnostics cannot distinguish a Docker Desktop internal resolver issue from an interaction with its proxy, endpoint security, or network policy without inspecting or changing Docker Desktop settings, which is outside this task.

## 11. Risks and safeguards

- No registry pulls, builds, image removal, Docker Desktop restart, configuration change, or container lifecycle action was performed.
- No proxy credentials, tokens, URLs containing credentials, or Docker configuration values were printed.
- The existing `ai-bap-rubric-test` stack and its persistent volume were not changed.
- A future E2E run must use a new unique Compose project and must reconfirm isolation before startup.

## 12. Recommended next action

**Ask the operator to inspect Docker Desktop's proxy and DNS configuration in its UI, compare it with the working host network, and explicitly approve any reversible settings change or Docker Desktop restart before retrying the isolated E2E run.**

## 13. GO / NO-GO for E2E rerun

**NO-GO.** The isolated E2E rerun remains blocked because required base images are absent locally and Docker Desktop’s registry DNS path has not been restored. The browser test must not be retried until the operator resolves and verifies Docker Desktop registry connectivity.
