from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.prompt import Prompt, PromptClass
from app.models.user import User


def _create_user(
    db_session: Session,
    username: str,
    *,
    is_superuser: bool = False,
    is_active: bool = True,
) -> User:
    user = User(
        username=username,
        hashed_password=get_password_hash("test-pass"),
        is_superuser=is_superuser,
        is_active=is_active,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_headers_for(user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def test_admin_can_list_all_prompts(client: TestClient, db_session: Session) -> None:
    """管理员可以看到所有用户的 Prompt，普通用户只能看到自己的。"""

    owner1 = _create_user(db_session, "owner-1")
    owner2 = _create_user(db_session, "owner-2")
    admin = _create_user(db_session, "admin", is_superuser=True)

    prompt_class = PromptClass(name="测试分类", description=None)
    db_session.add(prompt_class)
    db_session.commit()
    db_session.refresh(prompt_class)

    prompt1 = Prompt(
        name="Prompt1",
        description=None,
        author="u1",
        prompt_class=prompt_class,
        owner_id=owner1.id,
    )
    prompt2 = Prompt(
        name="Prompt2",
        description=None,
        author="u2",
        prompt_class=prompt_class,
        owner_id=owner2.id,
    )
    db_session.add_all([prompt1, prompt2])
    db_session.commit()

    # 普通用户只能看到自己的 Prompt
    user1_headers = _auth_headers_for(owner1)
    resp_user1 = client.get("/api/v1/prompts/", headers=user1_headers)
    assert resp_user1.status_code == 200
    data_user1 = resp_user1.json()
    assert {item["name"] for item in data_user1} == {"Prompt1"}

    # 管理员可以看到所有 Prompt
    admin_headers = _auth_headers_for(admin)
    resp_admin = client.get("/api/v1/prompts/", headers=admin_headers)
    assert resp_admin.status_code == 200
    data_admin = resp_admin.json()
    assert {item["name"] for item in data_admin} == {"Prompt1", "Prompt2"}


def test_non_admin_cannot_access_user_admin_api(
    client: TestClient, db_session: Session
) -> None:
    """非管理员访问用户管理接口应返回 403。"""

    user = _create_user(db_session, "normal-user")
    headers = _auth_headers_for(user)

    resp_list = client.get("/api/v1/users/", headers=headers)
    assert resp_list.status_code == 403

    resp_detail = client.get("/api/v1/users/1", headers=headers)
    assert resp_detail.status_code == 403


def test_admin_can_list_and_update_user(
    client: TestClient, db_session: Session
) -> None:
    """管理员可以查看并更新用户的角色与状态。"""

    admin = _create_user(db_session, "root", is_superuser=True)
    user = _create_user(db_session, "worker")

    headers = _auth_headers_for(admin)

    list_resp = client.get("/api/v1/users/", headers=headers)
    assert list_resp.status_code == 200
    items = list_resp.json()
    usernames = {item["username"] for item in items}
    assert {"root", "worker"}.issubset(usernames)

    patch_resp = client.patch(
        f"/api/v1/users/{user.id}",
        headers=headers,
        json={"is_superuser": True, "is_active": False},
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["is_superuser"] is True
    assert updated["is_active"] is False


def test_admin_cannot_remove_own_superuser_flag(
    client: TestClient, db_session: Session
) -> None:
    """管理员不能通过接口移除自己的管理员权限或禁用自己。"""

    admin = _create_user(db_session, "self-admin", is_superuser=True)
    headers = _auth_headers_for(admin)

    resp_role = client.patch(
        f"/api/v1/users/{admin.id}",
        headers=headers,
        json={"is_superuser": False},
    )
    assert resp_role.status_code == 400

    resp_active = client.patch(
        f"/api/v1/users/{admin.id}",
        headers=headers,
        json={"is_active": False},
    )
    assert resp_active.status_code == 400
