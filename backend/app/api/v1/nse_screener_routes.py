from __future__ import annotations

import logging
import time

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.nse_screener.exceptions import ConfigError, DataFetchError, ScreenerError
from app.nse_screener.factory import ScreenerFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/nse-screener", tags=["nse-screener"])


class RunRequest(BaseModel):
    screener: str


@router.get("/screeners")
def list_screeners():
    """Return all available NSE screeners."""
    return ScreenerFactory.list_screeners()


@router.post("/run")
def run_screener(request: RunRequest):
    """Run a named screener and return results inline."""
    try:
        screener = ScreenerFactory.get(request.screener)
    except ConfigError as e:
        raise HTTPException(status_code=422, detail=str(e))

    start = time.time()
    try:
        rows = screener.run()
    except DataFetchError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ScreenerError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.exception("Screener '%s' failed", request.screener)
        raise HTTPException(status_code=500, detail=str(e))

    took_ms = round((time.time() - start) * 1000)
    columns = list(rows[0].keys()) if rows else []

    return {
        "screener": request.screener,
        "columns": columns,
        "rows": rows,
        "count": len(rows),
        "took_ms": took_ms,
    }
