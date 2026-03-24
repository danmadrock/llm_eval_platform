"""init tables

Revision ID: 20260319_0001
Revises:
Create Date: 2026-03-23 13:46:14.584096

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260319_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UUID_TYPE = sa.Uuid()
TIMESTAMP_TYPE = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("task_type", sa.String(length=100), nullable=False),
        sa.Column("created_at", TIMESTAMP_TYPE, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TIMESTAMP_TYPE, server_default=sa.func.now(), nullable=False),
        sa.Column("id", UUID_TYPE, nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_datasets")),
        sa.UniqueConstraint("name", name=op.f("uq_datasets_name")),
    )
    op.create_index(op.f("ix_datasets_name"), "datasets", ["name"], unique=True)
    op.create_index(op.f("ix_datasets_task_type"), "datasets", ["task_type"], unique=False)

    op.create_table(
        "experiments",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", TIMESTAMP_TYPE, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TIMESTAMP_TYPE, server_default=sa.func.now(), nullable=False),
        sa.Column("id", UUID_TYPE, nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_experiments")),
        sa.UniqueConstraint("name", name=op.f("uq_experiments_name")),
    )
    op.create_index(op.f("ix_experiments_name"), "experiments", ["name"], unique=True)

    op.create_table(
        "model_configs",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("model_name", sa.String(length=255), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", TIMESTAMP_TYPE, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TIMESTAMP_TYPE, server_default=sa.func.now(), nullable=False),
        sa.Column("id", UUID_TYPE, nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_configs")),
        sa.UniqueConstraint("name", name=op.f("uq_model_configs_name")),
    )
    op.create_index(
        op.f("ix_model_configs_model_name"), "model_configs", ["model_name"], unique=False
    )
    op.create_index(op.f("ix_model_configs_name"), "model_configs", ["name"], unique=True)
    op.create_index(op.f("ix_model_configs_provider"), "model_configs", ["provider"], unique=False)

    op.create_table(
        "prompts",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", TIMESTAMP_TYPE, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TIMESTAMP_TYPE, server_default=sa.func.now(), nullable=False),
        sa.Column("id", UUID_TYPE, nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_prompts")),
        sa.UniqueConstraint("name", name=op.f("uq_prompts_name")),
    )
    op.create_index(op.f("ix_prompts_name"), "prompts", ["name"], unique=True)

    op.create_table(
        "dataset_versions",
        sa.Column("dataset_id", UUID_TYPE, nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("object_uri", sa.String(length=1024), nullable=False),
        sa.Column("example_count", sa.Integer(), nullable=False),
        sa.Column("created_at", TIMESTAMP_TYPE, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TIMESTAMP_TYPE, server_default=sa.func.now(), nullable=False),
        sa.Column("id", UUID_TYPE, nullable=False),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            name=op.f("fk_dataset_versions_dataset_id_datasets"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dataset_versions")),
        sa.UniqueConstraint("dataset_id", "version", name=op.f("uq_dataset_versions_dataset_id")),
    )
    op.create_index(
        op.f("ix_dataset_versions_dataset_id"), "dataset_versions", ["dataset_id"], unique=False
    )

    op.create_table(
        "prompt_versions",
        sa.Column("prompt_id", UUID_TYPE, nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("template", sa.Text(), nullable=False),
        sa.Column("created_at", TIMESTAMP_TYPE, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TIMESTAMP_TYPE, server_default=sa.func.now(), nullable=False),
        sa.Column("id", UUID_TYPE, nullable=False),
        sa.ForeignKeyConstraint(
            ["prompt_id"],
            ["prompts.id"],
            name=op.f("fk_prompt_versions_prompt_id_prompts"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_prompt_versions")),
        sa.UniqueConstraint("prompt_id", "version", name=op.f("uq_prompt_versions_prompt_id")),
    )
    op.create_index(
        op.f("ix_prompt_versions_prompt_id"), "prompt_versions", ["prompt_id"], unique=False
    )

    op.create_table(
        "runs",
        sa.Column("experiment_id", UUID_TYPE, nullable=False),
        sa.Column("dataset_version_id", UUID_TYPE, nullable=False),
        sa.Column("prompt_version_id", UUID_TYPE, nullable=False),
        sa.Column("model_config_id", UUID_TYPE, nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("total_examples", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processed_examples", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_examples", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_examples", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", TIMESTAMP_TYPE, nullable=True),
        sa.Column("completed_at", TIMESTAMP_TYPE, nullable=True),
        sa.Column("created_at", TIMESTAMP_TYPE, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TIMESTAMP_TYPE, server_default=sa.func.now(), nullable=False),
        sa.Column("id", UUID_TYPE, nullable=False),
        sa.ForeignKeyConstraint(
            ["dataset_version_id"],
            ["dataset_versions.id"],
            name=op.f("fk_runs_dataset_version_id_dataset_versions"),
        ),
        sa.ForeignKeyConstraint(
            ["experiment_id"],
            ["experiments.id"],
            name=op.f("fk_runs_experiment_id_experiments"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["model_config_id"],
            ["model_configs.id"],
            name=op.f("fk_runs_model_config_id_model_configs"),
        ),
        sa.ForeignKeyConstraint(
            ["prompt_version_id"],
            ["prompt_versions.id"],
            name=op.f("fk_runs_prompt_version_id_prompt_versions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_runs")),
    )
    op.create_index(
        op.f("ix_runs_dataset_version_id"), "runs", ["dataset_version_id"], unique=False
    )
    op.create_index(op.f("ix_runs_experiment_id"), "runs", ["experiment_id"], unique=False)
    op.create_index(op.f("ix_runs_model_config_id"), "runs", ["model_config_id"], unique=False)
    op.create_index(op.f("ix_runs_prompt_version_id"), "runs", ["prompt_version_id"], unique=False)
    op.create_index(op.f("ix_runs_status"), "runs", ["status"], unique=False)

    op.create_table(
        "evaluation_results",
        sa.Column("run_id", UUID_TYPE, nullable=False),
        sa.Column("example_index", sa.Integer(), nullable=False),
        sa.Column("input_payload", sa.JSON(), nullable=False),
        sa.Column("expected_output", sa.JSON(), nullable=True),
        sa.Column("actual_output", sa.JSON(), nullable=True),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", TIMESTAMP_TYPE, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TIMESTAMP_TYPE, server_default=sa.func.now(), nullable=False),
        sa.Column("id", UUID_TYPE, nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["runs.id"],
            name=op.f("fk_evaluation_results_run_id_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluation_results")),
        sa.UniqueConstraint("run_id", "example_index", name=op.f("uq_evaluation_results_run_id")),
    )
    op.create_index(
        op.f("ix_evaluation_results_run_id"), "evaluation_results", ["run_id"], unique=False
    )
    op.create_index(
        op.f("ix_evaluation_results_status"), "evaluation_results", ["status"], unique=False
    )

    op.create_table(
        "run_metrics",
        sa.Column("run_id", UUID_TYPE, nullable=False),
        sa.Column("metric_name", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("computed_at", TIMESTAMP_TYPE, nullable=False),
        sa.Column("created_at", TIMESTAMP_TYPE, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", TIMESTAMP_TYPE, server_default=sa.func.now(), nullable=False),
        sa.Column("id", UUID_TYPE, nullable=False),
        sa.ForeignKeyConstraint(
            ["run_id"],
            ["runs.id"],
            name=op.f("fk_run_metrics_run_id_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_run_metrics")),
        sa.UniqueConstraint("run_id", "metric_name", name=op.f("uq_run_metrics_run_id")),
    )
    op.create_index(
        op.f("ix_run_metrics_metric_name"), "run_metrics", ["metric_name"], unique=False
    )
    op.create_index(op.f("ix_run_metrics_run_id"), "run_metrics", ["run_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_run_metrics_run_id"), table_name="run_metrics")
    op.drop_index(op.f("ix_run_metrics_metric_name"), table_name="run_metrics")
    op.drop_table("run_metrics")
    op.drop_index(op.f("ix_evaluation_results_status"), table_name="evaluation_results")
    op.drop_index(op.f("ix_evaluation_results_run_id"), table_name="evaluation_results")
    op.drop_table("evaluation_results")
    op.drop_index(op.f("ix_runs_status"), table_name="runs")
    op.drop_index(op.f("ix_runs_prompt_version_id"), table_name="runs")
    op.drop_index(op.f("ix_runs_model_config_id"), table_name="runs")
    op.drop_index(op.f("ix_runs_experiment_id"), table_name="runs")
    op.drop_index(op.f("ix_runs_dataset_version_id"), table_name="runs")
    op.drop_table("runs")
    op.drop_index(op.f("ix_prompt_versions_prompt_id"), table_name="prompt_versions")
    op.drop_table("prompt_versions")
    op.drop_index(op.f("ix_dataset_versions_dataset_id"), table_name="dataset_versions")
    op.drop_table("dataset_versions")
    op.drop_index(op.f("ix_prompts_name"), table_name="prompts")
    op.drop_table("prompts")
    op.drop_index(op.f("ix_model_configs_provider"), table_name="model_configs")
    op.drop_index(op.f("ix_model_configs_name"), table_name="model_configs")
    op.drop_index(op.f("ix_model_configs_model_name"), table_name="model_configs")
    op.drop_table("model_configs")
    op.drop_index(op.f("ix_experiments_name"), table_name="experiments")
    op.drop_table("experiments")
    op.drop_index(op.f("ix_datasets_task_type"), table_name="datasets")
    op.drop_index(op.f("ix_datasets_name"), table_name="datasets")
    op.drop_table("datasets")