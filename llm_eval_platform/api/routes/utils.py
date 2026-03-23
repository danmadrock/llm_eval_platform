from __future__ import annotations


def data_response(data):
    return {"data": data}


def list_response(data, *, limit: int, offset: int, total: int):
    return {"data": data, "pagination": {"limit": limit, "offset": offset, "total": total}}
