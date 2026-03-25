"""phase 4 hardening

Revision ID: 20260324_0002
Revises: 20260319_0001
Create Date: 2026-03-24 09:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260324_0002"
down_revision: Union[str, None] = "20260319_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _add_tenant(table: str) -> None:
    op.add_column(table, sa.Column("tenant_id", sa.String(length=64), nullable=True))
    op.create_index(op.f(f"ix_{table}_tenant_id"), table, ["tenant_id"], unique=False)


def upgrade() -> None:
    for table in [
        "datasets",
        "dataset_versions",
        "prompts",
        "prompt_versions",
        "model_configs",
        "experiments",
        "runs",
        "evaluation_results",
        "run_metrics",
    ]:
        _add_tenant(table)

    op.execute("UPDATE datasets SET tenant_id = 'tenant-dev' WHERE tenant_id IS NULL")
    op.execute("UPDATE dataset_versions SET tenant_id = 'tenant-dev' WHERE tenant_id IS NULL")
    op.execute("UPDATE prompts SET tenant_id = 'tenant-dev' WHERE tenant_id IS NULL")
    op.execute("UPDATE prompt_versions SET tenant_id = 'tenant-dev' WHERE tenant_id IS NULL")
    op.execute("UPDATE model_configs SET tenant_id = 'tenant-dev' WHERE tenant_id IS NULL")
    op.execute("UPDATE experiments SET tenant_id = 'tenant-dev' WHERE tenant_id IS NULL")
    op.execute("UPDATE runs SET tenant_id = 'tenant-dev' WHERE tenant_id IS NULL")
    op.execute("UPDATE evaluation_results SET tenant_id = 'tenant-dev' WHERE tenant_id IS NULL")
    op.execute("UPDATE run_metrics SET tenant_id = 'tenant-dev' WHERE tenant_id IS NULL")

    for table in [
        "datasets",
        "dataset_versions",
        "prompts",
        "prompt_versions",
        "model_configs",
        "experiments",
        "runs",
        "evaluation_results",
        "run_metrics",
    ]:
        op.alter_column(table, "tenant_id", nullable=False)

    op.add_column("runs", sa.Column("baseline_run_id", sa.Uuid(), nullable=True))
    op.add_column("runs", sa.Column("result_artifact_uri", sa.String(length=1024), nullable=True))
    op.add_column("runs", sa.Column("regression_status", sa.String(length=50), nullable=True))
    op.add_column("runs", sa.Column("regression_summary", sa.JSON(), nullable=False, server_default="{}"))
    op.create_index(op.f("ix_runs_baseline_run_id"), "runs", ["baseline_run_id"], unique=False)
    op.create_index(op.f("ix_runs_regression_status"), "runs", ["regression_status"], unique=False)
    op.create_foreign_key(op.f("fk_runs_baseline_run_id_runs"), "runs", "runs", ["baseline_run_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint(op.f("fk_runs_baseline_run_id_runs"), "runs", type_="foreignkey")
    op.drop_index(op.f("ix_runs_regression_status"), table_name="runs")
    op.drop_index(op.f("ix_runs_baseline_run_id"), table_name="runs")
    op.drop_column("runs", "regression_summary")
    op.drop_column("runs", "regression_status")
    op.drop_column("runs", "result_artifact_uri")
    op.drop_column("runs", "baseline_run_id")

    for table in [
        "run_metrics",
        "evaluation_results",
        "runs",
        "experiments",
        "model_configs",
        "prompt_versions",
        "prompts",
        "dataset_versions",
        "datasets",
    ]:
        op.drop_index(op.f(f"ix_{table}_tenant_id"), table_name=table)
        op.drop_column(table, "tenant_id")
