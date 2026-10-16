# Isolated PostgreSQL Test Database

I use `compose.test.yaml` only for database-backed tests. It creates the
`ai-bap-test` Compose project, the `ai_bap_test` database, and the dedicated
`ai_bap_test_data` volume. It never references the application Compose file,
application volume, service, or environment file.

Before starting it, I choose a unique test-only password in my shell. I do not
place it in a repository `.env` file.

```powershell
$env:AI_BAP_TEST_POSTGRES_PASSWORD = Read-Host "Enter existing test database password" -AsSecureString | ForEach-Object { [System.Net.NetworkCredential]::new("", $_).Password }
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
