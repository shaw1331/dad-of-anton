from __future__ import annotations

import logging
import time
from urllib.parse import urlparse

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import settings

logger = logging.getLogger("app.timing")

_INSTALLED = False


def _kind(url: str) -> str:
    base = (settings.SUPABASE_URL or "").rstrip("/")
    if base and url.startswith(base):
        return "db"
    return "http"


def _log_downstream(kind: str, method: str, url: str, status: object, start: float) -> None:
    parsed = urlparse(url)
    logger.info(
        "downstream kind=%s method=%s host=%s path=%s status=%s duration_ms=%s",
        kind,
        method,
        parsed.netloc or "-",
        parsed.path or "-",
        status,
        round((time.time() - start) * 1000),
    )


class RequestTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        logger.info(
            "request method=%s path=%s query=%s status=%s duration_ms=%s content_length=%s",
            request.method,
            request.url.path,
            request.url.query or "-",
            response.status_code,
            round((time.time() - start) * 1000),
            response.headers.get("content-length", "-"),
        )
        return response


# ponytail: no request_id; add ContextVar if concurrent lines mix
def install_outbound_timing() -> None:
    global _INSTALLED
    if _INSTALLED:
        return

    from requests import Session

    _orig_requests_send = Session.send

    def _requests_send(self, request, **kwargs):
        start = time.time()
        status: object = "err"
        try:
            resp = _orig_requests_send(self, request, **kwargs)
            status = resp.status_code
            return resp
        finally:
            _log_downstream(_kind(request.url), request.method, request.url, status, start)

    Session.send = _requests_send

    import httpx

    _orig_httpx_send = httpx.Client.send

    def _httpx_send(self, request, **kwargs):
        start = time.time()
        status: object = "err"
        try:
            resp = _orig_httpx_send(self, request, **kwargs)
            status = resp.status_code
            return resp
        finally:
            _log_downstream(
                _kind(str(request.url)), request.method, str(request.url), status, start
            )

    httpx.Client.send = _httpx_send

    _orig_httpx_async_send = httpx.AsyncClient.send

    async def _httpx_async_send(self, request, **kwargs):
        start = time.time()
        status: object = "err"
        try:
            resp = await _orig_httpx_async_send(self, request, **kwargs)
            status = resp.status_code
            return resp
        finally:
            _log_downstream(
                _kind(str(request.url)), request.method, str(request.url), status, start
            )

    httpx.AsyncClient.send = _httpx_async_send
    _INSTALLED = True
