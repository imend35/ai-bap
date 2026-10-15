
"""Test AI-generated user story validation and error handling."""

import pytest
from pydantic import ValidationError

from app.services.ai.user_story_generator import (
    AIGenerationError,
    GeneratedUserStory,
    generate_user_story,
)


def create_story(acceptance_criteria: list[str]) -> GeneratedUserStory:
    """Create a user story draft for validation tests."""

    # Testlerimde ortak bir User Story taslağı kullanıyorum.
    return GeneratedUserStory(
        title="Secure User Login",
        description=(
            "As a user, I want to log in securely, "
            "so that I can access my account."
        ),
        acceptance_criteria=acceptance_criteria,
    )


def test_valid_user_story() -> None:
    """Verify that a valid user story is accepted."""

    # Geçerli bir kabul kriteriyle User Story oluşturuyorum.
    story = create_story(
        ["Given valid credentials, when I log in, then access is granted."]
    )

    assert story.title == "Secure User Login"
    assert len(story.acceptance_criteria) == 1


@pytest.mark.parametrize(
    "criterion",
    ["", "   "],
)
def test_blank_acceptance_criteria_rejected(criterion: str) -> None:
    """Verify that blank acceptance criteria are rejected."""

    # Boş veya yalnızca boşluk içeren kriterlerin reddedildiğini doğruluyorum.
    with pytest.raises(ValidationError):
        create_story([criterion])


def test_empty_acceptance_criteria_list_rejected() -> None:
    """Verify that at least one acceptance criterion is required."""

    # Kabul kriterleri listesinin tamamen boş olmasını engelliyorum.
    with pytest.raises(ValidationError):
        create_story([])


def test_acceptance_criterion_max_length() -> None:
    """Verify the acceptance criterion length boundary."""

    # 1000 karakterlik kriterin kabul edildiğini doğruluyorum.
    story = create_story(["A" * 1000])

    assert len(story.acceptance_criteria[0]) == 1000

    # 1001 karakterlik kriterin reddedildiğini doğruluyorum.
    with pytest.raises(ValidationError):
        create_story(["A" * 1001])


def test_too_many_acceptance_criteria_rejected() -> None:
    """Verify that no more than ten criteria are accepted."""

    # AI modelinin 10'dan fazla kriter üretmesini engelliyorum.
    with pytest.raises(ValidationError):
        create_story(["Valid criterion"] * 11)


def test_missing_api_key_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify controlled failure when the API key is missing."""

    from app.services import ai
    from app.services.ai import user_story_generator

    # API anahtarını test ortamında geçici olarak devre dışı bırakıyorum.
    settings = user_story_generator.get_settings().model_copy(
        update={"openai_api_key": None}
    )

    monkeypatch.setattr(
        user_story_generator,
        "get_settings",
        lambda: settings,
    )

    # API anahtarı olmadığında kontrollü hata bekliyorum.
    with pytest.raises(
        AIGenerationError,
        match="OpenAI API key is not configured",
    ):
        generate_user_story(
            requirement_title="User Login",
            requirement_description="Users must log in securely.",
            requirement_priority="high",
        )
