"""refactor llm providers and add models table

Revision ID: 0004_refactor_llm_providers
Revises: efea0d0224c5
Create Date: 2025-10-05 10:32:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0004_refactor_llm_providers"
down_revision: Union[str, None] = "efea0d0224c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "llm_providers",
        sa.Column("provider_key", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "llm_providers",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "llm_providers",
        sa.Column(
            "is_archived",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "llm_providers",
        sa.Column("default_model_name", sa.String(length=150), nullable=True),
    )

    op.drop_column("llm_providers", "parameters")
    op.drop_column("llm_providers", "model_name")

    op.create_index(
        "ix_llm_providers_provider_key",
        "llm_providers",
        ["provider_key"],
        unique=False,
    )

    op.create_table(
        "llm_models",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("capability", sa.String(length=120), nullable=True),
        sa.Column("quota", sa.String(length=120), nullable=True),
        sa.Column(
            "parameters", sa.JSON(), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["provider_id"],
            ["llm_providers.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_id", "name", name="uq_llm_model_provider_name"),
    )
    op.create_index(
        "ix_llm_models_provider_id", "llm_models", ["provider_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_llm_models_provider_id", table_name="llm_models")
    op.drop_table("llm_models")

    op.drop_index("ix_llm_providers_provider_key", table_name="llm_providers")

    op.add_column(
        "llm_providers",
        sa.Column(
            "model_name",
            sa.String(length=150),
            nullable=False,
            server_default="default-model",
        ),
    )
    op.add_column(
        "llm_providers",
        sa.Column(
            "parameters",
            sa.JSON(),
            nullable=False,
            server_default=None,
        ),
    )

    op.drop_column("llm_providers", "default_model_name")
    op.drop_column("llm_providers", "is_archived")
    op.drop_column("llm_providers", "description")
    op.drop_column("llm_providers", "provider_key")
