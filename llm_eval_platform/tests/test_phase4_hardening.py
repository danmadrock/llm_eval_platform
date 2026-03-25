from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import llm_eval_platform.models  # noqa: F401
from llm_eval_platform.api.main import app
from llm_eval_platform.core.database import Base, get_db


def _make_client(tmp_path: Path) -> TestClient:
    db_path = tmp_path / "phase4.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = session_local()
        try:
            db.info["tenant_id"] = "tenant-dev"
            db.info["principal_id"] = "dev-admin"
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    client.headers.update({"X-API-Key": "dev-admin"})
    return client


def test_auth_required(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    unauth = TestClient(app).get("/api/v1/datasets")
    assert unauth.status_code == 401


def test_dashboard_and_tenant_isolation(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    created = client.post("/api/v1/datasets", json={"name": "tenant-a", "task_type": "qa"})
    assert created.status_code == 201
    assert client.get("/api/v1/dashboard/overview").status_code == 200

    # Unknown key should be denied and prevent cross-tenant visibility.
    denied = client.get("/api/v1/datasets", headers={"X-API-Key": "invalid"})
    assert denied.status_code == 401
