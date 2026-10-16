
"""I test AI-generated user story validation and error handling."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from openai import APIConnectionError, APITimeoutError
from pydantic import SecretStr, ValidationError

from app.services.ai import user_story_generator
from app.services.ai.user_story_generator import (
    AIGenerationError,
    GeneratedUserStory,
    generate_user_story,
)


def create_story(acceptance_criteria: list[str]) -> GeneratedUserStory:
    """I create a user story draft for validation tests."""

    # I use a common user story draft across validation tests.
    return GeneratedUserStory(
        title="Secure User Login",
        description=(
            "As a user, I want to log in securely, "
            "so that I can access my account."
        ),
        acceptance_criteria=acceptance_criteria,
    )


def test_valid_user_story() -> None:
    """I verify that a valid user story is accepted."""

    # I create a story with one valid acceptance criterion.
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
    """I verify that blank acceptance criteria are rejected."""

    # I reject empty and whitespace-only acceptance criteria.
    with pytest.raises(ValidationError):
        create_story([criterion])


def test_empty_acceptance_criteria_list_rejected() -> None:
    """I verify that at least one acceptance criterion is required."""

    # I reject a user story without acceptance criteria.
    with pytest.raises(ValidationError):
        create_story([])


def test_acceptance_criterion_max_length() -> None:
    """I verify the acceptance criterion length boundary."""

    # I accept an acceptance criterion containing 1000 characters.
    story = create_story(["A" * 1000])

    assert len(story.acceptance_criteria[0]) == 1000

    # I reject an acceptance criterion exceeding 1000 characters.
    with pytest.raises(ValidationError):
        create_story(["A" * 1001])


def test_too_many_acceptance_criteria_rejected() -> None:
    """I verify that no more than ten criteria are accepted."""

    # I reject more than ten acceptance criteria.
    with pytest.raises(ValidationError):
        create_story(["Valid criterion"] * 11)


def test_missing_api_key_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """I verify controlled failure when the API key is missing."""

    # I temporarily disable the API key in the test environment.
    settings = user_story_generator.get_settings().model_copy(
        update={"openai_api_key": None}
    )

    monkeypatch.setattr(
        user_story_generator,
        "get_settings",
        lambda: settings,
    )

    # I expect a controlled error when no API key is configured.
    with pytest.raises(
        AIGenerationError,
        match="OpenAI API key is not configured",
    ):
        generate_user_story(
            requirement_title="User Login",
            requirement_description="Users must log in securely.",
            requirement_priority="high",
        )


@pytest.fixture
def mocked_openai(
    monkeypatch: pytest.MonkeyPatch,
) -> MagicMock:
    """I replace the OpenAI client with a controlled test double."""

    # I provide a synthetic key without exposing real credentials.
    settings = user_story_generator.get_settings().model_copy(
        update={"openai_api_key": SecretStr("test-only-api-key")}
    )

    monkeypatch.setattr(
        user_story_generator,
        "get_settings",
        lambda: settings,
    )

    # I prevent all real OpenAI API calls during these tests.
    client = MagicMock()

    monkeypatch.setattr(
        user_story_generator,
        "OpenAI",
        lambda **kwargs: client,
    )

    return client


def make_ai_response(content: str | None) -> SimpleNamespace:
    """I simulate an OpenAI chat completion response."""

    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content)
            )
        ]
    )


def run_generation() -> GeneratedUserStory:
    """I generate a user story using fixed test requirements."""

    return generate_user_story(
        requirement_title="Secure Login",
        requirement_description="Users must log in securely.",
        requirement_priority="high",
    )


def test_successful_ai_response(
    mocked_openai: MagicMock,
) -> None:
    """I verify that a valid AI response becomes a user story."""

    # I prepare a valid JSON response without calling the API.
    payload = {
        "title": "Secure Login",
        "description": (
            "As a user, I want to log in securely, "
            "so that I can access my account."
        ),
        "acceptance_criteria": [
            "Given valid credentials, when I log in, then access is granted."
        ],
    }

    mocked_openai.chat.completions.create.return_value = (
        make_ai_response(json.dumps(payload))
    )

    story = run_generation()

    assert isinstance(story, GeneratedUserStory)
    assert story.title == payload["title"]
    assert story.acceptance_criteria == payload["acceptance_criteria"]

    # I verify that the generator requests JSON output.
    request_kwargs = (
        mocked_openai.chat.completions.create.call_args.kwargs
    )

    assert request_kwargs["response_format"] == {
        "type": "json_object"
    }


def test_api_connection_error(
    mocked_openai: MagicMock,
) -> None:
    """I verify that API connection failures are handled safely."""

    # I simulate an SDK connection failure.
    request = httpx.Request(
        "POST",
        "https://api.openai.com/v1/chat/completions",
    )

    mocked_openai.chat.completions.create.side_effect = (
        APIConnectionError(request=request)
    )

    with pytest.raises(
        AIGenerationError,
        match="AI user story generation failed",
    ):
        run_generation()


def test_api_timeout_error(
    mocked_openai: MagicMock,
) -> None:
    """I verify that API timeouts are handled safely."""

    # I simulate an SDK timeout without making a network request.
    request = httpx.Request(
        "POST",
        "https://api.openai.com/v1/chat/completions",
    )

    mocked_openai.chat.completions.create.side_effect = (
        APITimeoutError(request=request)
    )

    with pytest.raises(
        AIGenerationError,
        match="AI user story generation failed",
    ):
        run_generation()


def test_invalid_json_response(
    mocked_openai: MagicMock,
) -> None:
    """I verify that malformed AI JSON responses are rejected."""

    # I simulate malformed JSON returned by the model.
    mocked_openai.chat.completions.create.return_value = (
        make_ai_response('{"title": "Incomplete"')
    )

    with pytest.raises(
        AIGenerationError,
        match="AI user story generation failed",
    ):
        run_generation()


def test_empty_ai_response(
    mocked_openai: MagicMock,
) -> None:
    """I verify that empty AI responses are rejected."""

    # I simulate an empty model response.
    mocked_openai.chat.completions.create.return_value = (
        make_ai_response(None)
    )

    with pytest.raises(
        AIGenerationError,
        match="AI returned an empty response",
    ):
        run_generation()


def test_invalid_ai_schema(
    mocked_openai: MagicMock,
) -> None:
    """I verify that AI responses must match the expected schema."""

    # I simulate valid JSON with missing required fields.
    mocked_openai.chat.completions.create.return_value = (
        make_ai_response(
            json.dumps(
                {
                    "title": "Secure Login",
                    "acceptance_criteria": [],
                }
            )
        )
    )

    with pytest.raises(
        AIGenerationError,
        match="AI user story generation failed",
    ):
        run_generation()
