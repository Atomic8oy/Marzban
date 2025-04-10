from typing import Any
from datetime import datetime as dt

from pydantic import BaseModel, ConfigDict, field_validator, Field


class BackendBase(BaseModel):
    name: str = Field(max_length=256)
    config: dict[str, Any]
    exclude_inbound_tags: str = Field(max_length=2048)
    fallbacks_inbound_tags: str = Field(max_length=2048)


class BackendCreate(BackendBase):
    name: str | None = None
    exclude_inbound_tags: str | None = None
    fallbacks_inbound_tags: str | None = None

    @field_validator("config", mode="before")
    def validate_config(cls, v: dict[str, Any]) -> dict[str, Any]:
        if not v:
            raise ValueError("config dictionary cannot be empty")
        return v


class BackendResponse(BackendBase):
    id: int
    created_at: dt

    model_config = ConfigDict(from_attributes=True)


class BackendResponseList(BaseModel):
    count: int
    backends: list[BackendResponse] = []

    model_config = ConfigDict(from_attributes=True)
