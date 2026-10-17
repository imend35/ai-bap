"""Reviewed, role-bound image identities for the migration rehearsal helper."""

from __future__ import annotations

import re


# An identity always names an explicit registry and repository.  A tag is not
# part of, and cannot substitute for, an approved image identity.
IMAGE_IDENTITY = re.compile(
    r"^[a-z0-9][a-z0-9.-]*(?::[0-9]+)?/"
    r"(?:[a-z0-9][a-z0-9._-]*/)*[a-z0-9][a-z0-9._-]*"
    r"@sha256:[0-9a-f]{64}$"
)

# Populate only through a separately reviewed change after independently
# verifying the exact publisher, manifest, and required platform.  These are
# deliberately empty: no digest was reviewed as part of this change.
REVIEWED_IMAGE_ALLOWLIST: dict[str, frozenset[str]] = {
    "python_base": frozenset(),
    "uv": frozenset(),
    "helper": frozenset(),
}


class ImagePolicyError(RuntimeError):
    """Represent a safe image-trust refusal category."""


def trusted_image_reference(image: str, role: str) -> str:
    """Return a reviewed complete identity or fail closed by category."""
    if not IMAGE_IDENTITY.fullmatch(image) or image.endswith("sha256:" + "0" * 64):
        raise ImagePolicyError("image_reference_error")
    approvals = REVIEWED_IMAGE_ALLOWLIST[role]
    if not approvals:
        raise ImagePolicyError("image_approval_missing")
    if image not in approvals:
        raise ImagePolicyError("image_not_approved")
    return image
