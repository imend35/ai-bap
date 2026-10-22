"""I configure fail-closed database safety before test modules are imported."""

from app.test_database_safety import configure_test_database_environment

configure_test_database_environment()
