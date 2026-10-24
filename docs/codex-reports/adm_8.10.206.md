# ADIM 8.10.206 — Host-Side Docker Image Metadata & Resource Isolation Preflight

## 1. Step Name and Objective

This read-only preflight assessed whether the proposed disposable PostgreSQL regression environment can be provisioned without colliding with existing Docker resources. It did not provision or contact a database.

## 2. Human Product Owner Authorization

Actions were limited to repository reads, Git inspection, Docker CLI availability/version diagnostics, a local TCP listener check, and local YAML parsing. Docker daemon operations were attempted only for read-only availability diagnostics; access was denied. No fallback, elevation, or retry was attempted. No database/SQL, credential, migration, Docker resource mutation, Git/GitHub, cloud, or deployment operation occurred.

## 3. Baseline Git State

- Branch: `docs/ci-pr-evidence`.
- HEAD: `f6fff10898fc9a7c3d56a303fba7f50a1b1715e2`.
- Index: empty.
- `docs/codex-reports/adm_8.10.206.md` was absent at baseline.
- Numerous tracked modifications and untracked reports/E2E files were already present; they were preserved.

## 4. Docker Availability

Docker CLI is installed at `C:\Program Files\Docker\Docker\resources\bin\docker.exe`, version `29.1.3`, client OS/architecture `windows/amd64`. Docker Compose plugin version `v5.0.1` is installed. The CLI reported context `default` and attempted `npipe:////./pipe/docker_engine`.

Commands and results:

```text
docker version
```

Exit code `1`: Docker client details printed, then `permission denied while trying to connect to the docker API at npipe:////./pipe/docker_engine`. Docker also warned it could not read the user Docker config due to access denied.

```text
docker info
```

Exit code `1`: client/plugin information printed; server access failed with the same named-pipe permission denial.

```text
docker compose version
```

Exit code `0`: Compose `v5.0.1`; a Docker config access warning appeared. This reports the CLI plugin version only, not daemon connectivity.

No attempt was made to change Docker context, access settings, or permissions.

## 5. PostgreSQL Image Metadata

Local availability of `postgres:16`, image ID/digest, OS/architecture metadata, `Config.Env`, and `Config.Volumes` are **NOT VERIFIED** because image listing/inspection requires the inaccessible Docker daemon. No image was pulled. In particular, whether this local image declares `/var/lib/postgresql/data` as a `VOLUME` is **NOT VERIFIED**.

## 6. Anonymous-Volume Risk

Static Compose inspection confirms `PGDATA=/var/lib/postgresql/regression-data` and no Compose-declared service or top-level volume. The configured path is distinct from the conventional `/var/lib/postgresql/data` path. However, absent image metadata, it cannot be determined whether the image declares a `VOLUME` at the latter path. If it does, Docker may create an anonymous mount based on image metadata despite the absent Compose volume declaration; custom `PGDATA` does not suppress or prove absence of that mount. Whether such a mount would contain database files or be unused depends on runtime image/entrypoint behavior and is **NOT VERIFIED**. Actual mounts can only be established after separately authorized provisioning and read-only inspection of the exact container.

## 7. Existing Container Inventory

The protected container name `ai-bap-test-db-test-1` and proposed name `ai-bap-regression-disposable-20261024-a202-db-1` were identified from the supplied baseline and local documentation. Live container listing, status, labels, IDs, and port bindings could not be queried because Docker daemon access was denied. Whether the protected container currently exists/runs or the proposed name/project is occupied is **NOT VERIFIED**. No container was inspected or changed.

## 8. Existing Volume Inventory

The protected volume name `ai-bap-test_ai_bap_test_data` is documented and treated as protected. Its live existence/labels, and any volumes associated with the proposed project/container, could not be listed because daemon access was denied. Ownership of any anonymous volume is **NOT VERIFIED**. No volume was mounted, read, or changed.

## 9. Existing Network Inventory

Live network inventory and any network carrying the proposed Compose project label are **NOT VERIFIED** because daemon access was denied. Static Compose YAML does not declare a custom network. No network was created, inspected, connected, or modified.

## 10. TCP Port 55434 Availability

Read-only PowerShell check:

```powershell
Get-NetTCPConnection -LocalPort 55434 -State Listen -ErrorAction SilentlyContinue
```

Result: no listening TCP endpoint was observed at inspection time. This is a time-bound observation, not a reservation or guarantee of availability. Docker port bindings could not be cross-checked because container metadata was unavailable. Recheck immediately before any future, separately authorized provisioning.

## 11. Compose Configuration Validation

The local `compose.regression-test.yaml` was parsed with PyYAML `safe_load` in memory. Static assertions passed (exit code `0`) for project name `ai-bap-regression-disposable-20261024-a202`, service `db`, container name `ai-bap-regression-disposable-20261024-a202-db-1`, image `postgres:16`, exact loopback mapping `127.0.0.1:55434:5432`, database name, secret-file reference, absence of a plaintext password and Compose-declared volumes, absence of privileged/host-network settings, health check, restart policy `no`, and configured PGDATA.

`docker compose -f compose.regression-test.yaml config` was not run. Compose interpolation requires `AI_BAP_REGRESSION_BOOTSTRAP_SECRET_FILE`; a CLI config operation might consult a project `.env` or require resolving a secret-file path. To avoid any implicit `.env`/secret-file access and because safe local YAML parsing succeeded, the command was skipped. No Compose daemon operation occurred.

## 12. Resource Collision Matrix

| Resource | Expected | Observed | Collision status | Evidence / status |
|---|---|---|---|---|
| Compose project | `ai-bap-regression-disposable-20261024-a202` | Static YAML declares this name; live project labels unavailable | NOT VERIFIED | Docker daemon denied |
| Container | `ai-bap-regression-disposable-20261024-a202-db-1` | Expected name in YAML; no live container inventory | NOT VERIFIED | Docker daemon denied |
| Host port | `127.0.0.1:55434` | No TCP listener observed; Docker bindings unavailable | NOT VERIFIED (no listener observed) | PowerShell listener query; time-sensitive |
| Docker network | Compose-generated project network | No custom network in YAML; live network list unavailable | NOT VERIFIED | Docker daemon denied |
| Database | `ai_bap_regression_20261024` | Static configuration only; database query prohibited | NOT VERIFIED | No DB connection authorized |
| Runtime role | `ai_bap_regression_user_20261024` | Documented design only; no live database inspection | NOT VERIFIED | No DB connection authorized |
| Image | `postgres:16` | YAML reference only; local image presence/metadata unavailable | NOT VERIFIED | Docker daemon denied |
| Protected volume | `ai-bap-test_ai_bap_test_data` | Name supplied/documented; live inventory unavailable | NOT VERIFIED (treated protected) | No volume access |
| Potential anonymous volume | Image-declared path, if any | `Config.Volumes` unavailable; runtime mount unknown | NOT VERIFIED | No image/container inspect |

## 13. Safety Decision

**INSUFFICIENT EVIDENCE.** No port listener was observed and the Compose file passes local static validation, but required Docker inventory, image `Config.Volumes`, container/project collision checks, network/volume inventory, and image presence could not be established. A separately approved provisioning decision should wait for a host environment where read-only Docker daemon inspection is authorized and succeeds. This decision does not itself authorize provisioning.

## 14. Acceptance Criteria Matrix

| Criterion | Status | Evidence |
|---|---|---|
| AC-01 Only read-only operations | PASS | No resource or repository-state mutation. |
| AC-02 Exactly one report created | PASS | This report; absent at baseline. |
| AC-03 Docker CLI/daemon checked | PASS | CLI present; daemon queries failed with permission denied. |
| AC-04 Local `postgres:16` metadata inspected or limitation recorded | NOT VERIFIED | Limitation recorded; image not inspectable through denied daemon. |
| AC-05 `Config.Volumes` risk assessed | NOT VERIFIED | Risk explained; metadata unavailable. |
| AC-06 Protected container identified | NOT VERIFIED | Name known from supplied baseline, live identity/status not verified. |
| AC-07 Proposed container collision checked | NOT VERIFIED | No live inventory. |
| AC-08 Protected volume identified | NOT VERIFIED | Protected name known; live volume metadata not verified. |
| AC-09 Disposable volume collision checked | NOT VERIFIED | No volume inventory. |
| AC-10 Disposable network collision checked | NOT VERIFIED | No network inventory. |
| AC-11 Host port 55434 checked | PASS (limited) | No listening TCP endpoint observed at check time; no Docker binding cross-check. |
| AC-12 Compose configuration inspected | PASS | Local YAML parsed and static assertions passed. |
| AC-13 Resource collision matrix completed | PASS | Matrix included with unavailable observations explicitly marked. |
| AC-14 No database connection or SQL | PASS | None performed. |
| AC-15 No Docker resource mutation | PASS | None performed. |
| AC-16 No migration or DB-backed tests | PASS | None performed. |
| AC-17 No credential exposure | PASS | No secret values or secret-file contents accessed. |
| AC-18 No application/configuration edit | PASS | Only authorized report created. |
| AC-19 No Git/GitHub/cloud mutation | PASS | Read-only Git checks only. |
| AC-20 Existing 50-record database preserved | PASS (not contacted) | No database or protected volume access; counts not re-queried. |
| AC-21 Explicit safety decision | PASS | Decision: INSUFFICIENT EVIDENCE. |

## 15. Residual Risks and Blockers

- Docker daemon access is denied at the Windows named pipe, so all live Docker resource checks are blocked.
- Local image availability and image-declared `VOLUME` metadata are unknown; the anonymous-volume behavior remains unknown.
- Proposed project/container/network/volume collisions cannot be ruled out.
- Port 55434 had no observed listener, but that result is time-sensitive and Docker bindings were unavailable.
- Database and runtime-role availability cannot be checked without a prohibited database connection.
- The protected database’s 50-record count is historical owner-provided evidence, not re-queried in this step; the database and volume were not contacted.

## 16. Git and Resource Preservation

Final read-only checks confirmed branch `docs/ci-pr-evidence`, HEAD `f6fff10898fc9a7c3d56a303fba7f50a1b1715e2`, and an empty index. Existing pending work remained present; only this authorized report was newly created. No source/configuration file, Docker resource, PostgreSQL database, GitHub state, or cloud resource was modified. No credentials were read or printed.

## 17. Recommended SINGLE Next Step

Ask the Human Product Owner to run or authorize a host-side **read-only** Docker inventory in an environment with Docker daemon access, specifically verifying the local `postgres:16` image’s `Config.Volumes` plus proposed project/container/network/volume collisions and the protected volume identity. Do not provision until that evidence is available and reviewed.
