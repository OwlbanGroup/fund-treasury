"""Entity request/response schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EntityBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: str = Field(min_length=1, max_length=50)
    base_currency: str = Field(default="USD", min_length=3, max_length=3)


class EntityCreate(EntityBase):
    pass


class EntityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    base_currency: str | None = Field(default=None, min_length=3, max_length=3)


class EntityOut(EntityBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
