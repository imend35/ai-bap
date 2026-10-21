"""Offline unit tests for the standalone PostgreSQL 16 role validator."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from typing import Any, Sequence


VALIDATOR_PATH = Path(__file__).resolve().parents[1] / "role_validator.py"
SPEC = importlib.util.spec_from_file_location("rehearsal_role_validator", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
ROLE_VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ROLE_VALIDATOR)


def identity_rows(
    expected_role: str = "reader_role",
    *,
    current_role: str | None = None,
    session_role: str | None = None,
    oid: int = 101,
    current_oid: int | None = None,
    session_oid: int | None = None,
    can_login: bool = True,
    attributes: tuple[bool, bool, bool, bool, bool] = (False, False, False, False, False),
) -> list[tuple[Any, ...]]:
    """Return identity rows in the exact PostgreSQL catalog-query shape."""
    return [
        ("current_user", current_oid or oid, current_role or expected_role, can_login, *attributes),
        ("session_user", session_oid or oid, session_role or expected_role, can_login, *attributes),
    ]


def membership_row(
    oid: int = 101,
    name: str = "reader_role",
    *,
    attributes: tuple[bool, bool, bool, bool, bool] = (False, False, False, False, False),
    inherited: bool = True,
    settable: bool = True,
    direct_admin: bool = False,
    cycle: bool = False,
    depth_limit: bool = False,
) -> tuple[Any, ...]:
    """Return one grouped recursive-membership result row."""
    return (
        oid,
        name,
        *attributes,
        inherited,
        settable,
        direct_admin,
        cycle,
        depth_limit,
    )


class CatalogQuery:
    """Deterministic in-memory replacement for the validator's query callback."""

    def __init__(
        self,
        *,
        identities: Sequence[tuple[Any, ...]] | object = None,
        memberships: Sequence[tuple[Any, ...]] | object = None,
        ownership: Sequence[tuple[Any, ...]] | object = None,
        privileges: Sequence[tuple[Any, ...]] | object = None,
    ) -> None:
        self.identities = identity_rows() if identities is None else identities
        self.memberships = [membership_row()] if memberships is None else memberships
        self.ownership = [(False, False, False, False, False, False, False, False)] if ownership is None else ownership
        self.privileges = [(False, False, False, False, False)] if privileges is None else privileges
        self.calls: list[tuple[str, tuple[Any, ...]]] = []

    def __call__(self, statement: str, parameters: tuple[Any, ...]) -> Sequence[tuple[Any, ...]]:
        self.calls.append((statement, parameters))
        if statement == ROLE_VALIDATOR._IDENTITY_SQL:
            return self.identities  # type: ignore[return-value]
        if statement == ROLE_VALIDATOR._MEMBERSHIP_SQL:
            return self.memberships  # type: ignore[return-value]
        if statement == ROLE_VALIDATOR._OWNERSHIP_SQL:
            return self.ownership  # type: ignore[return-value]
        if statement == ROLE_VALIDATOR._READER_PRIVILEGES_SQL:
            return self.privileges  # type: ignore[return-value]
        raise AssertionError("unexpected static catalog query")


class RoleValidatorTests(unittest.TestCase):
    """Exercise only mocked PostgreSQL 16 catalog-query responses."""

    def validate(self, catalog: CatalogQuery, *, profile: str = "reader") -> None:
        ROLE_VALIDATOR.validate_connection_role(
            catalog,
            expected_login_role="reader_role",
            profile=profile,
        )

    def assert_rejected(self, catalog: CatalogQuery, *, profile: str = "reader") -> None:
        with self.assertRaisesRegex(
            ROLE_VALIDATOR.RoleValidationError,
            r"^connection_role_validation_failed$",
        ):
            self.validate(catalog, profile=profile)

    def test_valid_reader_identity_and_restrictions_are_accepted(self) -> None:
        catalog = CatalogQuery()

        self.validate(catalog)

        self.assertEqual(len(catalog.calls), 4)

    def test_valid_migration_identity_skips_reader_only_queries(self) -> None:
        catalog = CatalogQuery()

        self.validate(catalog, profile="migration")

        self.assertEqual(
            [statement for statement, _ in catalog.calls],
            [ROLE_VALIDATOR._IDENTITY_SQL, ROLE_VALIDATOR._MEMBERSHIP_SQL],
        )

    def test_session_user_and_current_user_mismatches_are_rejected(self) -> None:
        for current_role, session_role in (
            ("other_role", "reader_role"),
            ("reader_role", "other_role"),
            ("other_role", "another_role"),
        ):
            with self.subTest(current_role=current_role, session_role=session_role):
                self.assert_rejected(
                    CatalogQuery(
                        identities=identity_rows(
                            current_role=current_role,
                            session_role=session_role,
                        )
                    )
                )

    def test_expected_login_role_requires_login_and_a_matching_oid(self) -> None:
        self.assert_rejected(CatalogQuery(identities=identity_rows(can_login=False)))
        self.assert_rejected(
            CatalogQuery(identities=identity_rows(current_oid=101, session_oid=202))
        )

    def test_each_prohibited_direct_role_attribute_is_rejected(self) -> None:
        attributes = ("SUPERUSER", "CREATEROLE", "CREATEDB", "REPLICATION", "BYPASSRLS")
        for index, name in enumerate(attributes):
            flags = [False] * 5
            flags[index] = True
            with self.subTest(attribute=name):
                self.assert_rejected(CatalogQuery(identities=identity_rows(attributes=tuple(flags))))

    def test_each_prohibited_reachable_ordinary_role_attribute_is_rejected(self) -> None:
        attributes = ("SUPERUSER", "CREATEROLE", "CREATEDB", "REPLICATION", "BYPASSRLS")
        for index, name in enumerate(attributes):
            flags = [False] * 5
            flags[index] = True
            with self.subTest(attribute=name):
                self.assert_rejected(
                    CatalogQuery(
                        memberships=[
                            membership_row(),
                            membership_row(202, "ordinary_group", attributes=tuple(flags)),
                        ]
                    )
                )

    def test_direct_dangerous_predefined_membership_is_rejected(self) -> None:
        self.assert_rejected(
            CatalogQuery(
                memberships=[
                    membership_row(),
                    membership_row(202, "pg_read_all_data", inherited=True, settable=True),
                ]
            )
        )

    def test_nested_dangerous_membership_is_rejected(self) -> None:
        self.assert_rejected(
            CatalogQuery(
                memberships=[
                    membership_row(),
                    membership_row(202, "analyst_group", inherited=True, settable=True),
                    membership_row(303, "pg_write_all_data", inherited=True, settable=True),
                ]
            )
        )

    def test_postgresql_16_membership_options_are_present_and_safe_paths_are_accepted(self) -> None:
        self.assertIn("memberships.inherit_option", ROLE_VALIDATOR._MEMBERSHIP_SQL)
        self.assertIn("memberships.set_option", ROLE_VALIDATOR._MEMBERSHIP_SQL)
        self.assertIn("memberships.admin_option", ROLE_VALIDATOR._MEMBERSHIP_SQL)

        self.validate(
            CatalogQuery(
                memberships=[
                    membership_row(),
                    membership_row(
                        202,
                        "ordinary_group",
                        inherited=False,
                        settable=False,
                        direct_admin=True,
                    ),
                ]
            )
        )

    def test_system_schema_predicate_uses_an_exact_pg_underscore_prefix(self) -> None:
        self.assertIn("left(n.nspname, 3) = 'pg_'", ROLE_VALIDATOR._SYSTEM_SCHEMA_PREDICATE)
        self.assertIn("n.nspname = 'information_schema'", ROLE_VALIDATOR._SYSTEM_SCHEMA_PREDICATE)
        self.assertNotIn("LIKE 'pg_%'", ROLE_VALIDATOR._SYSTEM_SCHEMA_PREDICATE)

    def test_reader_privilege_sql_covers_views_and_foreign_tables_not_materialized_views(self) -> None:
        self.assertIn("relation.relkind IN ('r', 'p', 'v', 'f')", ROLE_VALIDATOR._READER_PRIVILEGES_SQL)
        self.assertNotIn("relation.relkind IN ('r', 'p', 'v', 'm', 'f')", ROLE_VALIDATOR._READER_PRIVILEGES_SQL)
        self.assertIn("relation.relkind IN ('r', 'p', 'S', 'v', 'm', 'f')", ROLE_VALIDATOR._OWNERSHIP_SQL)

        for relation_kind in ("view", "foreign_table"):
            with self.subTest(relation_kind=relation_kind):
                self.assert_rejected(
                    CatalogQuery(privileges=[(False, False, False, True, False)])
                )

    def test_dangerous_membership_without_inheritance_or_set_role_is_rejected(self) -> None:
        self.assert_rejected(
            CatalogQuery(
                memberships=[
                    membership_row(),
                    membership_row(
                        202,
                        "pg_signal_backend",
                        inherited=False,
                        settable=False,
                        direct_admin=False,
                    ),
                ]
            )
        )

    def test_dangerous_membership_with_direct_admin_option_is_rejected(self) -> None:
        self.assert_rejected(
            CatalogQuery(
                memberships=[
                    membership_row(),
                    membership_row(
                        202,
                        "pg_execute_server_program",
                        inherited=False,
                        settable=False,
                        direct_admin=True,
                    ),
                ]
            )
        )

    def test_membership_cycle_and_depth_exhaustion_are_rejected(self) -> None:
        for cycle, depth_limit in ((True, False), (False, True)):
            with self.subTest(cycle=cycle, depth_limit=depth_limit):
                self.assert_rejected(
                    CatalogQuery(memberships=[membership_row(cycle=cycle, depth_limit=depth_limit)])
                )

    def test_missing_malformed_duplicate_and_unexpected_catalog_results_are_rejected(self) -> None:
        cases: tuple[tuple[str, CatalogQuery], ...] = (
            ("missing_identity", CatalogQuery(identities=[])),
            ("malformed_identity", CatalogQuery(identities=[("current_user",)])),
            ("missing_membership", CatalogQuery(memberships=[])),
            ("malformed_membership", CatalogQuery(memberships=[("bad",)])),
            (
                "duplicate_membership",
                CatalogQuery(memberships=[membership_row(), membership_row()]),
            ),
            ("unexpected_result_type", CatalogQuery(memberships="not-a-row-sequence")),
        )
        for name, catalog in cases:
            with self.subTest(case=name):
                self.assert_rejected(catalog)

    def test_reader_ownership_restrictions_are_enforced(self) -> None:
        ownerships = (
            "database",
            "schema",
            "relation",
            "function",
            "type",
            "extension",
            "foreign_data_wrapper",
            "foreign_server",
        )
        for index, ownership in enumerate(ownerships):
            values = [False] * 8
            values[index] = True
            with self.subTest(ownership=ownership):
                self.assert_rejected(CatalogQuery(ownership=[tuple(values)]))

    def test_reader_database_schema_create_and_temp_privileges_are_rejected(self) -> None:
        privileges = ("database_create", "database_temp", "schema_create")
        for index, privilege in enumerate(privileges):
            values = [False] * 5
            values[index] = True
            with self.subTest(privilege=privilege):
                self.assert_rejected(CatalogQuery(privileges=[tuple(values)]))

    def test_reader_table_write_trigger_and_sequence_usage_or_update_are_rejected(self) -> None:
        self.assertIn("has_table_privilege(%s::oid, relation.oid, 'TRIGGER')", ROLE_VALIDATOR._READER_PRIVILEGES_SQL)
        for index, privilege in (
            (3, "table_write"),
            (3, "table_trigger"),
            (4, "sequence_usage_or_update"),
        ):
            values = [False] * 5
            values[index] = True
            with self.subTest(privilege=privilege):
                self.assert_rejected(CatalogQuery(privileges=[tuple(values)]))

    def test_migration_profile_does_not_apply_reader_ownership_or_write_restrictions(self) -> None:
        catalog = CatalogQuery(
            ownership=[(True, True, True, True, True, True, True, True)],
            privileges=[(True, True, True, True, True)],
        )

        self.validate(catalog, profile="migration")

    def test_catalog_query_failures_fail_closed_without_sensitive_output(self) -> None:
        def failing_query(_: str, __: tuple[Any, ...]) -> Sequence[tuple[Any, ...]]:
            raise RuntimeError("postgresql://reader:secret@database.invalid/rehearsal")

        with self.assertRaises(ROLE_VALIDATOR.RoleValidationError) as raised:
            ROLE_VALIDATOR.validate_connection_role(
                failing_query,
                expected_login_role="reader_role",
                profile="reader",
            )

        self.assertEqual(str(raised.exception), "connection_role_validation_failed")
        self.assertNotIn("secret", str(raised.exception))
        self.assertNotIn("postgresql", str(raised.exception))
        self.assertIsNone(raised.exception.__cause__)
        self.assertIsNone(raised.exception.__context__)

    def test_invalid_profile_and_expected_role_fail_closed(self) -> None:
        self.assert_rejected(CatalogQuery(), profile="writer")
        with self.assertRaisesRegex(
            ROLE_VALIDATOR.RoleValidationError,
            r"^connection_role_validation_failed$",
        ):
            ROLE_VALIDATOR.validate_connection_role(
                CatalogQuery(),
                expected_login_role="quoted role",
                profile="reader",
            )


if __name__ == "__main__":
    unittest.main()
