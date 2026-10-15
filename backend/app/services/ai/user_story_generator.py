
"""Generate validated user story drafts using the OpenAI API."""

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
    """Represent a validated AI-generated user story draft."""

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
        """Validate each AI-generated acceptance criterion."""

        # Her kabul kriterinin anlamlı bir metin içerdiğini kontrol ediyorum.
        for criterion in criteria:
            if not criterion.strip():
                raise ValueError(
                    "Acceptance criteria cannot be blank."
                )

            # Mevcut User Story şemamızla uzunluk uyumunu koruyorum.
            if len(criterion) > 1000:
                raise ValueError(
                    "Each acceptance criterion must be at most 1000 characters."
                )

        return criteria


class AIGenerationError(Exception):
    """Represent a controlled AI generation failure."""


def generate_user_story(
    requirement_title: str,
    requirement_description: str,
    requirement_priority: str,
) -> GeneratedUserStory:
    """Generate a user story draft from requirement information."""

    # AI yapılandırmasını uygulama ayarlarından okuyorum.
    settings = get_settings()

    if (
        settings.openai_api_key is None
        or not settings.openai_api_key.get_secret_value().strip()
    ):
        raise AIGenerationError(
            "OpenAI API key is not configured."
        )

    # Gereksinim bilgilerinden kullanıcı prompt'unu oluşturuyorum.
    user_prompt = build_user_story_prompt(
        requirement_title=requirement_title,
        requirement_description=requirement_description,
        requirement_priority=requirement_priority,
    )

    # API anahtarını kaynak kodda tutmadan OpenAI istemcisini oluşturuyorum.
    client = OpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
        timeout=30.0,
        max_retries=1,
    )

    try:
        # Modelden yalnızca JSON biçiminde bir User Story taslağı istiyorum.
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

        content = response.choices[0].message.content

        if not content:
            raise AIGenerationError(
                "AI returned an empty response."
            )

        # AI yanıtını JSON olarak ayrıştırıp Pydantic ile doğruluyorum.
        generated_data = json.loads(content)

        return GeneratedUserStory.model_validate(generated_data)

    except (
        APIError,
        json.JSONDecodeError,
        ValidationError,
        IndexError,
    ) as exc:
        raise AIGenerationError(
            "AI user story generation failed."
        ) from exc
