from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class PromptTagBase(BaseModel):
    name: str = Field(..., max_length=100)
    color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$")


class PromptTagRead(PromptTagBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromptTagCreate(PromptTagBase):
    """Prompt 标签创建入参"""

    @model_validator(mode="after")
    def normalize_payload(self):
        trimmed = self.name.strip()
        if not trimmed:
            raise ValueError("name 不能为空字符")
        self.name = trimmed
        self.color = self.color.upper()
        return self


class PromptTagUpdate(BaseModel):
    """Prompt 标签更新入参"""

    name: str | None = Field(default=None, max_length=100)
    color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")

    @model_validator(mode="after")
    def normalize_payload(self):
        if self.name is not None:
            trimmed = self.name.strip()
            if not trimmed:
                raise ValueError("name 不能为空字符")
            self.name = trimmed
        if self.color is not None:
            self.color = self.color.upper()
        return self


class PromptTagStats(PromptTagRead):
    prompt_count: int = Field(default=0, ge=0)


class PromptTagListResponse(BaseModel):
    items: list[PromptTagStats]
    tagged_prompt_total: int = Field(default=0, ge=0)


class PromptClassBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None


class PromptClassRead(PromptClassBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromptClassCreate(PromptClassBase):
    """Prompt 分类创建入参"""

    @model_validator(mode="after")
    def validate_payload(self):
        trimmed = self.name.strip()
        if not trimmed:
            raise ValueError("name 不能为空字符")
        self.name = trimmed
        return self


class PromptClassUpdate(BaseModel):
    """Prompt 分类更新入参"""

    name: str | None = Field(default=None, max_length=255)
    description: str | None = None

    @model_validator(mode="after")
    def validate_payload(self):
        if self.name is not None and not self.name.strip():
            raise ValueError("name 不能为空字符")
        return self


class PromptClassStats(PromptClassRead):
    """带统计信息的 Prompt 分类出参"""

    prompt_count: int = Field(default=0, ge=0)
    latest_prompt_updated_at: datetime | None = None


class PromptVersionBase(BaseModel):
    version: str = Field(..., max_length=50)
    content: str


class PromptVersionCreate(PromptVersionBase):
    prompt_id: int


class PromptVersionRead(PromptVersionBase):
    id: int
    prompt_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromptBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    author: str | None = Field(default=None, max_length=100)


class PromptCreate(PromptBase):
    class_id: int | None = Field(default=None, ge=1)
    class_name: str | None = Field(default=None, max_length=255)
    class_description: str | None = None
    version: str = Field(..., max_length=50)
    content: str
    tag_ids: list[int] | None = Field(
        default=None,
        description="为 Prompt 选择的标签 ID 列表，未提供时保持既有设置",
    )

    @model_validator(mode="after")
    def validate_class_reference(self):
        if self.class_id is None and not (self.class_name and self.class_name.strip()):
            raise ValueError("class_id 或 class_name 至少需要提供一个")
        return self


class PromptUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    author: str | None = Field(default=None, max_length=100)
    class_id: int | None = Field(default=None, ge=1)
    class_name: str | None = Field(default=None, max_length=255)
    class_description: str | None = None
    version: str | None = Field(default=None, max_length=50)
    content: str | None = None
    activate_version_id: int | None = Field(default=None, ge=1)
    tag_ids: list[int] | None = Field(
        default=None,
        description="如果提供则覆盖 Prompt 的标签，传空列表代表清空标签",
    )

    @model_validator(mode="after")
    def validate_version_payload(self):
        if (self.version is None) != (self.content is None):
            raise ValueError("更新版本时必须同时提供 version 与 content")
        return self

    @model_validator(mode="after")
    def validate_class_reference(self):
        if (
            self.class_id is None
            and self.class_name is not None
            and not self.class_name.strip()
        ):
            raise ValueError("class_name 不能为空字符串")
        return self


class PromptRead(PromptBase):
    id: int
    owner_id: int | None = None
    prompt_class: PromptClassRead
    current_version: PromptVersionRead | None = None
    versions: list[PromptVersionRead] = Field(default_factory=list)
    tags: list[PromptTagRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PromptShareRequest(BaseModel):
    """请求将 Prompt 分享给其他用户。"""

    username: str = Field(..., max_length=50)
    role: Literal["viewer", "editor"] = Field(
        ..., description="共享角色：viewer 仅可查看，editor 可编辑"
    )


class PromptCollaboratorRead(BaseModel):
    """Prompt 协作者信息出参。"""

    id: int
    user_id: int
    username: str
    role: Literal["viewer", "editor"]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
