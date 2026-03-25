from __future__ import annotations

import hashlib
import hmac
import time
from collections.abc import Callable
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, Request, status

from llm_eval_platform.core.config import get_settings
from llm_eval_platform.core.tenancy import set_current_tenant


@dataclass(frozen=True)
class RequestContext:
    tenant_id: str
    principal_id: str
    role: str

    @property
    def can_write(self) -> bool:
        return self.role in {"writer", "admin"}


@dataclass(frozen=True)
class ApiPrincipal:
    principal_id: str
    tenant_id: str
    role: str
    secret: str


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, tuple[int, int]] = {}

    def allow(self, key: str, limit: int, now: int) -> bool:
        window = now // 60
        bucket_window, count = self._buckets.get(key, (window, 0))
        if bucket_window != window:
            bucket_window, count = window, 0
        if count >= limit:
            self._buckets[key] = (bucket_window, count)
            return False
        self._buckets[key] = (bucket_window, count + 1)
        return True


_rate_limiter = InMemoryRateLimiter()


def _parse_principals() -> dict[str, ApiPrincipal]:
    settings = get_settings()
    principals: dict[str, ApiPrincipal] = {}
    for raw in settings.api_key_records:
        key_id, tenant_id, role, secret = [part.strip() for part in raw.split(":", maxsplit=3)]
        principals[key_id] = ApiPrincipal(
            principal_id=key_id,
            tenant_id=tenant_id,
            role=role,
            secret=secret,
        )
    return principals


def _extract_api_key(request: Request, explicit_key: str | None, auth_header: str | None) -> str:
    if explicit_key:
        return explicit_key
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API credentials.")


def _validate_signature(api_key: str, signature: str | None, secret: str) -> None:
    if not signature:
        return
    digest = hmac.new(secret.encode("utf-8"), api_key.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key signature.")


def require_request_context(
    request: Request,
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_api_signature: str | None = Header(default=None, alias="X-API-Signature"),
) -> RequestContext:
    settings = get_settings()
    api_key = _extract_api_key(request, x_api_key, authorization)
    principals = _parse_principals()
    principal = principals.get(api_key)
    if principal is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key.")

    _validate_signature(api_key, x_api_signature, principal.secret)

    if request.method not in {"GET", "HEAD", "OPTIONS"} and principal.role not in {"writer", "admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Write access is required.")

    now = int(time.time())
    rate_limit_key = f"{principal.tenant_id}:{principal.principal_id}"
    if not _rate_limiter.allow(rate_limit_key, settings.requests_per_minute, now):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded.")

    context = RequestContext(
        tenant_id=principal.tenant_id,
        principal_id=principal.principal_id,
        role=principal.role,
    )
    request.state.request_context = context
    return context


def get_request_context(request: Request) -> RequestContext:
    context = getattr(request.state, "request_context", None)
    if context is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No request context available.")
    return context


def with_write_access(context_getter: Callable[[], RequestContext]) -> None:
    context = context_getter()
    if not context.can_write:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Write access is required.")


def bind_tenant_context(context: RequestContext = Depends(require_request_context)) -> RequestContext:
    set_current_tenant(context.tenant_id)
    return context
