from __future__ import annotations

import logging

from fastapi import APIRouter, Query

from app.stock_cache import search_stocks

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("/search")
def search(q: str = Query(..., min_length=1), limit: int = Query(10, ge=1, le=50)):
    return search_stocks(q, limit)
