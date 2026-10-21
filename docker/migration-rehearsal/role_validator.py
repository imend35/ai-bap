"""Fail-closed PostgreSQL 16 connection-role validation helpers.

This module deliberately depends only on a narrow catalog-query callback.  It
does not import database drivers, Alembic, or rehearsal entry points so that
the same validation can be used by both Psycopg and SQLAlchemy callers.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from typing import Any, Literal


CatalogQuery = Callable[[str, tuple[Any, ...]], Sequence[tuple[Any, ...]]]
Profile = Literal["reader", "migration"]

_ROLE_NAME = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")
_MAX_MEMBERSHIP_DEPTH = 32
_PROFILES = frozenset({"reader", "migration"})
_SYSTEM_SCHEMA_PREDICATE = "left(n.nspname, 3) = 'pg_' OR n.nspname = 'information_schema'"


class RoleValidationError(RuntimeError):
    """Represent a non-sensitive, fail-closed role-validation failure."""


_IDENTITY_SQL = """
WITH identities(identity_kind, role_name) AS (
    VALUES
        ('current_user'::text, current_user::text),
        ('session_user'::text, session_user::text)
)
SELECT
    identities.identity_kind,
    roles.oid,
    roles.rolname,
    roles.rolcanlogin,
    roles.rolsuper,
    roles.rolcreaterole,
    roles.rolcreatedb,
    roles.rolreplication,
    roles.rolbypassrls
FROM identities
LEFT JOIN pg_catalog.pg_roles AS roles
    ON roles.rolname = identities.role_name
ORDER BY identities.identity_kind
"""

_MEMBERSHIP_SQL = """
WITH RECURSIVE
roots AS (
    SELECT roles.oid
    FROM pg_catalog.pg_roles AS roles
    WHERE roles.rolname IN (session_user::text, current_user::text)
),
walk(role_oid, path, inherited_path, settable_path, final_edge_admin_option, depth) AS (
    SELECT
        roots.oid,
        ARRAY[roots.oid]::oid[],
        true,
        true,
        false,
        0
    FROM roots

    UNION ALL

    SELECT
        memberships.roleid,
        walk.path || memberships.roleid,
        walk.inherited_path AND memberships.inherit_option,
        walk.settable_path AND memberships.set_option,
        memberships.admin_option,
        walk.depth + 1
    FROM walk
    JOIN pg_catalog.pg_auth_members AS memberships
        ON memberships.member = walk.role_oid
    WHERE walk.depth < %s
      AND NOT memberships.roleid = ANY (walk.path)
),
graph_anomalies AS (
    SELECT
        EXISTS (
            SELECT 1
            FROM walk
            JOIN pg_catalog.pg_auth_members AS memberships
                ON memberships.member = walk.role_oid
            WHERE memberships.roleid = ANY (walk.path)
        ) AS cycle_detected,
        EXISTS (
            SELECT 1
            FROM walk
            JOIN pg_catalog.pg_auth_members AS memberships
                ON memberships.member = walk.role_oid
            WHERE walk.depth = %s
        ) AS depth_limit_reached
)
SELECT
    roles.oid,
    roles.rolname,
    roles.rolsuper,
    roles.rolcreaterole,
    roles.rolcreatedb,
    roles.rolreplication,
    roles.rolbypassrls,
    bool_or(walk.inherited_path) AS reachable_by_inheritance,
    bool_or(walk.settable_path) AS reachable_by_set_role,
    bool_or(walk.final_edge_admin_option) AS admin_option_on_direct_edge,
    (SELECT cycle_detected FROM graph_anomalies),
    (SELECT depth_limit_reached FROM graph_anomalies)
FROM walk
JOIN pg_catalog.pg_roles AS roles ON roles.oid = walk.role_oid
GROUP BY
    roles.oid,
    roles.rolname,
    roles.rolsuper,
    roles.rolcreaterole,
    roles.rolcreatedb,
    roles.rolreplication,
    roles.rolbypassrls
ORDER BY roles.oid
"""

_OWNERSHIP_SQL = f"""
SELECT
    EXISTS (
        SELECT 1
        FROM pg_catalog.pg_database AS database
        WHERE database.datdba = %s::oid
    ) AS owns_database,
    EXISTS (
        SELECT 1
        FROM pg_catalog.pg_namespace AS n
        WHERE n.nspowner = %s::oid
          AND NOT ({_SYSTEM_SCHEMA_PREDICATE})
    ) AS owns_user_schema,
    EXISTS (
        SELECT 1
        FROM pg_catalog.pg_class AS relation
        JOIN pg_catalog.pg_namespace AS n ON n.oid = relation.relnamespace
        WHERE relation.relowner = %s::oid
          AND NOT ({_SYSTEM_SCHEMA_PREDICATE})
          AND relation.relkind IN ('r', 'p', 'S', 'v', 'm', 'f')
    ) AS owns_user_relation,
    EXISTS (
        SELECT 1
        FROM pg_catalog.pg_proc AS procedure
        JOIN pg_catalog.pg_namespace AS n ON n.oid = procedure.pronamespace
        WHERE procedure.proowner = %s::oid
          AND NOT ({_SYSTEM_SCHEMA_PREDICATE})
    ) AS owns_user_function,
    EXISTS (
        SELECT 1
        FROM pg_catalog.pg_type AS type_entry
        JOIN pg_catalog.pg_namespace AS n ON n.oid = type_entry.typnamespace
        WHERE type_entry.typowner = %s::oid
          AND NOT ({_SYSTEM_SCHEMA_PREDICATE})
    ) AS owns_user_type,
    EXISTS (
        SELECT 1
        FROM pg_catalog.pg_extension AS extension
        WHERE extension.extowner = %s::oid
    ) AS owns_extension,
    EXISTS (
        SELECT 1
        FROM pg_catalog.pg_foreign_data_wrapper AS wrapper
        WHERE wrapper.fdwowner = %s::oid
    ) AS owns_foreign_data_wrapper,
    EXISTS (
        SELECT 1
        FROM pg_catalog.pg_foreign_server AS server
        WHERE server.srvowner = %s::oid
    ) AS owns_foreign_server
"""

_READER_PRIVILEGES_SQL = f"""
SELECT
    has_database_privilege(%s::oid, current_database(), 'CREATE')
        AS database_create,
    has_database_privilege(%s::oid, current_database(), 'TEMP')
        AS database_temp,
    EXISTS (
        SELECT 1
        FROM pg_catalog.pg_namespace AS n
        WHERE NOT ({_SYSTEM_SCHEMA_PREDICATE})
          AND has_schema_privilege(%s::oid, n.oid, 'CREATE')
    ) AS schema_create,
    EXISTS (
        SELECT 1
        FROM pg_catalog.pg_class AS relation
        JOIN pg_catalog.pg_namespace AS n ON n.oid = relation.relnamespace
        WHERE NOT ({_SYSTEM_SCHEMA_PREDICATE})
          AND relation.relkind IN ('r', 'p', 'v', 'f')
          AND (
              has_table_privilege(%s::oid, relation.oid, 'INSERT')
              OR has_table_privilege(%s::oid, relation.oid, 'UPDATE')
              OR has_table_privilege(%s::oid, relation.oid, 'DELETE')
              OR has_table_privilege(%s::oid, relation.oid, 'TRUNCATE')
              OR has_table_privilege(%s::oid, relation.oid, 'TRIGGER')
          )
    ) AS table_write,
    EXISTS (
        SELECT 1
        FROM pg_catalog.pg_class AS relation
        JOIN pg_catalog.pg_namespace AS n ON n.oid = relation.relnamespace
        WHERE NOT ({_SYSTEM_SCHEMA_PREDICATE})
          AND relation.relkind = 'S'
          AND (
              has_sequence_privilege(%s::oid, relation.oid, 'USAGE')
              OR has_sequence_privilege(%s::oid, relation.oid, 'UPDATE')
          )
    ) AS sequence_write
"""


def _fail() -> RoleValidationError:
    """Return the sole public failure category without sensitive details."""
    return RoleValidationError("connection_role_validation_failed")


def _query(
    query: CatalogQuery, statement: str, parameters: tuple[Any, ...] = ()
) -> Sequence[tuple[Any, ...]]:
    """Invoke a caller-owned parameterized query and reject malformed results."""
    try:
        rows = query(statement, parameters)
    except Exception:
        # Raise after the exception handler so no driver exception is retained
        # as this safe error's cause or context.
        failed = True
        rows: Sequence[tuple[Any, ...]] = ()
    else:
        failed = False
    if failed:
        raise _fail()
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise _fail()
    if any(not isinstance(row, tuple) for row in rows):
        raise _fail()
    return rows


def _is_oid(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_boolean(value: Any) -> bool:
    return isinstance(value, bool)


def _validate_expected_role(expected_login_role: str) -> None:
    if not isinstance(expected_login_role, str) or _ROLE_NAME.fullmatch(expected_login_role) is None:
        raise _fail()


def _validate_identity(query: CatalogQuery, expected_login_role: str) -> int:
    rows = _query(query, _IDENTITY_SQL)
    if len(rows) != 2:
        raise _fail()

    expected_kinds = {"current_user", "session_user"}
    identities: dict[str, int] = {}
    for row in rows:
        if len(row) != 9:
            raise _fail()
        kind, oid, name, can_login, *attributes = row
        if (
            not isinstance(kind, str)
            or kind not in expected_kinds
            or kind in identities
            or not _is_oid(oid)
            or name != expected_login_role
            or can_login is not True
            or len(attributes) != 5
            or any(not _is_boolean(value) for value in attributes)
            or any(attributes)
        ):
            raise _fail()
        identities[kind] = oid

    if set(identities) != expected_kinds or len(set(identities.values())) != 1:
        raise _fail()
    return identities["session_user"]


def _validate_memberships(query: CatalogQuery, expected_oid: int) -> tuple[int, ...]:
    rows = _query(query, _MEMBERSHIP_SQL, (_MAX_MEMBERSHIP_DEPTH, _MAX_MEMBERSHIP_DEPTH))
    if not rows:
        raise _fail()

    reachable: list[int] = []
    seen: set[int] = set()
    cycle_detected: bool | None = None
    depth_limit_reached: bool | None = None
    for row in rows:
        if len(row) != 12:
            raise _fail()
        (
            oid,
            name,
            is_superuser,
            can_create_role,
            can_create_database,
            can_replicate,
            can_bypass_rls,
            inherited_path,
            settable_path,
            direct_edge_admin_option,
            row_cycle_detected,
            row_depth_limit_reached,
        ) = row
        booleans = (
            is_superuser,
            can_create_role,
            can_create_database,
            can_replicate,
            can_bypass_rls,
            inherited_path,
            settable_path,
            direct_edge_admin_option,
            row_cycle_detected,
            row_depth_limit_reached,
        )
        if (
            not _is_oid(oid)
            or not isinstance(name, str)
            or not name
            or oid in seen
            or any(not _is_boolean(value) for value in booleans)
        ):
            raise _fail()
        if cycle_detected is None:
            cycle_detected = row_cycle_detected
            depth_limit_reached = row_depth_limit_reached
        elif (
            cycle_detected != row_cycle_detected
            or depth_limit_reached != row_depth_limit_reached
        ):
            raise _fail()

        # PostgreSQL 16's per-edge inheritance and SET options are retrieved
        # for diagnostics, but they never relax this fail-closed decision.
        # admin_option is intentionally not treated as a generic transitive
        # capability: it applies to the direct edge that granted a role.
        if (
            is_superuser
            or can_create_role
            or can_create_database
            or can_replicate
            or can_bypass_rls
            or name.startswith("pg_")
        ):
            raise _fail()
        seen.add(oid)
        reachable.append(oid)

    if (
        expected_oid not in seen
        or cycle_detected is not False
        or depth_limit_reached is not False
    ):
        raise _fail()
    return tuple(reachable)


def _validate_reader_boundary(query: CatalogQuery, reachable_role_oids: tuple[int, ...]) -> None:
    """Reject direct writes; indirect writes require role provisioning and runtime review.

    PostgreSQL 16 ownership checks cover databases, non-system schemas,
    relations, functions, types, extensions, foreign data wrappers, and
    foreign servers.  They do not establish safety for every mutable catalog
    class, large objects, or indirect writes through executable objects.
    """
    for role_oid in reachable_role_oids:
        ownership_rows = _query(
            query,
            _OWNERSHIP_SQL,
            (
                role_oid,
                role_oid,
                role_oid,
                role_oid,
                role_oid,
                role_oid,
                role_oid,
                role_oid,
            ),
        )
        if len(ownership_rows) != 1 or len(ownership_rows[0]) != 8:
            raise _fail()
        if any(value is not False for value in ownership_rows[0]):
            raise _fail()

        privilege_rows = _query(
            query,
            _READER_PRIVILEGES_SQL,
            (role_oid, role_oid, role_oid, role_oid, role_oid, role_oid),
        )
        if len(privilege_rows) != 1 or len(privilege_rows[0]) != 5:
            raise _fail()
        if any(value is not False for value in privilege_rows[0]):
            raise _fail()


def validate_connection_role(
    query: CatalogQuery,
    *,
    expected_login_role: str,
    profile: Profile,
) -> None:
    """Validate a PostgreSQL 16 connection role with fail-closed catalog checks.

    The supplied callback must execute only the provided parameterized SQL and
    return tuples in column order.  ``reader`` rejects detected direct object
    ownership and write privileges.  ``migration`` applies no reader-only
    ownership or write restriction, but receives all identity and membership
    safeguards.

    These catalog checks cannot prove the absence of indirect writes through
    functions, triggers, rules, foreign data wrappers, or extensions.  Those
    controls must be supplied through PostgreSQL role and object provisioning.
    """
    if profile not in _PROFILES:
        raise _fail()
    _validate_expected_role(expected_login_role)
    expected_oid = _validate_identity(query, expected_login_role)
    reachable_role_oids = _validate_memberships(query, expected_oid)
    if profile == "reader":
        _validate_reader_boundary(query, reachable_role_oids)


__all__ = ["RoleValidationError", "validate_connection_role"]
