
"""Define API schemas for AI-assisted user story generation."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AIUserStoryGenerateRequest(BaseModel):
    """Represent a request to generate a user story draft."""

    model_config = ConfigDict(extra="forbid")

    # AI taslağını mevcut bir gereksinime bağlı olarak oluşturuyorum.
    requirement_id: UUID


class AIUserStoryGenerateResponse(BaseModel):
    """Represent an AI-generated user story draft."""

    model_config = ConfigDict(extra="forbid")

    # Taslağın hangi gereksinimden üretildiğini belirtiyorum.
    requirement_id: UUID

    # AI tarafından oluşturulan User Story içeriğini döndürüyorum.
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=5000)
    acceptance_criteria: list[str] = Field(
        min_length=1,
        max_length=10,
    )

    # AI taslağının insan tarafından incelenmesi gerektiğini belirtiyorum.
    requires_human_review: bool = True

    # Taslağın otomatik olarak veritabanına kaydedilmediğini belirtiyorum.
    saved_to_database: bool = False
