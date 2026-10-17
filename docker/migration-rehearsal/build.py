"""Build an explicitly untrusted candidate rehearsal-helper image."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

from image_policy import ImagePolicyError, trusted_image_reference

ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = ROOT / "docker" / "migration-rehearsal" / "Dockerfile"
EXPECTED_DOCKERIGNORE = """# The repository root is a Docker context only for the rehearsal image.
# Send only the files copied by docker/migration-rehearsal/Dockerfile.
**
!backend/
!backend/pyproject.toml
!backend/uv.lock
!backend/migrations/
!backend/migrations/**
!docker/
!docker/migration-rehearsal/
!docker/migration-rehearsal/Dockerfile
!docker/migration-rehearsal/alembic.ini
!docker/migration-rehearsal/env.py
!docker/migration-rehearsal/rehearse.py
"""
LOCAL_CANDIDATE_TAG = re.compile(
    r"^[a-z0-9][a-z0-9._-]*:[a-z0-9][a-z0-9._-]{0,127}$"
)


class BuildError(RuntimeError):
    """Represent a safe build failure category."""


def required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise BuildError("build_configuration_error")
    return value


def approved_image(name: str, role: str) -> str:
    """Require a reviewed full identity, never merely digest-shaped input."""
    try:
        return trusted_image_reference(required(name), role)
    except ImagePolicyError as error:
        raise BuildError(str(error)) from error


def candidate_image_tag() -> str:
    """Return a local mutable label that is never an approval credential."""
    tag = required("REHEARSAL_CANDIDATE_HELPER_IMAGE_TAG")
    if not LOCAL_CANDIDATE_TAG.fullmatch(tag):
        raise BuildError("candidate_image_tag_error")
    if (
        os.environ.get("REHEARSAL_HELPER_IMAGE_TAG")
        or os.environ.get("REHEARSAL_HELPER_IMAGE")
    ):
        raise BuildError("build_configuration_error")
    return tag


def validate_context_policy() -> None:
    """Reject a modified allowlist before the Docker client receives the context."""
    policy_path = ROOT / ".dockerignore"
    if not policy_path.is_file() or policy_path.read_text(encoding="utf-8") != EXPECTED_DOCKERIGNORE:
        raise BuildError("build_context_policy_error")


def command() -> list[str]:
    """Build a candidate only from the root allowlisted Docker context."""
    if len(sys.argv) != 1 or not DOCKERFILE.is_file():
        raise BuildError("build_configuration_error")
    validate_context_policy()
    return [
        "docker",
        "build",
        "--file",
        str(DOCKERFILE),
        "--build-arg",
        f"PYTHON_BASE_IMAGE={approved_image('REHEARSAL_PYTHON_BASE_IMAGE', 'python_base')}",
        "--build-arg",
        f"UV_IMAGE={approved_image('REHEARSAL_UV_IMAGE', 'uv')}",
        "--tag",
        candidate_image_tag(),
        str(ROOT),
    ]


def main() -> int:
    """Invoke Docker only after every static build guard has passed."""
    try:
        completed = subprocess.run(command(), check=False, capture_output=True)
        if completed.returncode != 0:
            raise BuildError("helper_image_build_failed")
        return 0
    except BuildError as error:
        print(f"rehearsal build refused or failed: {error}", file=sys.stderr)
    except OSError:
        print("rehearsal build refused or failed: docker_unavailable", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
