"""add completed_at column to prompts

Revision ID: b7c3f9e2c4a0
Revises: 8c4f0b8f9fc1
Create Date: 2025-11-23 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c3f9e2c4a0"
down_revision: Union[str, None] = "8c4f0b8f9fc1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "prompts",
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("prompts", "completed_at")
