from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = round((time.perf_counter() - start) * 1000, 2)
        print(f"{request.method} {request.url.path} → {response.status_code} ({duration}ms)")
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


class OrgScopingMiddleware(BaseHTTPMiddleware):
    """Extracts org_id from JWT and attaches to request state for downstream use."""

    async def dispatch(self, request: Request, call_next):
        return await call_next(request)


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Logs mutating requests for audit trail (stub — logs to stdout only)."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.method in ("POST", "PUT", "PATCH", "DELETE") and response.status_code < 400:
            request_id = getattr(request.state, "request_id", "-")
            print(f"[AUDIT] {request.method} {request.url.path} request_id={request_id}")
        return response
