"""I define reusable response schemas for record ownership."""

from pydantic import BaseModel, ConfigDict, Field


class RecordCreator(BaseModel):
    """I expose the readable identity of a record creator."""

    model_config = ConfigDict(from_attributes=True)

    record_number: str = Field(pattern=r"^USR-[0-9]{3,}$")
    full_name: str = Field(max_length=160)
