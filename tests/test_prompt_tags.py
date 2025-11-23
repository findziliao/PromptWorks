from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.user import User


def _auth_headers(db_session: Session, username: str = "tag-tester") -> dict[str, str]:
    user = db_session.query(User).filter_by(username=username).first()
    if user is None:
        user = User(username=username, hashed_password=get_password_hash("test-pass"))
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def test_list_prompt_tags_returns_empty(client: TestClient) -> None:
    """初始状态下应返回空标签列表与覆盖统计 0。"""

    response = client.get("/api/v1/prompt-tags/")
    assert response.status_code == 200

    data = response.json()
    assert data["items"] == []
    assert data["tagged_prompt_total"] == 0


def test_create_prompt_tag_and_list_stats(client: TestClient) -> None:
    """创建标签后应能在列表中看到并校验字段归一化。"""

    payload = {"name": "主流程", "color": "#409eff"}
    create_resp = client.post("/api/v1/prompt-tags/", json=payload)
    assert create_resp.status_code == 201

    created = create_resp.json()
    assert created["name"] == "主流程"
    assert created["color"] == "#409EFF"

    list_resp = client.get("/api/v1/prompt-tags/")
    assert list_resp.status_code == 200

    data = list_resp.json()
    assert data["tagged_prompt_total"] == 0
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["id"] == created["id"]
    assert item["prompt_count"] == 0


def test_duplicate_tag_creation_returns_400(client: TestClient) -> None:
    """重复名称的标签不允许创建。"""

    payload = {"name": "渠道投放", "color": "#E6A23C"}
    first = client.post("/api/v1/prompt-tags/", json=payload)
    assert first.status_code == 201

    second = client.post("/api/v1/prompt-tags/", json=payload)
    assert second.status_code == 400


def test_delete_tag_blocked_when_in_use(
    client: TestClient, db_session: Session
) -> None:
    """有 Prompt 使用的标签在删除时应返回 409。"""

    tag_resp = client.post(
        "/api/v1/prompt-tags/",
        json={"name": "客服应答", "color": "#67C23A"},
    )
    assert tag_resp.status_code == 201
    tag_id = tag_resp.json()["id"]

    prompt_payload = {
        "name": "客服问候语",
        "version": "v1",
        "content": "您好，我是智能助手，很高兴为您服务",
        "class_name": "客服场景",
        "tag_ids": [tag_id],
    }
    headers = _auth_headers(db_session)

    prompt_resp = client.post("/api/v1/prompts/", headers=headers, json=prompt_payload)
    assert prompt_resp.status_code == 201

    delete_resp = client.delete(f"/api/v1/prompt-tags/{tag_id}")
    assert delete_resp.status_code == 409


def test_delete_unused_tag_succeeds(client: TestClient) -> None:
    """未被使用的标签可正常删除。"""

    create_resp = client.post(
        "/api/v1/prompt-tags/",
        json={"name": "待归档", "color": "#909399"},
    )
    assert create_resp.status_code == 201
    tag_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/v1/prompt-tags/{tag_id}")
    assert delete_resp.status_code == 204

    list_resp = client.get("/api/v1/prompt-tags/")
    data = list_resp.json()
    assert all(item["id"] != tag_id for item in data["items"])


def test_update_prompt_tag_name_and_color(client: TestClient) -> None:
    """可以更新标签名称和颜色，并保持规范化。"""

    create_resp = client.post(
        "/api/v1/prompt-tags/",
        json={"name": "旧名称", "color": "#123456"},
    )
    assert create_resp.status_code == 201
    created = create_resp.json()

    update_resp = client.patch(
        f"/api/v1/prompt-tags/{created['id']}",
        json={"name": "新名称", "color": "#abcdef"},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["name"] == "新名称"
    assert updated["color"] == "#ABCDEF"

    list_resp = client.get("/api/v1/prompt-tags/")
    data = list_resp.json()
    names = {item["name"] for item in data["items"]}
    assert "旧名称" not in names
    assert "新名称" in names


def test_update_prompt_tag_duplicate_name_returns_400(client: TestClient) -> None:
    """更新为重复名称时应返回 400。"""

    first = client.post(
        "/api/v1/prompt-tags/",
        json={"name": "A", "color": "#111111"},
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/prompt-tags/",
        json={"name": "B", "color": "#222222"},
    )
    assert second.status_code == 201
    second_id = second.json()["id"]

    update_resp = client.patch(
        f"/api/v1/prompt-tags/{second_id}",
        json={"name": "A"},
    )
    assert update_resp.status_code == 400
