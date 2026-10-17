# Clone-Specific Migration Rehearsal Helper

This helper is limited to a reviewable rehearsal of revision `d4e5f6a7b8c9` on
the approved restored clone. It is not a general migration runner and must
never be aimed at the normal database (`127.0.0.1:5433/ai_bap`) or either test
database (ports `55432` and `55433`). This document does not authorize any
command; each operational action requires separate explicit approval.

The rehearsal has three strictly separate stages: Stage A is the `preflight`
launcher invocation, Stage B is an external human approval through a separately
trusted attestation system, and Stage C is the `upgrade` launcher invocation. The
launcher accepts only `preflight` or `upgrade`; it has no default or combined
mode. A successful stage does not start another one.

- Stage A, `preflight`, opens PostgreSQL with `default_transaction_read_only=on`
  before its first query. It contains no Alembic invocation or subprocess path,
  performs fixed `SELECT` validation only, and emits a safe JSON baseline.
- Stage B is deliberately outside the helper. A human approval must be
  independently verified by a trusted attestation verifier, not by a token,
  text file, or matching digest. The helper never generates an approval.
- Stage C, `upgrade`, revalidates trusted authorization, clone identity,
  migration hashes, source revision, and baseline under read-only access,
  then would perform the one fixed Alembic upgrade and emit read-only
  postflight evidence. It is currently blocked before that point.

The preflight-only command is:

```text
python docker/migration-rehearsal/launch.py preflight
```

It never calls `alembic upgrade`, executes DDL, or modifies a database. To
retain its JSON output for Stage C, an approved operator may save the complete
stdout to a new restrictive-permission file outside the repository. Stage C
requires that path in `REHEARSAL_PREFLIGHT_REPORT_SOURCE`; the launcher mounts
it read-only at a fixed in-container location. The report is machine-readable
JSON and includes a unique approval-request binding. Its binding digest covers the
verified restore-container ID (reported only as a SHA-256 digest), database
identity, source revision, reviewed migration-file hashes, and the complete
baseline fingerprint. The report contains no database rows, row-level IDs,
passwords, connection URLs, secret values, or Docker diagnostics. A malformed
or missing report fails closed; the report must be retained under the approved
operator's control between Stage A and Stage C.

## Scope and hard guards

The image in `docker/migration-rehearsal/Dockerfile` has a fixed entrypoint
that accepts only one fixed stage argument and runs as UID/GID `10001`, not root. The secret
mount target directory is owned by that account. The approved host secret file
must be readable by UID/GID `10001` inside the helper container and must not
be readable by other in-container users. It requires these exact non-secret
settings:

- `REHEARSAL_DATABASE_HOST=127.0.0.1`
- `REHEARSAL_DATABASE_PORT=5432`
- `REHEARSAL_DATABASE_NAME=restore_check_db`
- `REHEARSAL_DATABASE_USER` set to the approved clone-only role

The password is read only from Docker secret mount
`/run/secrets/restore_db_password`. It is not accepted in an environment
variable, command argument, build argument, repository file, or image layer.
The secret source must be supplied when the container is created, must not be
committed, and must not be echoed or inspected.

Stage A performs two independent read-only preflight checks after the launcher
has verified the immutable restore container ID, exact name, running state,
`network=none`, and absence of published ports. First, it asks PostgreSQL to verify the actual
`current_database()`, `inet_server_addr()`, and `inet_server_port()` against
`restore_check_db`, `127.0.0.1`, and `5432`; it reports only a boolean and
rejects a mismatch. Second, it reads `alembic_version` and refuses unless it is
exactly `921eeafe8be6`. It verifies the presence of `users`, `projects`,
`requirements`, `user_stories`, and `user_story_approval_audits`; reads each
legacy column list in ordinal order; and captures an ordered, type-marked,
length-delimited SHA-256 fingerprint with its column list and row count. This
is the deterministic baseline Stage C must match. Stage A performs no mutation.
Before opening the database connection, it also verifies SHA-256 digests and
`revision`/`down_revision` metadata for the reviewed source, target, and
security-follow-up migration files. The required chain is
`921eeafe8be6` → `c7a8d9e0f1b2` → `d4e5f6a7b8c9`; Stage C targets the final revision, which must
include the reviewed trigger-function hardening intent (`search_path` fixed to
`pg_catalog`, qualified sequence access, and no insecure downgrade). Any file,
digest, metadata, chain, or follow-up-intent mismatch fails Stage A before any
database query. The security follow-up is a prerequisite artifact in this
rehearsal; Stage B remains limited to the separately approved fixed target
revision below.
If a trusted external approval verifier is provisioned in a future reviewed
change, the only mutation it may authorize is this fixed subprocess invocation:

```text
alembic -c /workspace/rehearsal/alembic.ini upgrade d4e5f6a7b8c9
```

No user-supplied revision, Alembic argument, database endpoint, or host-side
Alembic execution path exists. The image uses a dedicated Alembic environment,
so it does not read the application `.env` or require unrelated application
secrets.

`docker/migration-rehearsal/launch.py` is the only supported host-side
launcher. It requires one of the two fixed stage arguments and performs `docker inspect` before it can
issue a helper-container command. It requires the full 64-character immutable
ID in `REHEARSAL_APPROVED_RESTORE_CONTAINER_ID`; a short ID, name, image ID, or
newly created replacement container is rejected. The full approved ID was not
provided in this task and is intentionally not invented or stored in source.

The inspection must report all of the following, or the launcher stops before
helper execution:

- the inspected `Id` exactly equals the approved full ID;
- the name is exactly `ai-bap-restore-verification-20261017`;
- `State.Running` is `true`;
- `HostConfig.NetworkMode` is exactly `none`;
- both `HostConfig.PortBindings` and `NetworkSettings.Ports` are empty.

Only after those checks does the launcher use the `Id` returned by that exact
inspection record in its sole network option, `--network
container:<verified-exact-id>`. It has no alternative network mode or network
name option. Its fixed `docker run` command publishes no ports, drops Linux
capabilities, uses `no-new-privileges`, and uses a read-only filesystem. The
launcher also requires a helper image digest reference, not a tag. Docker
subprocess output is captured and discarded; launcher failures report only a
safe category, never a command line, secret-source path, or Docker error text.

The launcher supplies, and the in-container runner independently requires,
only `REHEARSAL_DATABASE_HOST=127.0.0.1`,
`REHEARSAL_DATABASE_PORT=5432`, and
`REHEARSAL_DATABASE_NAME=restore_check_db`. Any substitution is rejected
before a database connection or helper-container execution. Thus the helper's
only possible database destination is `127.0.0.1:5432/restore_check_db` inside
the verified restore container's network namespace.

For local Docker Engine, the temporary credential mount is a read-only bind
mount from the manually approved `REHEARSAL_PASSWORD_SECRET_SOURCE` file to
`/run/secrets/restore_db_password`. The launcher checks only that the source
is a file; it never reads, prints, or passes its contents in an environment,
argument, or image layer. The source must be created outside the repository
with restrictive permissions and removed through a separately approved
cleanup process. This mount is named for the in-container secret interface; it
does not claim to use Docker Swarm secrets.

## Dependency and image provenance

The Dockerfile runs `uv sync --locked --no-dev --no-install-project` against
`backend/uv.lock`. The current lockfile resolves Alembic to `1.20.0` and
psycopg (binary extra) to `3.3.6`; its hashes fix their transitive artifacts.
Python compatibility is the lockfile's `>=3.13` requirement. The application
package and development dependencies are not installed, and this helper adds
no Python dependency.

`docker/migration-rehearsal/build.py` is the only permitted candidate-build
entrypoint. It accepts no arguments and can build only an **untrusted candidate**
under the required local label `REHEARSAL_CANDIDATE_HELPER_IMAGE_TAG` (for
example, `ai-bap-rehearsal-candidate:review`). It rejects registry-qualified
candidate names and launch-time `REHEARSAL_HELPER_IMAGE` or retired
`REHEARSAL_HELPER_IMAGE_TAG` settings so a local build output cannot be
confused with a launchable identity. The candidate label is mutable and is
never proof of image identity or approval.

The reviewed allowlist in `docker/migration-rehearsal/image_policy.py` has
separate roles for the Python base image, uv image, and independently reviewed
rehearsal helper image. Every approved identity must be the complete
`registry/repository@sha256:<64 lowercase hex>` reference; a digest approved
for one repository is not approved for another repository. Building continues
to require approved Python and uv base images, but it deliberately does not
consult the helper allowlist: no local build can establish that it produced an
approved helper digest.

The allowlists are intentionally empty until a reviewer provisions real,
reviewed identities in a separately reviewed source change. With no approved
base images, candidate building refuses. With no approved helper image,
launching refuses with `image_approval_missing`; the launcher neither invents
nor learns an approval from Docker output. A syntactically valid but unlisted
launch identity refuses with `image_not_approved`, while malformed input
refuses with `image_reference_error`. The launcher is the sole enforcement
point for execution and accepts only an exact reviewed helper identity.

Before provisioning each role, a reviewer must independently resolve and
record the complete identity, publisher, manifest list, selected platform, and
review rationale. For the helper role, independently review the candidate,
publish it through the approved process, resolve the published digest, and
review that immutable digest before adding it to the allowlist. The operator
then supplies that exact digest in `REHEARSAL_HELPER_IMAGE` to launch it. A
candidate's local tag, local image ID, build log, or claimed digest is not
acceptable launch evidence. Digest pinning establishes immutability and repository binding only;
it is not provenance, publisher authentication, or signature/attestation
verification. Those guarantees require a separately reviewed signature or
provenance-verification mechanism, which this helper does not implement.

The root `.dockerignore` is intentionally a default-deny allowlist. It sends
only `backend/pyproject.toml`, `backend/uv.lock`, `backend/migrations/**`, and
the helper files copied by the rehearsal Dockerfile. It excludes `.env`, other
credentials, backups, dumps, application source, and unrelated repository
files from the Docker build context. Existing Compose files define no image
builds, so this policy does not change an existing build workflow. Any future
root-context build must be explicitly reviewed before widening the allowlist;
the build wrapper rejects any policy change until its own reviewed expected
allowlist is updated in the same change. The wrapper's exact-policy check and
static test protect against accidental context widening; reviewing a policy
change must also compare every Dockerfile `COPY` source with the allowlist.

## Required approval gates

1. Review and approve the target migration, restore provenance, clone-only
   role, and the two complete base-image identities. Provision the base roles
   in the allowlist only after recording the manual review evidence described
   above.
2. Explicitly approve building an untrusted candidate through `build.py`.
   Confirm the two independently verified base-image digests and review any
   requested change to the root Docker-context allowlist. Do not launch it.
3. Independently review and publish the candidate, resolve its published
   digest, and add that exact helper identity to the helper allowlist in a
   separately reviewed change. Only then may an operator provide that same
   digest as `REHEARSAL_HELPER_IMAGE` to the launcher.
4. Manually record and approve the restore container's full ID in
   `REHEARSAL_APPROVED_RESTORE_CONTAINER_ID`. Explicitly approve invoking the
   launcher, which will revalidate its exact name, running status,
   `network=none`, and zero published ports before it creates one disposable
   helper container. Confirm there is no writable database-volume mount and
   that the password source is a temporary read-only file. The approved restore
   container remains `network=none`; namespace sharing is the expected path to
   `127.0.0.1:5432` within that isolated namespace.
5. Explicitly approve Stage A only, inspect its redacted preflight report, and
   preserve its complete stdout in an approved outside-repository file. Stop
   unless it reports the expected source revision and required source tables.
6. Stop: this version intentionally refuses every `upgrade`. The helper image
   has no independently trusted signature/attestation verifier or pinned
   verifier public key. A human-supplied token, arbitrary artifact, or matching
   report digest is not authorization and is never accepted.
7. Before any future upgrade review, provision a separate trusted approval
   authority and immutable verifier public key outside the helper's control;
   specify a signed, canonical authorization payload binding the complete
   preflight report, approved restore-container ID, baseline, migration hashes,
   and intended target. Review and test that verifier in a separate change.

No build, container creation, connection, migration, or cleanup is performed
by this change.

## Verification evidence and residual risks

Preflight and postflight issue only fixed `SELECT` statements and are protected
by PostgreSQL read-only transaction defaults. The separate migration stage is
the only stage that can invoke Alembic. Before migration approval, preflight verifies the database
identity and that `alembic_version` contains exactly the one expected source
revision, verifies all five relevant source tables, and creates an in-memory
baseline for `users`, `projects`, `requirements`, `user_stories`, and
`user_story_approval_audits`.

For each baseline table, the helper includes every source-revision column,
including IDs, business data, timestamps, parent/actor relationships, and the
full approval-audit record. It excludes only the fixed migration's new columns
(`record_number` and, where applicable, `created_by_id`). Rows are ordered by
ID and represented with explicit type markers, so empty tables, NULL values,
JSON values, timestamps, and binary values produce deterministic SHA-256
table hashes. Any unsupported PostgreSQL value representation fails closed
instead of falling back to a potentially unstable string representation. The
postflight fails closed if a source column list, row count, or hash differs.
Reports contain only column names, counts, hashes, and booleans; they never
include rows, IDs, passwords, connection strings, SQL definitions, environment
contents, or child-process output.

Alembic's own fresh migration connection first compares the expected database
OID and PostgreSQL cluster system identifier captured immediately before
invocation. It refuses drift before Alembic configures or executes a migration;
endpoint strings alone are not treated as clone identity.

Postflight requires the target revision to be the only Alembic version and
requires every validation to pass. It validates each `record_number` column as
`varchar(32)` and non-null, the exact unique constraint attached to its table
and column, the exact bigint sequence properties created by the migration
(start, increment, minimum, maximum, cache, and non-cycling behavior), and
each enabled row-level trigger's table association, event/timing, and
condition. It uses `pg_proc`, `pg_get_functiondef()`, and the stored function
source to require the exact zero-argument public PL/pgSQL trigger signatures
and bodies from revision `d4e5f6a7b8c9`: explicit-value rejection, the
per-table prefix, `pg_catalog.lpad`, `pg_catalog.nextval` against that table's
public-qualified `pg_catalog.regclass` sequence, and the
record-number immutability exception. Trigger condition validation uses
`pg_get_expr(tgqual, tgrelid)`, not formatting-sensitive trigger-definition
text. It verifies prefix format, non-nullability, uniqueness, `created_at, id`
deterministic backfill order, and the effective next sequence value without
calling `nextval`, `setval`, or otherwise changing sequence state. It also
verifies each nullable creator UUID column, its non-unique valid index on the
correct table/column, and its validated foreign key from `created_by_id` to
`users(id)` with `ON DELETE SET NULL`. It also reads PostgreSQL catalogs to
require SECURITY INVOKER functions, exactly `search_path=pg_catalog`, and
function/table plus sequence/table owner alignment. It requires the explicitly
configured `REHEARSAL_RECORD_NUMBER_WRITER_ROLE` to be the reviewed writer role
and to have INSERT on every target table and USAGE on every sequence. This
assumes that role is the only supported record writer; unsupported role or
privilege models fail closed.

The Alembic environment passes the secret-bearing SQLAlchemy `URL` directly
to `create_engine`. It no longer renders that URL into Alembic configuration,
which avoids plaintext password propagation through that configuration path.
The runner suppresses Alembic subprocess output and replaces database,
configuration, migration, and unexpected failures with safe error categories
while retaining a non-zero exit status.

The target objects are `record_number` on `users`, `projects`,
`requirements`, and `user_stories`, including their sequences, unique
constraints, assignment triggers, and immutable update triggers. On
`projects`, `requirements`, and `user_stories`, they also include
`created_by_id`, its index, and its `ON DELETE SET NULL` foreign key to
`users(id)`.

The target migration takes table locks and changes the clone. This helper
cannot prove namespace isolation, the source secret's scope, image-digest
provenance, restore fidelity, host-to-container UID/GID mapping for the bind
mounted secret, or compatibility with a PostgreSQL version not represented by
the reviewed migration. It also cannot prove behavior for records written
after the snapshot or replace human review of the migration's SQL semantics.
The next single safe review action is a security-focused source review of the
helper, build wrapper, root `.dockerignore`, and this document; do not build,
connect, or run the helper until that review has explicit approval.
