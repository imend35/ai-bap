# ADIM 8.10.65 — Docker Desktop Registry Connectivity Diagnostics

## Step Name and Objective

Diagnose the Docker Hub registry connectivity failure that blocked the isolated full-stack image build in ADIM 8.10.64 without modifying Docker configuration, resources, or application files.

## Diagnostic Commands Executed and Sanitized Results

- Docker context: `desktop-linux`.
- Docker Desktop status: running.
- Docker client/server version: 29.1.3 / 29.1.3.
- Windows DNS: one IPv4 DNS server is configured for the active Wi-Fi interface; DNS resolution succeeded for both `registry-1.docker.io` and `auth.docker.io`.
- Windows TCP/443: reachable for both Docker Hub hosts.
- Windows HTTPS checks: the registry `/v2/` endpoint returned expected unauthenticated status 401; the auth endpoint was reachable and returned HTTP 404 for the tested root path. These results demonstrate Windows-to-Docker-Hub HTTPS connectivity, not Docker authentication.
- WinHTTP proxy: direct access (no proxy configured).
- Environment proxy variables: absent.
- Docker client config: exists; no Docker proxy configuration key was found. No configuration values or credentials were printed.
- Cached base images: `postgres:16` is present. Exact tags `python:3.13-slim`, `node:22-alpine`, and `nginx:1.27-alpine` are absent.
- Matching nearby cached tags include non-equivalent Python and PostgreSQL tags, but no compatible Node or nginx tag was found.

## Root Cause Assessment

The evidence rules out a general Windows DNS failure, Windows TCP/HTTPS block, Docker Hub host outage visible from Windows, and missing Windows proxy configuration as the primary observed failure.

The ADIM 8.10.64 build failed inside Docker Desktop while resolving `registry-1.docker.io`; its error explicitly reported direct connection and DNS lookup failure. The most likely cause is therefore a Docker Desktop internal DNS/network-path issue that is distinct from the working Windows host network path. A transient Docker Desktop DNS failure, Docker Desktop network configuration issue, or VPN/firewall policy affecting the internal Linux VM remains possible. This diagnostic cannot prove which of those internal causes applies without changing settings or restarting Docker Desktop.

## Cached Image Assessment

An offline build is not technically possible with the current cache because the exact required base images for the backend and frontend are missing. The repository should not be changed to substitute unrelated cached versions merely to bypass the connectivity issue.

## Recommended Recovery Steps

1. Do not change Dockerfiles, proxy, DNS, firewall, or VPN settings yet; the Windows network path is healthy and no specific configuration defect is proven.
2. With Human Product Owner approval, use Docker Desktop's manual **Restart** action to refresh its internal networking. This action can interrupt existing containers, including active AI BAP database containers, and therefore must not be performed automatically.
3. After the restart, repeat only the isolated ADIM 8.10.64 build using project `ai-bap-rubric-test`, its unique ports, and disposable volume.
4. If the internal lookup still fails, have the operator inspect Docker Desktop settings for the organization-required proxy or DNS configuration and confirm VPN/firewall policy. Any settings change requires separate approval because it affects Docker Desktop globally.
5. Once connectivity is restored, pull/build only through the isolated project and complete the pending health, reverse-proxy, and synthetic smoke checks.

## Whether Isolated Runtime Verification Can Resume

**NOT YET.** Static Compose isolation remains valid, but runtime verification is blocked until Docker Desktop can resolve/fetch the missing base images. No Docker resource was modified during this diagnostic.

## Files Inspected or Modified

- Inspected Docker Desktop/Engine status, Docker context, local image cache, Windows DNS, Windows HTTPS connectivity, and proxy-configuration presence.
- Created only `docs/codex-reports/adm_8.10.65.md`.

## Validation and Test Results

- Docker/resource configuration changes: NOT RUN.
- Image pulls/builds/container lifecycle/database operations: NOT RUN.
- Git staging, commit, push, or application-file changes: NOT RUN.
- Sensitive values: not displayed or recorded.

## Recommended Next Step

Obtain explicit approval before restarting Docker Desktop or changing any global Docker network/proxy/DNS setting. After registry connectivity is restored, repeat the isolated runtime verification without touching the default `ai-bap` project.
