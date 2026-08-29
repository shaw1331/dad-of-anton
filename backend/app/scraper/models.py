from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ScraperResult(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: str | None = None
    source: str


class IndexDTO(BaseModel):
    name: str
    slug: str
    stocks: list[StockSummaryDTO] = []


class StockSummaryDTO(BaseModel):
    ticker: str
    name: str
    url: str


class StockDTO(BaseModel):
    ticker: str
    name: str
    company_name: str = ""
    sector: str | None = None
    industry: str | None = None
    ratios: dict[str, str] = Field(default_factory=dict)
    quarterly: dict[str, str] = Field(default_factory=dict)
    shareholding: dict[str, str] = Field(default_factory=dict)
    pros: list[str] = Field(default_factory=list)
    cons: list[str] = Field(default_factory=list)
    url: str = ""
    scraped_at: datetime | None = None
