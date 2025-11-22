from __future__ import annotations

from datetime import datetime
from enum import Enum

from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum as PgEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.types import JSONBCompat
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.prompt import Prompt, PromptVersion
    from app.models.result import Result


class TestRunStatus(str, Enum):
    __test__ = False
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TestRun(Base):
    __test__ = False
    __tablename__ = "test_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prompt_version_id: Mapped[int] = mapped_column(
        ForeignKey("prompts_versions.id", ondelete="CASCADE"), nullable=False
    )
    batch_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    temperature: Mapped[float] = mapped_column(nullable=False, default=0.7)
    top_p: Mapped[float] = mapped_column(nullable=False, default=1.0)
    repetitions: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    schema: Mapped[dict | None] = mapped_column(JSONBCompat, nullable=True)
    status: Mapped[TestRunStatus] = mapped_column(
        String(50),
        nullable=False,
        default=TestRunStatus.PENDING,
        server_default=TestRunStatus.PENDING.value,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    prompt_version: Mapped["PromptVersion"] = relationship(
        "PromptVersion", back_populates="test_runs"
    )
    results: Mapped[list["Result"]] = relationship(
        "Result",
        back_populates="test_run",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def last_error(self) -> str | None:
        schema_data = self.schema
        if isinstance(schema_data, dict):
            raw_value = schema_data.get("last_error")
            if isinstance(raw_value, str):
                trimmed = raw_value.strip()
                if trimmed:
                    return trimmed
        return None

    @last_error.setter
    def last_error(self, message: str | None) -> None:
        schema_data = dict(self.schema or {})
        if message and message.strip():
            schema_data["last_error"] = message.strip()
        else:
            schema_data.pop("last_error", None)
        self.schema = schema_data or None

    @property
    def failure_reason(self) -> str | None:
        return self.last_error

    @failure_reason.setter
    def failure_reason(self, message: str | None) -> None:
        self.last_error = message

    @property
    def prompt(self) -> Prompt | None:
        return self.prompt_version.prompt if self.prompt_version else None


__all__ = ["TestRun", "TestRunStatus"]
