from __future__ import annotations

from contextvars import ContextVar

_current_tenant_id: ContextVar[str | None] = ContextVar("current_tenant_id", default=None)


def set_current_tenant(tenant_id: str | None):
    return _current_tenant_id.set(tenant_id)


def reset_current_tenant(token) -> None:
    _current_tenant_id.reset(token)


def get_current_tenant() -> str | None:
    return _current_tenant_id.get()
