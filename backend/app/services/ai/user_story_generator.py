"""I generate validated user story drafts using the OpenAI API."""

import json

from openai import APIError, OpenAI
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
)

from app.config import get_settings
from app.services.ai.user_story_prompt import (
    SYSTEM_PROMPT,
    build_user_story_prompt,
)


class GeneratedUserStory(BaseModel):
    """I represent a validated AI-generated user story draft."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=5000)
    acceptance_criteria: list[str] = Field(
        min_length=1,
        max_length=10,
    )

    @field_validator("acceptance_criteria")
    @classmethod
    def validate_acceptance_criteria(
        cls,
        criteria: list[str],
    ) -> list[str]:
        """I validate each AI-generated acceptance criterion."""

        # I verify that every acceptance criterion contains meaningful text.
        for criterion in criteria:
            if not criterion.strip():
                raise ValueError("Acceptance criteria cannot be blank.")

            # I enforce the length limit defined by the user story schema.
            if len(criterion) > 1000:
                raise ValueError("Each acceptance criterion must be at most 1000 characters.")

        return criteria


class AIGenerationError(Exception):
    """I represent a controlled AI generation failure."""


def extract_response_content(response: object) -> str:
    """I safely extract JSON text from an OpenAI response."""

    # I verify that the response contains a non-empty choices list.
    choices = getattr(response, "choices", None)

    if not isinstance(choices, list) or not choices:
        raise AIGenerationError("AI returned an invalid response structure.")

    # I verify that the first choice contains a message.
    message = getattr(choices[0], "message", None)

    if message is None:
        raise AIGenerationError("AI returned an invalid response structure.")

    # I verify that the message contains text rather than another data type.
    content = getattr(message, "content", None)

    if content is None or content == "":
        raise AIGenerationError("AI returned an empty response.")

    if not isinstance(content, str):
        raise AIGenerationError("AI returned an invalid response structure.")

    return content


def generate_user_story(
    requirement_title: str,
    requirement_description: str,
    requirement_priority: str,
) -> GeneratedUserStory:
    """I generate a user story draft from requirement information."""

    # I read the AI configuration from application settings.
    settings = get_settings()

    if settings.openai_api_key is None or not settings.openai_api_key.get_secret_value().strip():
        raise AIGenerationError("OpenAI API key is not configured.")

    # I construct the user prompt from untrusted requirement data.
    user_prompt = build_user_story_prompt(
        requirement_title=requirement_title,
        requirement_description=requirement_description,
        requirement_priority=requirement_priority,
    )

    try:
        # I initialize the OpenAI client without exposing credentials.
        client = OpenAI(
            api_key=settings.openai_api_key.get_secret_value(),
            base_url=settings.openai_base_url,
            timeout=30.0,
            max_retries=1,
        )

        # I request a JSON-formatted user story draft.
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        # I validate the response structure before parsing its content.
        content = extract_response_content(response)

        # I parse JSON and validate the generated story schema.
        generated_data = json.loads(content)

        return GeneratedUserStory.model_validate(generated_data)

    except (
        APIError,
        json.JSONDecodeError,
        ValidationError,
        ValueError,
    ) as exc:
        raise AIGenerationError("AI user story generation failed.") from exc
