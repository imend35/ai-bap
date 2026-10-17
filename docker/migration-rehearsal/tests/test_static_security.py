"""Static-only checks for clone rehearsal safety controls."""

from __future__ import annotations

import ast
import importlib
import importlib.util
import os
import sys
import unittest
from unittest.mock import patch
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
REHEARSE = ROOT / "docker" / "migration-rehearsal" / "rehearse.py"
LAUNCHER = ROOT / "docker" / "migration-rehearsal" / "launch.py"
ALEMBIC_ENV = ROOT / "docker" / "migration-rehearsal" / "env.py"
BUILD = ROOT / "docker" / "migration-rehearsal" / "build.py"
DOCKERFILE = ROOT / "docker" / "migration-rehearsal" / "Dockerfile"
DOCKERIGNORE = ROOT / ".dockerignore"
MIGRATION = ROOT / "backend" / "migrations" / "versions" / "c7a8d9e0f1b2_add_readable_record_numbers_and_creators.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sys.path.insert(0, str(ROOT / "docker" / "migration-rehearsal"))
IMAGE_POLICY = importlib.import_module("image_policy")
BUILD_MODULE = load_module("rehearsal_build", BUILD)
LAUNCH_MODULE = load_module("rehearsal_launch", LAUNCHER)
RUNNER_MODULE = load_module("rehearsal_runner", REHEARSE)


def forged_approval(*, binding_sha256: str = "a" * 64) -> dict[str, Any]:
    """Return a structurally plausible artifact that has no trusted signature."""
    return {
        "binding_sha256": binding_sha256,
        "restore_container_id_sha256": "b" * 64,
        "run_id": "c" * 64,
        "version": 1,
    }


class RehearsalStaticSecurityTests(unittest.TestCase):
    """Use source inspection and isolated mocks; never invoke Docker, Alembic, or PostgreSQL."""

    def test_python_sources_parse(self) -> None:
        for path in (REHEARSE, LAUNCHER, ALEMBIC_ENV, BUILD, ROOT / "docker" / "migration-rehearsal" / "image_policy.py"):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def test_runner_uses_catalog_function_and_sequence_validation(self) -> None:
        source = REHEARSE.read_text(encoding="utf-8")
        self.assertIn("pg_get_functiondef(p.oid)", source)
        self.assertIn("p.prosrc", source)
        self.assertIn("s.seqincrement", source)
        self.assertIn("s.seqmin", source)
        self.assertIn("s.seqmax", source)
        self.assertIn("s.seqcache", source)
        self.assertIn("s.seqcycle", source)
        self.assertIn("CanonicalizationError", source)
        self.assertNotIn("pg_get_triggerdef", source)

    def test_function_expectations_match_the_fixed_migration_source(self) -> None:
        runner = REHEARSE.read_text(encoding="utf-8")
        migration = (ROOT / "backend" / "migrations" / "versions" / "d4e5f6a7b8c9_harden_record_number_trigger_functions.py").read_text(encoding="utf-8")
        for fragment in (
            "record_number is assigned by PostgreSQL",
            "SET search_path = pg_catalog",
            "pg_catalog.nextval('public.users_record_number_seq'::pg_catalog.regclass)",
            "pg_catalog.nextval('public.projects_record_number_seq'::pg_catalog.regclass)",
            "pg_catalog.nextval('public.requirements_record_number_seq'::pg_catalog.regclass)",
            "pg_catalog.nextval('public.user_stories_record_number_seq'::pg_catalog.regclass)",
        ):
            self.assertIn(fragment, migration)
        self.assertIn("HARDENED_ASSIGNMENT_BODY", runner)
        self.assertIn("IMMUTABILITY_BODY", runner)
        self.assertIn("p.proconfig = ARRAY['search_path=pg_catalog']", runner)
        self.assertIn("NOT p.prosecdef", runner)
        self.assertIn("p.proowner = table_relation.relowner", runner)
        self.assertIn("has_sequence_privilege", runner)
        self.assertNotIn("LPAD(nextval('{sequence}')", runner)
        self.assertIn("SEQUENCE_MAXIMUM = 9223372036854775807", runner)

    def test_runner_preserves_fixed_endpoint_and_revisions(self) -> None:
        source = REHEARSE.read_text(encoding="utf-8")
        self.assertIn('EXPECTED_ENDPOINT = ("127.0.0.1", "5432", "restore_check_db")', source)
        self.assertIn('EXPECTED_SOURCE_REVISION = "921eeafe8be6"', source)
        self.assertIn('TARGET_REVISION = "d4e5f6a7b8c9"', source)
        self.assertIn("preflight_report(connection, prerequisites, container_id)", source)
        self.assertIn("postflight_validation_failed", source)

    def test_preflight_verifies_source_schema_and_captures_deterministic_baseline(self) -> None:
        source = REHEARSE.read_text(encoding="utf-8")
        self.assertIn("revisions(connection) == (EXPECTED_SOURCE_REVISION,)", source)
        self.assertIn('INTEGRITY_TABLES = (*TABLES, "user_story_approval_audits")', source)
        self.assertIn('TABLES = ("users", "projects", "requirements", "user_stories")', source)
        self.assertIn("ORDER BY ordinal_position", source)
        self.assertIn("if not columns or \"id\" not in columns", source)
        self.assertIn('f"SELECT {quoted_columns} FROM public.{table} ORDER BY id"', source)
        self.assertIn("hashlib.sha256()", source)
        self.assertIn("len(canonical).to_bytes(8, \"big\")", source)
        self.assertIn("[normalize(value) for value in row]", source)
        self.assertIn('"columns": columns', source)
        self.assertIn('"row_count": len(table_rows)', source)
        self.assertIn('"sha256": digest.hexdigest()', source)

    def test_preflight_requires_reviewed_migration_chain_and_security_followup(self) -> None:
        source = REHEARSE.read_text(encoding="utf-8")
        self.assertIn("EXPECTED_MIGRATION_CHAIN", source)
        self.assertIn("d4e5f6a7b8c9_harden_record_number_trigger_functions.py", source)
        self.assertIn('and verified[-1][1] == "d4e5f6a7b8c9"', source)
        self.assertIn("hashlib.sha256(source).hexdigest() != expected_digest", source)
        self.assertIn("SECURITY_FOLLOWUP_FRAGMENTS", source)
        self.assertIn('"SET search_path = pg_catalog"', source)
        self.assertIn('"security_followup_intent": followup_intent_verified', source)
        self.assertIn('raise PreflightError("migration_prerequisite_failed")', source)

    def test_upgrade_refuses_forged_approval_artifacts_without_a_trusted_verifier(self) -> None:
        runner = REHEARSE.read_text(encoding="utf-8")
        launcher = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("def approval_binding_sha256(", runner)
        self.assertIn('"restore_container_id": container_id', runner)
        self.assertIn('"migration_file_hashes": migration_file_hashes()', runner)
        self.assertIn('"source_revision": EXPECTED_SOURCE_REVISION', runner)
        self.assertIn("restore_container_id_sha256", runner)
        self.assertIn("def verify_external_approval", runner)
        self.assertIn('raise RehearsalError("approval_verifier_unavailable")', runner)
        self.assertIn("verify_external_approval(approval)", runner)
        self.assertNotIn("APPROVAL_ARTIFACT_FILE", runner)
        self.assertNotIn("[A-Za-z0-9_-]{32,128}", runner)
        self.assertNotIn("REHEARSAL_APPROVAL_ARTIFACT_SOURCE", launcher)
        self.assertIn("REHEARSAL_RESTORE_CONTAINER_ID", launcher)
        self.assertNotIn("print(password", runner)
        self.assertNotIn("print(table_rows", runner)
        self.assertNotIn("print(kwargs", runner)

    def test_run_upgrade_stops_before_database_or_alembic_for_forged_approval(self) -> None:
        """An artifact-shaped approval cannot reach any upgrade side effect."""
        baseline = {
            "users": {
                "columns": ("id", "created_at"),
                "row_count": 1,
                "sha256": "d" * 64,
            }
        }
        with (
            patch.object(RUNNER_MODULE, "load_preflight_report", return_value=(baseline, forged_approval())),
            patch.object(RUNNER_MODULE.psycopg, "connect") as connect,
            patch.object(RUNNER_MODULE.subprocess, "run") as subprocess_run,
            self.assertRaisesRegex(RUNNER_MODULE.RehearsalError, "^approval_verifier_unavailable$"),
        ):
            RUNNER_MODULE.run_upgrade()
        connect.assert_not_called()
        subprocess_run.assert_not_called()

    def test_external_approval_verifier_rejects_forged_objects_with_matching_digests(self) -> None:
        """Digests bind preflight evidence but cannot serve as external authorization."""
        matching_digest = RUNNER_MODULE.approval_binding_sha256(
            "a" * 64,
            "c" * 64,
            {
                "users": {
                    "columns": ("id", "created_at"),
                    "row_count": 1,
                    "sha256": "d" * 64,
                }
            },
        )
        matching_approval = {
            "binding_sha256": matching_digest,
            "restore_container_id_sha256": RUNNER_MODULE.hashlib.sha256(
                ("a" * 64).encode("ascii")
            ).hexdigest(),
            "run_id": "c" * 64,
            "version": 1,
        }
        forged_objects = (
            forged_approval(),
            matching_approval,
            {
                **matching_approval,
                "run_id": "e" * 64,
            },
        )
        for approval in forged_objects:
            with self.subTest(approval=approval):
                with self.assertRaisesRegex(
                    RUNNER_MODULE.RehearsalError, "^approval_verifier_unavailable$"
                ):
                    RUNNER_MODULE.verify_external_approval(approval)

    def test_stages_are_explicit_and_validation_stages_are_read_only(self) -> None:
        source = REHEARSE.read_text(encoding="utf-8")
        tree = ast.parse(source)
        functions = {
            node.name: node
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }
        self.assertIn('sys.argv[1] not in {"preflight", "upgrade"}', source)
        self.assertIn('kwargs["options"] = "-c default_transaction_read_only=on"', source)
        self.assertIn("PREFLIGHT_REPORT_FILE", source)
        self.assertIn("load_preflight_report", source)
        for name in ("run_preflight",):
            body = ast.unparse(functions[name])
            self.assertNotIn("subprocess", body)
            self.assertNotIn("alembic", body.lower())
            self.assertIn("read_only=True", body)
        migration_body = ast.unparse(functions["run_upgrade"])
        self.assertIn('["alembic", "-c", ALEMBIC_CONFIG, "upgrade", TARGET_REVISION]', source)
        self.assertIn("approval_stale_or_target_drift", migration_body)

    def test_upgrade_verifies_external_approval_before_alembic_subprocess(self) -> None:
        """The approval gate must syntactically precede the Alembic process call."""
        tree = ast.parse(REHEARSE.read_text(encoding="utf-8"), filename=str(REHEARSE))
        run_upgrade = next(
            node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run_upgrade"
        )
        approval_call = next(
            statement.value
            for statement in run_upgrade.body
            if isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Call)
            and isinstance(statement.value.func, ast.Name)
            and statement.value.func.id == "verify_external_approval"
        )
        alembic_calls = [
            call
            for call in ast.walk(run_upgrade)
            if isinstance(call, ast.Call)
            and isinstance(call.func, ast.Attribute)
            and isinstance(call.func.value, ast.Name)
            and call.func.value.id == "subprocess"
            and call.func.attr == "run"
            and call.args
            and isinstance(call.args[0], ast.List)
            and call.args[0].elts
            and isinstance(call.args[0].elts[0], ast.Constant)
            and call.args[0].elts[0].value == "alembic"
        ]
        self.assertEqual(len(alembic_calls), 1)
        self.assertLess(approval_call.lineno, alembic_calls[0].lineno)

    def test_launcher_requires_a_stage_and_upgrade_inputs_only(self) -> None:
        source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn('sys.argv[1] not in {"preflight", "upgrade"}', source)
        self.assertIn('if stage == "upgrade":', source)
        self.assertIn("REHEARSAL_PREFLIGHT_REPORT_SOURCE", source)
        self.assertIn("PREFLIGHT_REPORT_TARGET", source)
        self.assertIn("REHEARSAL_RECORD_NUMBER_WRITER_ROLE", source)
        self.assertIn("image, stage", source)

    def test_launcher_verifies_restore_identity_isolation_and_fixed_endpoint(self) -> None:
        launcher = LAUNCHER.read_text(encoding="utf-8")
        runner = REHEARSE.read_text(encoding="utf-8")
        self.assertIn("FULL_CONTAINER_ID.fullmatch(container_id)", launcher)
        self.assertIn('restore.get("Id") != container_id', launcher)
        self.assertIn('restore.get("Name") != f"/{APPROVED_RESTORE_NAME}"', launcher)
        self.assertIn('restore.get("State", {}).get("Running") is not True', launcher)
        self.assertIn('restore.get("HostConfig", {}).get("NetworkMode") != "none"', launcher)
        self.assertIn('restore.get("HostConfig", {}).get("PortBindings")', launcher)
        self.assertIn('restore.get("NetworkSettings", {}).get("Ports")', launcher)
        self.assertIn("if endpoint != EXPECTED_ENDPOINT", launcher)
        self.assertIn("SELECT current_database() = %s AND inet_server_addr() = %s::inet", runner)
        self.assertIn("AND inet_server_port() = %s", runner)

    def test_alembic_connection_rechecks_clone_identity_before_ddl(self) -> None:
        runner = REHEARSE.read_text(encoding="utf-8")
        env = ALEMBIC_ENV.read_text(encoding="utf-8")
        self.assertIn("def alembic_identity_environment", runner)
        self.assertIn("(pg_control_system()).system_identifier::text", runner)
        self.assertIn('"REHEARSAL_EXPECTED_DATABASE_OID"', runner)
        self.assertIn('"REHEARSAL_EXPECTED_SYSTEM_IDENTIFIER"', runner)
        self.assertIn("def assert_clone_identity", env)
        self.assertIn("clone_identity_drift", env)
        self.assertIn("assert_clone_identity(connection)", env)
        self.assertLess(env.index("assert_clone_identity(connection)"), env.index("context.configure"))

    def test_docker_controls_are_non_root_and_allowlisted(self) -> None:
        dockerfile = DOCKERFILE.read_text(encoding="utf-8")
        self.assertIn("USER 10001:10001", dockerfile)
        self.assertIn("/run/rehearsal", dockerfile)
        ignore = DOCKERIGNORE.read_text(encoding="utf-8")
        self.assertIn("**", ignore)
        self.assertIn("!backend/migrations/**", ignore)
        self.assertNotIn("!.env", ignore)

    def test_build_and_launcher_redact_subprocess_output(self) -> None:
        build_source = BUILD.read_text(encoding="utf-8")
        launcher_source = LAUNCHER.read_text(encoding="utf-8")
        self.assertIn("trusted_image_reference", build_source)
        self.assertIn("REHEARSAL_CANDIDATE_HELPER_IMAGE_TAG", build_source)
        self.assertNotIn("require_role_approval", build_source)
        self.assertNotIn("REHEARSAL_HELPER_IMAGE_TAG\"),", build_source)
        self.assertIn("validate_context_policy", build_source)
        self.assertIn("EXPECTED_DOCKERIGNORE", build_source)
        self.assertIn("capture_output=True", build_source)
        self.assertIn("capture_output=True", launcher_source)
        self.assertNotIn("subprocess.CalledProcessError", launcher_source)
        self.assertIn("LauncherError(\"helper_container_failed\")", launcher_source)

    def test_image_policy_rejects_malformed_unapproved_and_wrong_repository_identities(self) -> None:
        reviewed = "registry.example/rehearsal/python@sha256:" + "a" * 64
        wrong_repository = "registry.example/other/python@sha256:" + "a" * 64
        with patch.object(IMAGE_POLICY, "REVIEWED_IMAGE_ALLOWLIST", {"python_base": frozenset({reviewed}), "uv": frozenset(), "helper": frozenset()}):
            with self.assertRaisesRegex(IMAGE_POLICY.ImagePolicyError, "image_reference_error"):
                IMAGE_POLICY.trusted_image_reference("registry.example/rehearsal/python:3.13", "python_base")
            with self.assertRaisesRegex(IMAGE_POLICY.ImagePolicyError, "image_reference_error"):
                IMAGE_POLICY.trusted_image_reference("registry.example/rehearsal/python@sha256:" + "A" * 64, "python_base")
            with self.assertRaisesRegex(IMAGE_POLICY.ImagePolicyError, "image_reference_error"):
                IMAGE_POLICY.trusted_image_reference("registry.example/rehearsal/python@sha256:" + "0" * 64, "python_base")
            with self.assertRaisesRegex(IMAGE_POLICY.ImagePolicyError, "image_not_approved"):
                IMAGE_POLICY.trusted_image_reference(wrong_repository, "python_base")
            with self.assertRaisesRegex(IMAGE_POLICY.ImagePolicyError, "image_not_approved"):
                IMAGE_POLICY.trusted_image_reference("registry.example/rehearsal/python@sha256:" + "b" * 64, "python_base")

    def test_candidate_build_does_not_treat_a_local_tag_as_helper_approval(self) -> None:
        image = "registry.example/rehearsal/helper@sha256:" + "a" * 64
        python_base = "registry.example/rehearsal/python@sha256:" + "b" * 64
        uv = "registry.example/rehearsal/uv@sha256:" + "c" * 64
        reviewed_bases_only = {
            "python_base": frozenset({python_base}),
            "uv": frozenset({uv}),
            "helper": frozenset(),
        }
        environment = {
            "REHEARSAL_CANDIDATE_HELPER_IMAGE_TAG": "ai-bap-rehearsal-candidate:review",
            "REHEARSAL_PYTHON_BASE_IMAGE": python_base,
            "REHEARSAL_UV_IMAGE": uv,
        }
        with (
            patch.object(IMAGE_POLICY, "REVIEWED_IMAGE_ALLOWLIST", reviewed_bases_only),
            patch.object(sys, "argv", [str(BUILD)]),
            patch.dict(os.environ, environment, clear=True),
        ):
            build_command = BUILD_MODULE.command()
        self.assertIn("ai-bap-rehearsal-candidate:review", build_command)
        self.assertNotIn(image, build_command)

        with (
            patch.object(IMAGE_POLICY, "REVIEWED_IMAGE_ALLOWLIST", {
                "python_base": frozenset(), "uv": frozenset(), "helper": frozenset(),
            }),
            self.assertRaisesRegex(IMAGE_POLICY.ImagePolicyError, "image_approval_missing"),
        ):
            IMAGE_POLICY.trusted_image_reference(image, "helper")
        with (
            self.assertRaisesRegex(LAUNCH_MODULE.LauncherError, "image_approval_missing"),
            patch.dict(os.environ, {"REHEARSAL_HELPER_IMAGE": image}, clear=True),
        ):
            LAUNCH_MODULE.helper_command("a" * 64, "preflight")
        with (
            self.assertRaisesRegex(LAUNCH_MODULE.LauncherError, "image_reference_error"),
            patch.dict(os.environ, {
                "REHEARSAL_HELPER_IMAGE": "ai-bap-rehearsal-candidate:review",
            }, clear=True),
        ):
            LAUNCH_MODULE.helper_command("a" * 64, "preflight")

    def test_build_rejects_legacy_or_non_local_candidate_tags(self) -> None:
        with (
            patch.dict(os.environ, {
                "REHEARSAL_CANDIDATE_HELPER_IMAGE_TAG": "registry.example/rehearsal:review",
            }, clear=True),
            self.assertRaisesRegex(BUILD_MODULE.BuildError, "candidate_image_tag_error"),
        ):
            BUILD_MODULE.candidate_image_tag()
        with (
            patch.dict(os.environ, {
                "REHEARSAL_CANDIDATE_HELPER_IMAGE_TAG": "ai-bap-rehearsal-candidate:review",
                "REHEARSAL_HELPER_IMAGE_TAG": "legacy:tag",
            }, clear=True),
            self.assertRaisesRegex(BUILD_MODULE.BuildError, "build_configuration_error"),
        ):
            BUILD_MODULE.candidate_image_tag()
        with (
            patch.dict(os.environ, {
                "REHEARSAL_CANDIDATE_HELPER_IMAGE_TAG": "ai-bap-rehearsal-candidate:review",
                "REHEARSAL_HELPER_IMAGE": (
                    "registry.example/rehearsal/helper@sha256:" + "a" * 64
                ),
            }, clear=True),
            self.assertRaisesRegex(BUILD_MODULE.BuildError, "build_configuration_error"),
        ):
            BUILD_MODULE.candidate_image_tag()

    def test_build_rejects_an_altered_context_policy(self) -> None:
        with patch.object(BUILD_MODULE, "EXPECTED_DOCKERIGNORE", BUILD_MODULE.EXPECTED_DOCKERIGNORE + "# altered\n"):
            with self.assertRaisesRegex(BUILD_MODULE.BuildError, "build_context_policy_error"):
                BUILD_MODULE.validate_context_policy()


if __name__ == "__main__":
    unittest.main()
