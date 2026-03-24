from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

EXPECTED_TABLES = {
    "alembic_version",
    "datasets",
    "dataset_versions",
    "prompts",
    "prompt_versions",
    "model_configs",
    "experiments",
    "runs",
    "evaluation_results",
    "run_metrics",
}


def build_config(db_path: Path) -> Config:
    config = Config("alembic.ini")
    config.set_main_option("script_location", "llm_eval_platform/migrations")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
    return config


def test_alembic_migrations_are_reproducible(tmp_path: Path) -> None:
    db_path = tmp_path / "migrations.db"
    config = build_config(db_path)

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{db_path}")
    inspector = inspect(engine)
    assert EXPECTED_TABLES.issubset(set(inspector.get_table_names()))

    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
            == "20260319_0001"
        )

    command.downgrade(config, "base")
    inspector = inspect(engine)
    assert inspector.get_table_names() == ["alembic_version"]

    command.upgrade(config, "head")
    inspector = inspect(engine)
    assert EXPECTED_TABLES.issubset(set(inspector.get_table_names()))
    engine.dispose()