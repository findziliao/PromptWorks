from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.prompt import PromptTag, prompt_tag_association
from app.schemas import (
    PromptTagCreate,
    PromptTagListResponse,
    PromptTagRead,
    PromptTagStats,
    PromptTagUpdate,
)

router = APIRouter()


@router.get("/", response_model=PromptTagListResponse)
def list_prompt_tags(*, db: Session = Depends(get_db)) -> PromptTagListResponse:
    """按名称排序返回全部 Prompt 标签及其引用统计。"""

    prompt_count = func.count(prompt_tag_association.c.prompt_id)
    stmt = (
        select(PromptTag, prompt_count.label("prompt_count"))
        .select_from(PromptTag)
        .outerjoin(
            prompt_tag_association,
            PromptTag.id == prompt_tag_association.c.tag_id,
        )
        .group_by(PromptTag.id)
        .order_by(PromptTag.name.asc())
    )

    rows = db.execute(stmt).all()
    items = [
        PromptTagStats(
            id=row.PromptTag.id,
            name=row.PromptTag.name,
            color=row.PromptTag.color,
            created_at=row.PromptTag.created_at,
            updated_at=row.PromptTag.updated_at,
            prompt_count=row.prompt_count or 0,
        )
        for row in rows
    ]

    tagged_prompt_total = db.scalar(
        select(func.count(func.distinct(prompt_tag_association.c.prompt_id)))
    )

    return PromptTagListResponse(
        items=items,
        tagged_prompt_total=tagged_prompt_total or 0,
    )


@router.post("/", response_model=PromptTagRead, status_code=status.HTTP_201_CREATED)
def create_prompt_tag(
    *, db: Session = Depends(get_db), payload: PromptTagCreate
) -> PromptTag:
    """创建新的 Prompt 标签。"""

    prompt_tag = PromptTag(name=payload.name, color=payload.color)
    db.add(prompt_tag)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="同名标签已存在"
        ) from exc
    db.refresh(prompt_tag)
    return prompt_tag


@router.patch("/{tag_id}", response_model=PromptTagRead)
def update_prompt_tag(
    *, db: Session = Depends(get_db), tag_id: int, payload: PromptTagUpdate
) -> PromptTag:
    """更新指定 Prompt 标签的名称或颜色。"""

    prompt_tag = db.get(PromptTag, tag_id)
    if not prompt_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="标签不存在",
        )

    if payload.name is not None:
        prompt_tag.name = payload.name
    if payload.color is not None:
        prompt_tag.color = payload.color

    try:
        db.add(prompt_tag)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="同名标签已存在",
        ) from exc

    db.refresh(prompt_tag)
    return prompt_tag


@router.delete(
    "/{tag_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
def delete_prompt_tag(*, db: Session = Depends(get_db), tag_id: int) -> Response:
    """删除指定 Prompt 标签，若仍有关联则阻止删除。"""

    prompt_tag = db.get(PromptTag, tag_id)
    if not prompt_tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="标签不存在")

    associated = db.scalar(
        select(func.count())
        .select_from(prompt_tag_association)
        .where(prompt_tag_association.c.tag_id == tag_id)
    )

    if associated and associated > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="仍有 Prompt 使用该标签，请先迁移或删除相关 Prompt",
        )

    db.delete(prompt_tag)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
