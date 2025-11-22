"""introduce prompt classifications and versions

Revision ID: 0002_prompt_class_and_versions
Revises: 0001_initial_schema
Create Date: 2025-09-20 00:05:00

"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_prompt_class_and_versions"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()

    op.create_table(
        "prompts_class",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
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
    )

    op.add_column(
        "prompts",
        sa.Column("class_id", sa.Integer(), nullable=True),
    )
    op.add_column(
        "prompts",
        sa.Column("current_version_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_prompts_class_id", "prompts", ["class_id"], unique=False)
    op.create_index(
        "ix_prompts_current_version_id", "prompts", ["current_version_id"], unique=False
    )

    op.create_table(
        "prompts_versions",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("prompt_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
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
        sa.ForeignKeyConstraint(["prompt_id"], ["prompts.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("prompt_id", "version", name="uq_prompt_version"),
    )
    op.create_index(
        "ix_prompts_versions_prompt_id", "prompts_versions", ["prompt_id"], unique=False
    )

    connection.execute(
        sa.text(
            "INSERT INTO prompts_class (name, description) VALUES (:name, :description)"
        ),
        {
            "name": "默认分类",
            "description": "迁移自动创建的默认分类",
        },
    )
    # 获取刚刚插入的 ID
    result = connection.execute(sa.text("SELECT last_insert_id()"))
    default_class_id = result.scalar()

    connection.execute(
        sa.text("UPDATE prompts SET class_id = :class_id"),
        {"class_id": default_class_id},
    )

    connection.execute(
        sa.text(
            """
            INSERT INTO prompts_versions (prompt_id, version, content, created_at, updated_at)
            SELECT id, version, content, created_at, updated_at
            FROM prompts
            """
        )
    )

    connection.execute(
        sa.text(
            """
            UPDATE prompts p
            JOIN prompts_versions pv ON pv.prompt_id = p.id AND pv.version = p.version
            SET p.current_version_id = pv.id
            """
        )
    )

    op.drop_constraint("uq_prompt_name_version", "prompts", type_="unique")
    op.create_unique_constraint("uq_prompt_class_name", "prompts", ["class_id", "name"])

    op.create_foreign_key(
        "prompts_class_id_fkey",
        "prompts",
        "prompts_class",
        ["class_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "prompts_current_version_id_fkey",
        "prompts",
        "prompts_versions",
        ["current_version_id"],
        ["id"],
    )

    op.drop_constraint("test_runs_prompt_id_fkey", "test_runs", type_="foreignkey")
    op.alter_column(
        "test_runs",
        "prompt_id",
        new_column_name="prompt_version_id",
        existing_type=sa.Integer(),
    )

    connection.execute(
        sa.text(
            """
            UPDATE test_runs tr
            JOIN prompts_versions pv ON pv.prompt_id = tr.prompt_version_id
            SET tr.prompt_version_id = pv.id
            """
        )
    )

    op.create_foreign_key(
        "test_runs_prompt_version_id_fkey",
        "test_runs",
        "prompts_versions",
        ["prompt_version_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.alter_column(
        "prompts",
        "class_id",
        existing_type=sa.Integer(),
        nullable=False,
    )

    op.drop_column("prompts", "version")
    op.drop_column("prompts", "content")


def downgrade() -> None:
    connection = op.get_bind()

    op.add_column(
        "prompts",
        sa.Column("version", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "prompts",
        sa.Column("content", sa.Text(), nullable=True),
    )

    connection.execute(
        sa.text(
            """
            UPDATE prompts p
            JOIN prompts_versions pv ON pv.id = p.current_version_id
            SET p.version = pv.version,
                p.content = pv.content
            """
        )
    )

    op.drop_constraint(
        "test_runs_prompt_version_id_fkey", "test_runs", type_="foreignkey"
    )

    connection.execute(
        sa.text(
            """
            UPDATE test_runs tr
            JOIN prompts_versions pv ON pv.id = tr.prompt_version_id
            SET tr.prompt_version_id = pv.prompt_id
            """
        )
    )

    op.alter_column("test_runs", "prompt_version_id", new_column_name="prompt_id")
    op.create_foreign_key(
        "test_runs_prompt_id_fkey",
        "test_runs",
        "prompts",
        ["prompt_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_constraint("prompts_current_version_id_fkey", "prompts", type_="foreignkey")
    op.drop_constraint("prompts_class_id_fkey", "prompts", type_="foreignkey")
    op.drop_constraint("uq_prompt_class_name", "prompts", type_="unique")

    connection.execute(
        sa.text("UPDATE prompts SET class_id = NULL, current_version_id = NULL"),
    )

    op.create_unique_constraint(
        "uq_prompt_name_version", "prompts", ["name", "version"]
    )

    op.drop_index("ix_prompts_current_version_id", table_name="prompts")
    op.drop_index("ix_prompts_class_id", table_name="prompts")
    op.drop_column("prompts", "current_version_id")
    op.drop_column("prompts", "class_id")

    op.drop_index("ix_prompts_versions_prompt_id", table_name="prompts_versions")
    op.drop_table("prompts_versions")

    op.drop_table("prompts_class")

    connection.execute(
        sa.text(
            """
            UPDATE prompts
            SET version = COALESCE(version, 'v1'),
                content = COALESCE(content, '')
            """
        )
    )

    op.alter_column(
        "prompts",
        "version",
        existing_type=sa.String(length=50),
        nullable=False,
    )
    op.alter_column(
        "prompts",
        "content",
        existing_type=sa.Text(),
        nullable=False,
    )
