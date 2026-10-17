"""Share transaction coordination for administrator user lifecycle actions."""

from sqlalchemy import text
from sqlalchemy.orm import Session

# I serialize changes that can create or change the active-admin set.
ACTIVE_ADMIN_LIFECYCLE_ADVISORY_LOCK_KEY = 7_432_094_863_100


def acquire_active_admin_lifecycle_lock(db: Session) -> None:
    """Acquire the PostgreSQL transaction-scoped active-admin lifecycle lock."""

    db.execute(
        text("SELECT pg_advisory_xact_lock(:lock_key)"),
        {"lock_key": ACTIVE_ADMIN_LIFECYCLE_ADVISORY_LOCK_KEY},
    )
