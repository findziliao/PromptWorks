from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:  # pragma: no cover - 类型检查辅助
    from app.models.test_run import TestRun
    from app.models.user import User

from app.models.base import Base


prompt_tag_association = Table(
    "prompt_tag_links",
    Base.metadata,
    Column(
        "prompt_id",
        ForeignKey("prompts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id",
        ForeignKey("prompt_tags.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class PromptClass(Base):
    __tablename__ = "prompts_class"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    prompts: Mapped[list["Prompt"]] = relationship(
        "Prompt",
        back_populates="prompt_class",
        cascade="all, delete-orphan",
    )


class PromptTag(Base):
    __tablename__ = "prompt_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    color: Mapped[str] = mapped_column(String(7), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    prompts: Mapped[list["Prompt"]] = relationship(
        "Prompt",
        secondary=prompt_tag_association,
        back_populates="tags",
    )


class PromptCollaborator(Base):
    __tablename__ = "prompt_collaborators"
    __table_args__ = (
        UniqueConstraint(
            "prompt_id", "user_id", name="uq_prompt_collaborators_prompt_user"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prompt_id: Mapped[int] = mapped_column(
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    prompt: Mapped["Prompt"] = relationship("Prompt", back_populates="collaborators")
    user: Mapped["User"] = relationship("User", back_populates="shared_prompts")

    @property
    def username(self) -> str:
        """Convenience accessor used in API schemas."""

        return self.user.username if self.user is not None else ""


class Prompt(Base):
    __tablename__ = "prompts"
    __table_args__ = (
        UniqueConstraint("class_id", "name", "owner_id", name="uq_prompt_class_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    class_id: Mapped[int] = mapped_column(
        ForeignKey(
            "prompts_class.id",
            ondelete="CASCADE",
            name="prompts_class_id_fkey",
        ),
        nullable=False,
        index=True,
    )
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    author: Mapped[str | None] = mapped_column(String(100), nullable=True)
    current_version_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "prompts_versions.id",
            name="prompts_current_version_id_fkey",
            use_alter=True,
        ),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    prompt_class: Mapped[PromptClass] = relationship(
        "PromptClass", back_populates="prompts"
    )
    owner: Mapped["User | None"] = relationship("User", back_populates="prompts")
    versions: Mapped[list["PromptVersion"]] = relationship(
        "PromptVersion",
        back_populates="prompt",
        cascade="all, delete-orphan",
        order_by="PromptVersion.created_at.desc()",
        foreign_keys="PromptVersion.prompt_id",
        primaryjoin="Prompt.id == PromptVersion.prompt_id",
    )
    current_version: Mapped["PromptVersion | None"] = relationship(
        "PromptVersion",
        foreign_keys="Prompt.current_version_id",
        primaryjoin="Prompt.current_version_id == PromptVersion.id",
        post_update=True,
    )
    tags: Mapped[list["PromptTag"]] = relationship(
        "PromptTag",
        secondary=prompt_tag_association,
        back_populates="prompts",
    )
    collaborators: Mapped[list["PromptCollaborator"]] = relationship(
        "PromptCollaborator",
        back_populates="prompt",
        cascade="all, delete-orphan",
    )


class PromptVersion(Base):
    __tablename__ = "prompts_versions"
    __table_args__ = (
        UniqueConstraint("prompt_id", "version", name="uq_prompt_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prompt_id: Mapped[int] = mapped_column(
        ForeignKey(
            "prompts.id",
            ondelete="CASCADE",
            name="prompts_versions_prompt_id_fkey",
        ),
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    prompt: Mapped["Prompt"] = relationship(
        "Prompt",
        back_populates="versions",
        foreign_keys="PromptVersion.prompt_id",
        primaryjoin="PromptVersion.prompt_id == Prompt.id",
    )
    test_runs: Mapped[list["TestRun"]] = relationship(
        "TestRun", back_populates="prompt_version", cascade="all, delete-orphan"
    )


__all__ = [
    "PromptClass",
    "Prompt",
    "PromptTag",
    "PromptVersion",
    "PromptCollaborator",
]
