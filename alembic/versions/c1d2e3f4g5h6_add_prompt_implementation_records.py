"""add prompt implementation records table

Revision ID: c1d2e3f4g5h6
Revises: b7c3f9e2c4a0
Create Date: 2025-11-23 00:00:01.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c1d2e3f4g5h6"
down_revision: Union[str, None] = "b7c3f9e2c4a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "prompt_implementation_records",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("prompt_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["prompt_id"], ["prompts.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_prompt_implementation_records_prompt_id",
        "prompt_implementation_records",
        ["prompt_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_prompt_implementation_records_prompt_id",
        table_name="prompt_implementation_records",
    )
    op.drop_table("prompt_implementation_records")
