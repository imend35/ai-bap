# Initial Administrator Bootstrap

I use the bootstrap command only to establish the first active administrator
for an environment that does not already have one. It is intentionally a local,
interactive operation and is not an HTTP endpoint.

From the `backend` directory, I run:

```powershell
uv run python -m scripts.bootstrap_admin
```

The command prompts for an administrator email, full name, password, and
password confirmation. The password is collected with `getpass`, is never
accepted through command-line arguments, and is never printed. I provide only
the normal application configuration through my approved runtime environment;
I do not place credentials in source control or command history.

The command normalizes the email address, applies the existing registration
constraints, hashes the password with Argon2id, and creates an active `admin`
user. PostgreSQL assigns the immutable `USR-###` record number.

Before checking or inserting, the command acquires a transaction-scoped
PostgreSQL advisory lock. It refuses to create an account when either the email
already exists or any active administrator already exists. It does not reveal
existing user details, password hashes, tokens, or database error details.

I run this command deliberately and only after confirming the intended database
target. To verify bootstrap state without disclosing account data, I use a
boolean-only check equivalent to:

```sql
SELECT EXISTS (
  SELECT 1
  FROM users
  WHERE role = 'admin'
    AND is_active = true
) AS active_admin_exists;
```

This command does not replace the current public registration endpoint. That
endpoint remains unchanged until a later, explicitly approved phase.

## Render Free Startup Bootstrap

For the separate [`render.free.yaml`](../render.free.yaml) demonstration path,
I can establish the first administrator inside the API container without shell
access or public database connectivity. This is a one-time, operator-approved
startup action; it is not an HTTP endpoint and does not change the interactive
local command described above.

Before the approved first deployment only, I configure these values as
temporary Render environment variables:

- `AI_BAP_INITIAL_ADMIN_BOOTSTRAP_ENABLED=true`
- `AI_BAP_INITIAL_ADMIN_EMAIL`
- `AI_BAP_INITIAL_ADMIN_FULL_NAME`
- `AI_BAP_INITIAL_ADMIN_PASSWORD` (a Render secret from my password manager)

Only the exact lowercase value `true` enables this path. When enabled, all
three administrator details are required and are validated with the normal
registration rules. The startup sequence is migration, bootstrap, then API.
The bootstrap adapter reuses the existing Argon2id hashing, active-admin
advisory lock, and no-overwrite checks. It creates no account when an active
administrator already exists.

I never place those values in Git, `.env.example`, logs, browser requests, or
chat. After a successful first administrator creation, I remove **all four**
temporary values in the Render Dashboard and perform a controlled redeploy.
If enabled configuration is incomplete, invalid, conflicts with an existing
email, or encounters a database failure, startup exits nonzero and the API
does not start.
