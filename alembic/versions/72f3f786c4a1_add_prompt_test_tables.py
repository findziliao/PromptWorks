"""add prompt test task/unit/experiment tables

Revision ID: 72f3f786c4a1
Revises: 9b546f1b6f1a
Create Date: 2025-02-14 10:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "72f3f786c4a1"
down_revision: Union[str, None] = "9b546f1b6f1a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    task_status_enum = sa.Enum(
        "draft",
        "ready",
        "running",
        "completed",
        "failed",
        native_enum=False,
    )
    experiment_status_enum = sa.Enum(
        "pending",
        "running",
        "completed",
        "failed",
        "cancelled",
        native_enum=False,
    )

    # task_status_enum.create(bind, checkfirst=True)
    # experiment_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "prompt_test_tasks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("prompt_version_id", sa.Integer(), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("config", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            task_status_enum,
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["prompt_version_id"], ["prompts_versions.id"], ondelete="SET NULL"
        ),
    )

    op.create_table(
        "prompt_test_units",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("prompt_version_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("llm_provider_id", sa.Integer(), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("top_p", sa.Float(), nullable=True),
        sa.Column("rounds", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("prompt_template", sa.Text(), nullable=True),
        sa.Column("variables", sa.JSON(), nullable=True),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("expectations", sa.JSON(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["task_id"], ["prompt_test_tasks.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["prompt_version_id"], ["prompts_versions.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint("task_id", "name", name="uq_prompt_test_unit_task_name"),
    )
    op.create_index(
        "ix_prompt_test_units_task_id", "prompt_test_units", ["task_id"], unique=False
    )

    op.create_table(
        "prompt_test_experiments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("unit_id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.String(length=64), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "status",
            experiment_status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("outputs", sa.JSON(), nullable=True),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["unit_id"], ["prompt_test_units.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_prompt_test_experiments_unit_id",
        "prompt_test_experiments",
        ["unit_id"],
        unique=False,
    )
    op.create_index(
        "ix_prompt_test_experiments_batch_id",
        "prompt_test_experiments",
        ["batch_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_prompt_test_experiments_batch_id",
        table_name="prompt_test_experiments",
    )
    op.drop_index(
        "ix_prompt_test_experiments_unit_id",
        table_name="prompt_test_experiments",
    )
    op.drop_table("prompt_test_experiments")

    op.drop_index("ix_prompt_test_units_task_id", table_name="prompt_test_units")
    op.drop_table("prompt_test_units")

    op.drop_table("prompt_test_tasks")

    bind = op.get_bind()
    # sa.Enum(name="prompt_test_experiment_status").drop(bind, checkfirst=True)
    # sa.Enum(name="prompt_test_task_status").drop(bind, checkfirst=True)
