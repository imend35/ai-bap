"""I configure fail-closed database safety before test modules are imported."""

import os

from pydantic import ValidationError
from pydantic_settings.exceptions import SettingsError
from sqlalchemy.exc import ArgumentError

from app.test_database_safety import (
    IntegrationDatabaseSafetyError,
    configure_pytest_test_database_environment,
    validate_effective_settings_database_target,
)

_selected_database_target = configure_pytest_test_database_environment()

# I opt into the legacy registration contract only inside the test process.
os.environ["PUBLIC_REGISTRATION_ENABLED"] = "true"

# I validate process and dotenv settings before any test module can import an engine.
try:
    from app.config import get_settings

    get_settings.cache_clear()
    validate_effective_settings_database_target(
        get_settings(), _selected_database_target
    )
except IntegrationDatabaseSafetyError:
    raise
except (
    ArgumentError,
    AttributeError,
    OSError,
    RuntimeError,
    SettingsError,
    TypeError,
    ValidationError,
    ValueError,
):
    raise IntegrationDatabaseSafetyError(
        "Effective integration-test database settings are invalid."
    ) from None
