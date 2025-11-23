from __future__ import annotations

from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import get_current_active_superuser, get_password_hash
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserAdminUpdate, UserRead


router = APIRouter()


@router.get("/", response_model=list[UserRead], summary="列出系统用户，仅管理员")
def list_users(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),  # noqa: ARG001
    q: str | None = Query(default=None, description="按用户名模糊搜索"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> Sequence[User]:
    stmt = select(User)
    if q:
        like_term = f"%{q.strip()}%"
        stmt = stmt.where(User.username.ilike(like_term))

    stmt = stmt.order_by(User.id.asc()).offset(offset).limit(limit)
    return list(db.execute(stmt).scalars().all())


@router.get("/{user_id}", response_model=UserRead, summary="获取指定用户详情，仅管理员")
def get_user(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),  # noqa: ARG001
    user_id: int,
) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )
    return user


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="更新用户状态或角色，仅管理员",
)
def update_user(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
    user_id: int,
    payload: UserAdminUpdate,
) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    if payload.is_superuser is not None:
        if user.id == current_user.id and not payload.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能移除自己的管理员权限",
            )
        user.is_superuser = payload.is_superuser

    if payload.is_active is not None:
        if user.id == current_user.id and payload.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能禁用当前登录的管理员账号",
            )
        user.is_active = payload.is_active

    if payload.password is not None:
        user.hashed_password = get_password_hash(payload.password)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="删除用户，仅管理员",
)
def delete_user(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
    user_id: int,
) -> None:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除当前登录的管理员账号",
        )

    db.delete(user)
    db.commit()


__all__ = ["router"]
