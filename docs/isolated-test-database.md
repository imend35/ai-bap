# Isolated PostgreSQL Test Database

The existing `ai_bap_test` database is populated and its records are
protected. Its previously exposed password is compromised. Do not run
database-backed tests against that database or reuse that password until a
separately approved rotation and target-safety review is complete. The regular
target guard is retained for backward compatibility, not as proof that its
database is empty or disposable.

I use `compose.test.yaml` only for database-backed tests. It creates the
`ai-bap-test` Compose project, the `ai_bap_test` database, and the dedicated
`ai_bap_test_data` volume. It never references the application Compose file,
application volume, service, or environment file.

Before starting it, I choose a unique test-only password in my shell. I do not
place it in a repository `.env` file.

```powershell
$env:AI_BAP_TEST_POSTGRES_PASSWORD = Read-Host "Enter rotated test-only database password" -AsSecureString | ForEach-Object { [System.Net.NetworkCredential]::new("", $_).Password }
docker compose --env-file docker/compose-test.variables -p ai-bap-test -f compose.test.yaml up -d
```

I pass `--env-file docker/compose-test.variables` instead of allowing Docker
Compose to automatically load the application `.env` file. This non-secret
file may not be replaced with the application `.env` file.

Before invoking database-backed tests, I set the fail-closed test values:

```powershell
$env:AI_BAP_TEST_MODE = "true"
$env:AI_BAP_TEST_DATABASE_CONFIRMATION = "isolated-postgresql-acknowledged"
$env:POSTGRES_HOST = "127.0.0.1"
$env:POSTGRES_PORT = "55432"
$env:POSTGRES_DB = "ai_bap_test"
$env:POSTGRES_USER = "ai_bap_test_user"
$env:POSTGRES_PASSWORD = $env:AI_BAP_TEST_POSTGRES_PASSWORD
```

The pytest guard runs before application database imports. It rejects missing
confirmation and any host, port, database, or user value that does not match
the isolated test configuration.

I stop the isolated environment only when explicitly authorized:

```powershell
docker compose --env-file docker/compose-test.variables -p ai-bap-test -f compose.test.yaml down
```

I do not add `-v` unless I have explicit approval to remove test data.

## Disposable Regression Environment (ADIM 8.10.203)

The existing `ai-bap-test` project, `ai-bap-test-db-test-1` container,
`ai_bap_test` database, and `ai-bap-test_ai_bap_test_data` volume are
protected. The database currently contains records and must not be treated as
disposable. Do not connect tests or migrations to it as part of the new
regression environment.

The new definition is `compose.regression-test.yaml`. It describes a
*proposed, not yet provisioned* PostgreSQL 16 service. Its intended explicit
Compose project is `ai-bap-regression-disposable-20261024-a202`, service
`db`, expected container
`ai-bap-regression-disposable-20261024-a202-db-1`, database
`ai_bap_regression_20261024`, and loopback-only host mapping
`127.0.0.1:55435` to container port `5432`. Host port `55434` is already
published by the separate rubric-test container
`ai-bap-rubric-test-db-1` and must not be reused or modified. Port `55435` is
not reserved; its availability is not verified by this change and must be
checked immediately before separately authorized provisioning. Any port
availability observation is time-bound. The Compose YAML defines no data
volume and sets `PGDATA` to `/var/lib/postgresql/regression-data`, outside the
official image’s conventional `/var/lib/postgresql/data` path. This does not
prove that Docker creates no volume: the `postgres:16` image may declare
`VOLUME /var/lib/postgresql/data`, which can cause Docker to create an
anonymous volume from image metadata even without a Compose `volumes:` entry.
Custom `PGDATA` may leave that mount unused, but does not guarantee its
absence. Local image metadata and runtime mounts have not been verified, so
actual mount behavior is **NOT VERIFIED**. Treat any image-declared anonymous
volume as a run-specific disposable resource; do not claim a zero-volume
container. The distinct Compose project/container identity, database, role,
and loopback port isolate the proposed service from the protected existing
test environment. The Compose file does not reference or mount
`ai-bap-test_ai_bap_test_data`. Do not provision until separate owner approval
and host-side collision checks confirm names and port are free.

The Compose service initializes a bootstrap superuser, not the test identity.
The runtime role is `ai_bap_regression_user_20261024`. After the new database
is initialized, a separately approved manual bootstrap must create that
non-superuser login, set its password interactively, make it owner of only the
new database and its application schema, and grant only the privileges needed
for guarded migrations/tests. Tests and Alembic must never use the bootstrap
superuser. No bootstrap SQL/script is included in this change.

### Secret handling

Supply `AI_BAP_REGRESSION_BOOTSTRAP_SECRET_FILE` only in the host process,
pointing to an owner-restricted secret file outside the repository. The
Compose definition consumes it using `POSTGRES_PASSWORD_FILE`; it contains no
password literal. Do not print the path if it reveals private information,
echo secret contents, pass passwords as command-line arguments, or place
credentials in Git, reports, README files, URLs, or frontend variables. The
host test process receives the runtime role secret through the process-only
variables `AI_BAP_DISPOSABLE_TEST_POSTGRES_PASSWORD` and matching
`POSTGRES_PASSWORD`, entered without echo. Never reuse the previously exposed
`ai_bap_test_user` password. Secret files and process variables are managed
only during a separately approved host operation.

### Guard selection and preflight

The backward-compatible default target remains the existing regular target
only when `AI_BAP_TEST_TARGET` is absent (or explicitly `isolated-test`). The
new target requires the exact selector
`AI_BAP_TEST_TARGET=disposable-regression`,
`AI_BAP_TEST_MODE=true`, and the exact non-secret acknowledgment
`AI_BAP_DISPOSABLE_TEST_DATABASE_CONFIRMATION=disposable-regression-postgresql-acknowledged`.
It also requires the exact host/port/database/user tuple in the central guard
and a non-empty dedicated runtime secret matching `POSTGRES_PASSWORD`.
Unknown, partial, mixed, or conflicting target configuration fails closed.

The app’s settings support `DATABASE_URL`, which can override `POSTGRES_*`.
The pytest bootstrap now validates the effective settings URL—including a
dotenv-derived override—before test modules can create/use `SessionLocal`.
The guarded Alembic wrapper validates its effective URL before invoking
Alembic. Do not invoke `alembic` directly. No database connection is opened by
URL validation itself. An identity preflight must additionally confirm the
live database and user after an explicitly authorized connection and before
any DDL or tests.

### Future host-side workflow — not executed by this documentation

1. Obtain separate approval for source changes, host provisioning, runtime
   role bootstrap, migration, each database test phase, and any cleanup.
2. On the authorized Windows host, check that the exact project/container
   names and `127.0.0.1:55435` are unused. Stop on any collision. Confirm the
   existing project and volume remain untouched.
3. Create a protected bootstrap secret file outside the repository and set
   `AI_BAP_REGRESSION_BOOTSTRAP_SECRET_FILE` in the current PowerShell
   process. Invoke only the documented Compose file with explicit
   `-p ai-bap-regression-disposable-20261024-a202`; do not use the app or
   existing test Compose files. Confirm container labels, exact name, port
   binding, image, health, and every actual mount before use, including
   anonymous image-declared volumes. Stop on unexpected mounts. Neither the
   absence of Compose `volumes:` nor custom `PGDATA` proves there are no
   Docker-managed volumes.
4. Through a separately approved interactive bootstrap, create the distinct
   runtime role and set its password without echo. Test connections use only
   that runtime role, never the bootstrap superuser.
5. Set process-only test variables for the exact disposable selector/tuple
   and runtime role password. Do not set an application `DATABASE_URL`; if a
   dotenv or process override exists, the guard must validate it against the
   exact target or abort.
6. Perform a read-only identity/schema check first. Require the expected
   database, runtime role, loopback endpoint, and empty application schema.
   Stop on any mismatch or unexpected objects.
7. After separate approval, run migrations only through
   `backend/scripts/run_isolated_test_alembic.py` using the disposable target
   selector (`AI_BAP_TEST_TARGET=disposable-regression` and
   `AI_BAP_ALEMBIC_TARGET=disposable-regression`), then verify Alembic head
   and expected tables.
8. Run the approved regression phases: database-independent guard/RBAC and
   static configuration checks; target identity/connectivity; auth/JWT;
   RBAC/admin; project persistence; approval/audit; then the combined
   relevant suite. Record actual commands, exit codes, counts, identity
   (without credentials), and aggregate before/after counts. Stop on
   unexplained changes or cleanup failures.

Approval/audit tests intentionally leave audit rows after their synthetic
story and user records are deleted. The expected audit count therefore grows
inside the disposable database; snapshot identifiers remain while FK actor
and story fields become null. Do not try to erase this history to force a
zero count. A fresh run-specific database provides repeatability.

The existing `ai_bap_test` credential was previously exposed and is treated
as compromised. Rotation is a separate authorized security task; it is not
performed by creating this new target. Coordinate rotation of the database
role password and all authorized client secret sources without deleting or
recreating the existing persistent volume. Do not use the old password for
the new environment.

### Lifecycle and cleanup boundary

Capture test output, schema revision, aggregate table counts, identity
verification, exact Compose labels, all mount metadata, and failure
diagnostics before considering cleanup. Cleanup is optional and requires
separate explicit approval. Before any lifecycle action, verify the exact
disposable container name, project/target labels, and each associated mount;
identify an anonymous volume by its exact container association. Do not delete
any volume without separate explicit approval. Never use broad Docker cleanup
or operate on `ai-bap-test-db-test-1` or
`ai-bap-test_ai_bap_test_data`. Keep the protected bootstrap secret file
available while the container consumes it; removal of that file is also an
explicit, narrowly scoped host action after confirming it is no longer
needed.

## Legacy Migration Validation Environment

I use `compose.legacy-migration-test.yaml` only when I have explicit approval
to validate a migration against synthetic pre-migration data. It is separate
from `ai-bap-test`: it uses the `ai-bap-legacy-migration-test` project,
`ai_bap_legacy_test` database, `ai_bap_legacy_test_user`, loopback port
`55433`, and `ai_bap_legacy_test_data` volume.

Before starting this separately approved environment, I provide a different
test-only password through the calling shell. I never use an application
environment file.

```powershell
$env:AI_BAP_LEGACY_TEST_POSTGRES_PASSWORD = Read-Host "Enter existing test database password" -AsSecureString | ForEach-Object { [System.Net.NetworkCredential]::new("", $_).Password }
docker compose --env-file docker/compose-legacy-migration-test.variables -p ai-bap-legacy-migration-test -f compose.legacy-migration-test.yaml up -d
```

The guarded Alembic wrapper allows this target only after all of the following
values are set exactly. The `AI_BAP_ALEMBIC_TARGET` selector and separate
acknowledgment prevent an accidental substitution of the ordinary test target.

```powershell
$env:AI_BAP_TEST_MODE = "true"
$env:AI_BAP_ALEMBIC_TARGET = "legacy-migration"
$env:AI_BAP_LEGACY_TEST_DATABASE_CONFIRMATION = "legacy-migration-postgresql-acknowledged"
$env:POSTGRES_HOST = "127.0.0.1"
$env:POSTGRES_PORT = "55433"
$env:POSTGRES_DB = "ai_bap_legacy_test"
$env:POSTGRES_USER = "ai_bap_legacy_test_user"
$env:POSTGRES_PASSWORD = $env:AI_BAP_LEGACY_TEST_POSTGRES_PASSWORD
```

For the approved legacy-backfill procedure, I will first run the guarded
wrapper to revision `921eeafe8be6`, insert only synthetic fixtures, then run
the same wrapper to `c7a8d9e0f1b2`. I will not run an unguarded Alembic command,
downgrade either isolated database, or remove volumes without separate approval.
