from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class NewsArticle(BaseModel):
    id: str
    summary: str
    url: str
    image_url: str | None = None
    pub_date: datetime
    source: str
