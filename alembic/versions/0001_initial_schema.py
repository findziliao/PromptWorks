"""Create initial tables

Revision ID: 0001_initial_schema
Revises:
Create Date: 2024-10-06 00:00:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


test_run_status_enum = sa.Enum(
    "pending",
    "running",
    "completed",
    "failed",
    native_enum=False,
)


def upgrade() -> None:
    """Apply the initial database schema."""

    # op.execute(...) removed for cross-database compatibility

    op.create_table(
        "prompts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("author", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "version", name="uq_prompt_name_version"),
    )
    op.create_index("ix_prompts_id", "prompts", ["id"], unique=False)

    op.create_table(
        "llm_providers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider_name", sa.String(length=100), nullable=False),
        sa.Column("model_name", sa.String(length=150), nullable=False),
        sa.Column("base_url", sa.String(length=255), nullable=True),
        sa.Column("api_key", sa.Text(), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("is_custom", sa.Boolean(), nullable=False),
        sa.Column("logo_url", sa.String(length=255), nullable=True),
        sa.Column("logo_emoji", sa.String(length=16), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_llm_providers_id", "llm_providers", ["id"], unique=False)

    op.create_table(
        "test_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("prompt_id", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("model_version", sa.String(length=50), nullable=True),
        sa.Column("temperature", sa.Float(), nullable=False),
        sa.Column("top_p", sa.Float(), nullable=False),
        sa.Column("repetitions", sa.Integer(), nullable=False),
        sa.Column("schema", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            test_run_status_enum,
            server_default="pending",
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["prompt_id"], ["prompts.id"], name="test_runs_prompt_id_fkey", ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_test_runs_id", "test_runs", ["id"], unique=False)

    op.create_table(
        "results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("test_run_id", sa.Integer(), nullable=False),
        sa.Column("run_index", sa.Integer(), nullable=False),
        sa.Column("output", sa.Text(), nullable=False),
        sa.Column(
            "parsed_output", sa.JSON(), nullable=True
        ),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["test_run_id"], ["test_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_results_id", "results", ["id"], unique=False)

    op.create_table(
        "metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("result_id", sa.Integer(), nullable=False),
        sa.Column("is_valid_json", sa.Boolean(), nullable=True),
        sa.Column("schema_pass", sa.Boolean(), nullable=True),
        sa.Column(
            "missing_fields", sa.JSON(), nullable=True
        ),
        sa.Column(
            "type_mismatches", sa.JSON(), nullable=True
        ),
        sa.Column("consistency_score", sa.Float(), nullable=True),
        sa.Column("numeric_accuracy", sa.Float(), nullable=True),
        sa.Column("boolean_accuracy", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["result_id"], ["results.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_metrics_id", "metrics", ["id"], unique=False)


def downgrade() -> None:
    """Drop the initial database schema."""

    op.drop_index("ix_metrics_id", table_name="metrics")
    op.drop_table("metrics")
    op.drop_index("ix_results_id", table_name="results")
    op.drop_table("results")
    op.drop_index("ix_test_runs_id", table_name="test_runs")
    op.drop_table("test_runs")
    op.drop_index("ix_llm_providers_id", table_name="llm_providers")
    op.drop_table("llm_providers")
    op.drop_index("ix_prompts_id", table_name="prompts")
    op.drop_table("prompts")

    # op.execute(sa.text("DROP TYPE IF EXISTS test_run_status"))
