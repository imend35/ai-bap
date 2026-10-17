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
