"""add users table and prompt ownership/collaborators

Revision ID: 8c4f0b8f9fc1
Revises: 6d6a1f6dfb41
Create Date: 2025-11-22 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c4f0b8f9fc1"
down_revision: Union[str, None] = "6d6a1f6dfb41"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "is_superuser",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("ix_users_id", "users", ["id"], unique=False)
    op.create_index("ix_users_username", "users", ["username"], unique=False)

    op.add_column(
        "prompts",
        sa.Column("owner_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_prompts_owner_id", "prompts", ["owner_id"], unique=False)
    op.create_foreign_key(
        "prompts_owner_id_fkey",
        "prompts",
        "users",
        ["owner_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.drop_constraint("uq_prompt_class_name", "prompts", type_="unique")
    op.create_unique_constraint(
        "uq_prompt_class_name",
        "prompts",
        ["class_id", "name", "owner_id"],
    )

    op.create_table(
        "prompt_collaborators",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("prompt_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["prompt_id"],
            ["prompts.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "prompt_id",
            "user_id",
            name="uq_prompt_collaborators_prompt_user",
        ),
    )
    op.create_index(
        "ix_prompt_collaborators_prompt_id",
        "prompt_collaborators",
        ["prompt_id"],
        unique=False,
    )
    op.create_index(
        "ix_prompt_collaborators_user_id",
        "prompt_collaborators",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_prompt_collaborators_user_id",
        table_name="prompt_collaborators",
    )
    op.drop_index(
        "ix_prompt_collaborators_prompt_id",
        table_name="prompt_collaborators",
    )
    op.drop_table("prompt_collaborators")

    op.drop_constraint(
        "prompts_owner_id_fkey",
        "prompts",
        type_="foreignkey",
    )
    op.drop_index("ix_prompts_owner_id", table_name="prompts")
    op.drop_constraint("uq_prompt_class_name", "prompts", type_="unique")
    op.create_unique_constraint(
        "uq_prompt_class_name",
        "prompts",
        ["class_id", "name"],
    )
    op.drop_column("prompts", "owner_id")

    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_id", table_name="users")
    op.drop_table("users")
