"""Fail-closed host launcher for the clone-specific rehearsal helper."""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

from image_policy import ImagePolicyError, trusted_image_reference


APPROVED_RESTORE_NAME = "ai-bap-restore-verification-20261017"
EXPECTED_ENDPOINT = ("127.0.0.1", "5432", "restore_check_db")
SECRET_TARGET = "/run/secrets/restore_db_password"
PREFLIGHT_REPORT_TARGET = "/run/rehearsal/preflight-report.json"
FULL_CONTAINER_ID = re.compile(r"^[0-9a-f]{64}$")


class LauncherError(RuntimeError):
    """Represent a safe launcher failure category."""


def required(name: str) -> str:
    """Read a required launcher setting without printing its value."""
    value = os.environ.get(name)
    if not value:
        raise LauncherError("configuration_error")
    return value


def approved_container_id() -> str:
    """Require a manually approved immutable full container ID."""
    container_id = required("REHEARSAL_APPROVED_RESTORE_CONTAINER_ID")
    if not FULL_CONTAINER_ID.fullmatch(container_id):
        raise LauncherError("configuration_error")
    return container_id


def inspect_restore(container_id: str) -> str:
    """Inspect exactly one container and reject every unapproved attribute."""
    completed = subprocess.run(
        ["docker", "inspect", "--type", "container", container_id],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise LauncherError("restore_inspection_failed")
    inspected = json.loads(completed.stdout)
    if not isinstance(inspected, list) or len(inspected) != 1 or not isinstance(inspected[0], dict):
        raise LauncherError("restore_inspection_failed")
    restore = inspected[0]
    if restore.get("Id") != container_id:
        raise LauncherError("restore_verification_failed")
    if restore.get("Name") != f"/{APPROVED_RESTORE_NAME}":
        raise LauncherError("restore_verification_failed")
    if restore.get("State", {}).get("Running") is not True:
        raise LauncherError("restore_verification_failed")
    if restore.get("HostConfig", {}).get("NetworkMode") != "none":
        raise LauncherError("restore_verification_failed")
    host_ports = restore.get("HostConfig", {}).get("PortBindings")
    network_ports = restore.get("NetworkSettings", {}).get("Ports")
    if host_ports or network_ports:
        raise LauncherError("restore_verification_failed")
    # Use Docker's successfully inspected immutable ID as the namespace target.
    return str(restore["Id"])


def requested_stage() -> str:
    """Require the operator to select one stage; there is no combined mode."""
    if len(sys.argv) != 2 or sys.argv[1] not in {"preflight", "upgrade"}:
        raise LauncherError("configuration_error")
    return sys.argv[1]


def helper_command(container_id: str, stage: str) -> list[str]:
    """Build the fixed helper command only after the restore checks succeed."""
    try:
        image = trusted_image_reference(required("REHEARSAL_HELPER_IMAGE"), "helper")
    except ImagePolicyError as error:
        raise LauncherError(str(error)) from error
    secret_source = Path(required("REHEARSAL_PASSWORD_SECRET_SOURCE"))
    if not secret_source.is_file():
        raise LauncherError("configuration_error")
    endpoint = (
        required("REHEARSAL_DATABASE_HOST"),
        required("REHEARSAL_DATABASE_PORT"),
        required("REHEARSAL_DATABASE_NAME"),
    )
    if endpoint != EXPECTED_ENDPOINT:
        raise LauncherError("configuration_error")
    database_user = required("REHEARSAL_DATABASE_USER")
    command = [
        "docker", "run", "--rm", "--read-only", "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges", "--network", f"container:{container_id}",
        "--mount", f"type=bind,src={secret_source},dst={SECRET_TARGET},readonly",
        "--env", f"REHEARSAL_DATABASE_HOST={endpoint[0]}",
        "--env", f"REHEARSAL_DATABASE_PORT={endpoint[1]}",
        "--env", f"REHEARSAL_DATABASE_NAME={endpoint[2]}",
        "--env", f"REHEARSAL_DATABASE_USER={database_user}",
        "--env", f"REHEARSAL_RESTORE_CONTAINER_ID={container_id}",
    ]
    if stage == "upgrade":
        report_source = Path(required("REHEARSAL_PREFLIGHT_REPORT_SOURCE"))
        if not report_source.is_file():
            raise LauncherError("configuration_error")
        command.extend([
            "--mount", f"type=bind,src={report_source},dst={PREFLIGHT_REPORT_TARGET},readonly",
        ])
        command.extend([
            "--env", f"REHEARSAL_RECORD_NUMBER_WRITER_ROLE={required('REHEARSAL_RECORD_NUMBER_WRITER_ROLE')}",
        ])
    return [*command, image, stage]


def main() -> int:
    """Inspect first, then start the fixed helper exactly once."""
    try:
        stage = requested_stage()
        approved_id = approved_container_id()
        verified_id = inspect_restore(approved_id)
        completed = subprocess.run(helper_command(verified_id, stage), check=False, capture_output=True)
        if completed.returncode != 0:
            raise LauncherError("helper_container_failed")
        if stage in {"preflight", "upgrade"}:
            sys.stdout.buffer.write(completed.stdout)
        return 0
    except LauncherError as error:
        print(f"rehearsal launcher refused or failed: {error}", file=sys.stderr)
    except (OSError, json.JSONDecodeError):
        print("rehearsal launcher refused or failed: docker_or_runtime_error", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
