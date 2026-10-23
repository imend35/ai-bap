# ADIM 8.10.100.8 — Registration Validation Root Cause & Targeted Fix

## Step Name and Objective

Identify the confirmed `validation:invalid_registration_details` cause in the isolated initial-administrator integration fixture and apply the smallest correction without weakening registration or password-security policy.

## Confirmed Validation Root Cause

`UserRegister` applies these relevant constraints:

- `email`: Pydantic `EmailStr` validation.
- `full_name`: string length from 2 through 160 characters.
- `password`: string length from 12 through 128 characters.

The integration fixture generated unique bootstrap addresses under the reserved `.test` top-level domain. A schema-only validation of the exact fixture shape reported only the `email` field with a generic value-validation classification. The full name and password shape were accepted by the same schema check.

Therefore the defect was an invalid **test fixture email domain**, not the environment adapter, registration schema, PostgreSQL integration, password policy, or account-creation security controls.

## Minimal Correction

- Changed only the generated isolated bootstrap-test email suffix from the reserved `.test` domain to the valid documentation domain `example.com`.
- Added a focused non-database regression test that validates the generated bootstrap email shape through the existing `validate_bootstrap_details()` / `UserRegister` path.

No production validation rule, password requirement, email normalization policy, Argon2id hashing, advisory lock, transaction handling, or existing-user protection was changed.

## Files Inspected or Modified

### Inspected

- `AGENTS.md`
- `backend/app/schemas/auth.py`
- `backend/app/initial_admin_bootstrap.py`
- `backend/tests/test_initial_admin_bootstrap_integration.py`
- `backend/tests/test_initial_admin_bootstrap.py`
- `backend/tests/test_bootstrap_admin.py`
- Relevant authentication and schema test references

### Modified

- `backend/tests/test_initial_admin_bootstrap_integration.py`
- `backend/tests/test_bootstrap_admin.py`
- `docs/codex-reports/adm_8.10.100.8.md`

All pre-existing working-tree changes were preserved.

## Regression Coverage

- The existing integration tests now construct UserRegister-compatible email addresses before invoking the environment bootstrap adapter.
- The added unit regression verifies that a generated isolated bootstrap fixture address is accepted by the existing validation operation.
- Existing tests continue to cover invalid email, short name, and short password rejection without weakening any constraint.

## Commands Executed and Results

| Command or check | Result |
| --- | --- |
| Source review of `UserRegister`, integration fixture, and adapter validation path | PASS — the email domain was the only fixture/schema mismatch. |
| Schema-only validation of the previous fixture shape | PASS — reported only the `email` field and a generic validation category; no fixture values or error details were output. |
| Schema-only validation of the corrected fixture shape | PASS — `UserRegister` accepted the payload shape. |
| `uv run --no-sync ruff check app/initial_admin_bootstrap.py scripts/bootstrap_admin.py tests/test_bootstrap_admin.py tests/test_initial_admin_bootstrap.py tests/test_initial_admin_bootstrap_integration.py ../docker/backend/bootstrap_initial_admin_from_environment.py` | PASS — `All checks passed!` |
| `python -m py_compile` for modified bootstrap and focused test modules | PASS — completed successfully with no output. |
| Guarded database integration tests | NOT RUN — all required isolated-test variables remain absent in the Codex process. |
| `git diff --check` before creating this report | PASS — no whitespace errors; only pre-existing line-ending warnings were emitted. |

## Security Checks

- No credential, token, password, personal-data value, password hash, database URL, or Pydantic exception detail was displayed.
- The fail-closed database guard is unchanged and was not bypassed.
- No database connection, migration, Docker operation, deployment, provisioning, commit, or push occurred.
- Existing registration and bootstrap security policies remain unchanged.

## Blockers and Remaining Tasks

The corrected integration suite has not run in this Codex process because the existing isolated test environment variables and test-only credentials are absent. End-to-end verification of first creation, repeat no-op, email-conflict preservation, concurrency, and login remains pending a guarded operator-side run.

No cost-bearing service or external resource was created or changed.

## Recommended Next Step

After securely restoring the documented existing isolated-test session, run from `backend`:

```powershell
uv run --no-sync pytest -q tests/test_initial_admin_bootstrap_integration.py tests/test_bootstrap_admin.py tests/test_initial_admin_bootstrap.py tests/test_auth_login_api.py tests/test_render_free_deployment_configuration.py
```

If the integration tests fail after this fixture correction, capture only the fixed safe diagnostic event and investigate that specific path without disclosing raw database errors.

## Final GO / NO-GO

**GO for guarded isolated integration verification.** The confirmed validation defect has a minimal fixture-only correction and static validation passes.

**NO-GO for deployment, commit, or push** until the corrected integration tests have passed in the documented isolated environment.
