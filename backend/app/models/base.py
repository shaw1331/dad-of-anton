from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel as PydanticBaseModel, Field


class BaseModel(PydanticBaseModel):
    id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
