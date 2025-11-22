from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.api.v1.endpoints.prompts import _user_can_edit_prompt
from app.models.prompt import Prompt, PromptCollaborator
from app.models.user import User


def _auth_headers_for(user: User) -> dict[str, str]:
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def test_prompt_is_isolated_between_users(
    client: TestClient, db_session: Session
) -> None:
    """不同用户默认只能看到自己创建的 Prompt。"""

    owner = User(username="owner", hashed_password=get_password_hash("owner-pwd"))
    other = User(username="other", hashed_password=get_password_hash("other-pwd"))
    db_session.add_all([owner, other])
    db_session.commit()
    db_session.refresh(owner)
    db_session.refresh(other)

    owner_headers = _auth_headers_for(owner)
    other_headers = _auth_headers_for(other)

    create_resp = client.post(
        "/api/v1/prompts/",
        headers=owner_headers,
        json={
            "name": "私有提示",
            "version": "v1",
            "content": "仅 owner 可见",
            "class_name": "测试分类",
        },
    )
    assert create_resp.status_code == 201
    prompt_id = create_resp.json()["id"]

    list_resp = client.get("/api/v1/prompts/", headers=other_headers)
    assert list_resp.status_code == 200
    assert all(item["id"] != prompt_id for item in list_resp.json())

    get_resp = client.get(f"/api/v1/prompts/{prompt_id}", headers=other_headers)
    assert get_resp.status_code == 403


def test_shared_prompt_viewer_can_read_but_not_edit(
    client: TestClient, db_session: Session
) -> None:
    """viewer 协作者可以查看共享 Prompt，但不能修改。"""

    owner = User(username="owner2", hashed_password=get_password_hash("owner-pwd"))
    viewer = User(username="viewer", hashed_password=get_password_hash("viewer-pwd"))
    db_session.add_all([owner, viewer])
    db_session.commit()
    db_session.refresh(owner)
    db_session.refresh(viewer)

    owner_headers = _auth_headers_for(owner)
    viewer_headers = _auth_headers_for(viewer)

    create_resp = client.post(
        "/api/v1/prompts/",
        headers=owner_headers,
        json={
            "name": "共享提示",
            "version": "v1",
            "content": "共享内容",
            "class_name": "共享分类",
        },
    )
    assert create_resp.status_code == 201
    prompt_id = create_resp.json()["id"]

    share_resp = client.post(
        f"/api/v1/prompts/{prompt_id}/share",
        headers=owner_headers,
        json={"username": "viewer", "role": "viewer"},
    )
    assert share_resp.status_code == 201
    collab = share_resp.json()
    assert collab["username"] == "viewer"
    assert collab["role"] == "viewer"

    list_resp = client.get("/api/v1/prompts/", headers=viewer_headers)
    assert any(item["id"] == prompt_id for item in list_resp.json())

    get_resp = client.get(f"/api/v1/prompts/{prompt_id}", headers=viewer_headers)
    assert get_resp.status_code == 200

    update_resp = client.put(
        f"/api/v1/prompts/{prompt_id}",
        headers=viewer_headers,
        json={"description": "不应生效"},
    )
    assert update_resp.status_code == 403


def test_shared_prompt_editor_can_update(
    client: TestClient, db_session: Session
) -> None:
    """editor 协作者可以更新共享 Prompt。"""

    owner = User(username="owner3", hashed_password=get_password_hash("owner-pwd"))
    editor = User(username="editor", hashed_password=get_password_hash("editor-pwd"))
    db_session.add_all([owner, editor])
    db_session.commit()
    db_session.refresh(owner)
    db_session.refresh(editor)

    owner_headers = _auth_headers_for(owner)
    editor_headers = _auth_headers_for(editor)

    create_resp = client.post(
        "/api/v1/prompts/",
        headers=owner_headers,
        json={
            "name": "可编辑提示",
            "version": "v1",
            "content": "初始内容",
            "class_name": "编辑分类",
        },
    )
    assert create_resp.status_code == 201
    prompt_id = create_resp.json()["id"]

    share_resp = client.post(
        f"/api/v1/prompts/{prompt_id}/share",
        headers=owner_headers,
        json={"username": "editor", "role": "editor"},
    )
    assert share_resp.status_code == 201

    # 直接验证权限辅助函数，确保编辑者具备编辑权限
    all_collabs = db_session.query(PromptCollaborator).all()
    assert any(c.prompt_id == prompt_id and c.user_id == editor.id for c in all_collabs)

    prompt_obj = db_session.get(Prompt, prompt_id)
    assert prompt_obj is not None
    assert _user_can_edit_prompt(db_session, prompt_obj, editor) is True

    update_resp = client.put(
        f"/api/v1/prompts/{prompt_id}",
        headers=editor_headers,
        json={"description": "由编辑者更新"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["description"] == "由编辑者更新"
