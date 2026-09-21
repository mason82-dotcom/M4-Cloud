from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EventIn(BaseModel):
    source: str = Field(min_length=1, max_length=64)
    topic: str | None = Field(default=None, max_length=512)
    payload: dict[str, Any] | list[Any] | str | int | float | bool | None
