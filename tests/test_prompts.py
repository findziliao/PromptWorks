from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash
from app.models.prompt import PromptClass, PromptTag
from app.models.user import User


def _auth_headers(db_session: Session, username: str = "tester") -> dict[str, str]:
    user = db_session.query(User).filter_by(username=username).first()
    if user is None:
        user = User(username=username, hashed_password=get_password_hash("test-pass"))
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    token = create_access_token({"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def test_create_and_list_prompts(client: TestClient, db_session: Session):
    """验证创建 Prompt 时可绑定标签，并在列表与详情接口中返回"""
    # 准备多个标签，保证创建 Prompt 时能够成功绑定多项标签信息
    tag_notice = PromptTag(name="通知", color="#1D4ED8")
    tag_email = PromptTag(name="邮件", color="#F97316")
    db_session.add_all([tag_notice, tag_email])
    db_session.commit()

    # 通过创建接口写入首个 Prompt，并指定需要的标签与分类名称
    headers = _auth_headers(db_session)
    payload = {
        "name": "订单确认",
        "version": "v1",
        "content": "请基于输入生成客户确认邮件",
        "description": "默认中文邮件模版",
        "author": "tester",
        "class_name": "通知",
        "tag_ids": [tag_notice.id, tag_email.id],
    }
    response = client.post("/api/v1/prompts/", headers=headers, json=payload)
    assert response.status_code == 201
    data = response.json()

    # 校验创建后返回的数据结构，确保版本与标签信息完整
    assert data["name"] == payload["name"]
    assert data["prompt_class"]["name"] == payload["class_name"]
    assert data["current_version"]["version"] == payload["version"]
    assert data["current_version"]["content"] == payload["content"]
    assert len(data["versions"]) == 1
    assert [tag["id"] for tag in data["tags"]] == payload["tag_ids"]

    # 列表接口应返回刚创建的 Prompt，验证分页接口的最基本行为
    list_resp = client.get("/api/v1/prompts/", headers=headers)
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert len(items) == 1
    assert items[0]["name"] == payload["name"]
    assert items[0]["prompt_class"]["name"] == payload["class_name"]
    assert items[0]["current_version"]["version"] == payload["version"]
    assert [tag["id"] for tag in items[0]["tags"]] == payload["tag_ids"]

    # 再次读取标签接口，确认标签数据与 Prompt 绑定后的状态一致
    tag_list_resp = client.get("/api/v1/prompt-tags/")
    assert tag_list_resp.status_code == 200
    tag_list = tag_list_resp.json()
    assert tag_list["tagged_prompt_total"] == 1
    tag_names = {tag["name"] for tag in tag_list["items"]}
    assert {"通知", "邮件"}.issubset(tag_names)


def test_update_and_delete_prompt(client: TestClient, db_session: Session):
    """验证 Prompt 更新时可切换标签，删除后无法再访问"""
    # 预先创建两个标签，提供更新前后的标签对比
    tag_initial = PromptTag(name="流程校验", color="#10B981")
    tag_new = PromptTag(name="归档", color="#6B7280")
    db_session.add_all([tag_initial, tag_new])
    db_session.commit()

    # 创建初始 Prompt，先绑定初始标签，为后续更新做准备
    headers = _auth_headers(db_session)
    create_resp = client.post(
        "/api/v1/prompts/",
        headers=headers,
        json={
            "name": "测试提示",
            "version": "v1",
            "content": "原始内容",
            "class_name": "实验",
            "tag_ids": [tag_initial.id],
        },
    )
    assert create_resp.status_code == 201
    prompt = create_resp.json()
    prompt_id = prompt["id"]
    assert [tag["id"] for tag in prompt["tags"]] == [tag_initial.id]

    # 更新 Prompt 时新增版本与标签，验证版本堆叠逻辑与标签覆盖逻辑
    update_resp = client.put(
        f"/api/v1/prompts/{prompt_id}",
        headers=headers,
        json={
            "content": "更新后的内容",
            "version": "v2",
            "tag_ids": [tag_new.id],
        },
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["current_version"]["content"] == "更新后的内容"
    assert updated["current_version"]["version"] == "v2"
    assert len(updated["versions"]) == 2
    assert [tag["id"] for tag in updated["tags"]] == [tag_new.id]

    # 清空标签列表，验证显式传入空数组时可清除所有标签
    clear_tags_resp = client.put(
        f"/api/v1/prompts/{prompt_id}",
        headers=headers,
        json={"tag_ids": []},
    )
    assert clear_tags_resp.status_code == 200
    assert clear_tags_resp.json()["tags"] == []

    # 删除 Prompt 后再次访问应返回 404，确保删除操作彻底
    delete_resp = client.delete(f"/api/v1/prompts/{prompt_id}", headers=headers)
    assert delete_resp.status_code == 204

    not_found_resp = client.get(f"/api/v1/prompts/{prompt_id}", headers=headers)
    assert not_found_resp.status_code == 404


def test_create_prompt_with_existing_class_id(client: TestClient, db_session: Session):
    """使用既有分类 ID 创建 Prompt 时应复用分类并补充描述"""
    # 构造一个未填写描述的分类，稍后通过接口传入描述补齐
    prompt_class = PromptClass(name="系统工作流")
    db_session.add(prompt_class)
    db_session.commit()

    # 使用 class_id 创建 Prompt，同时提供 class_description 以补充分类信息
    headers = _auth_headers(db_session)
    payload = {
        "name": "系统问候",
        "version": "v1",
        "content": "请输出系统欢迎语",
        "author": "system",
        "description": "系统问候语示例",
        "class_id": prompt_class.id,
        "class_description": "系统分类的文字说明",
    }
    response = client.post("/api/v1/prompts/", headers=headers, json=payload)
    assert response.status_code == 201
    data = response.json()

    # 验证分类被复用且描述被补齐，同时由于未传标签需返回空标签
    assert data["prompt_class"]["id"] == prompt_class.id
    assert data["prompt_class"]["description"] is None
    assert data["tags"] == []

    db_session.refresh(prompt_class)
    assert prompt_class.description is None


def test_create_prompt_with_invalid_class_id(client: TestClient, db_session: Session):
    """引用不存在的分类 ID 时应返回 404"""
    # 构造仅包含 class_id 的请求体，触发分类不存在的分支
    headers = _auth_headers(db_session)

    payload = {
        "name": "异常分类",
        "version": "v1",
        "content": "随便写点内容",
        "class_id": 999,
    }
    response = client.post("/api/v1/prompts/", headers=headers, json=payload)
    assert response.status_code == 404


def test_create_prompt_with_invalid_tag_ids(client: TestClient, db_session: Session):
    """当标签 ID 不存在时应触发 404 异常"""
    # 仅传入不存在的标签 ID，验证 _resolve_prompt_tags 的缺失标签分支
    headers = _auth_headers(db_session)

    payload = {
        "name": "标签检查",
        "version": "v1",
        "content": "测试缺失标签",
        "class_name": "校验",
        "tag_ids": [123456],
    }
    response = client.post("/api/v1/prompts/", headers=headers, json=payload)
    assert response.status_code == 404


def test_create_prompt_adds_new_version_for_existing_prompt(
    client: TestClient, db_session: Session
):
    """重复调用创建接口时应在既有 Prompt 上追加新版本"""
    # 预置两个标签，为第二次创建时验证去重与顺序
    tag_primary = PromptTag(name="主要", color="#1F2937")
    tag_secondary = PromptTag(name="次要", color="#E5E7EB")
    db_session.add_all([tag_primary, tag_secondary])
    db_session.commit()

    # 首次创建 Prompt，使用 class_name 触发分类自动创建
    headers = _auth_headers(db_session)
    first_payload = {
        "name": "多版本提示",
        "version": "v1",
        "content": "第一版内容",
        "class_name": "知识库",
    }
    first_resp = client.post("/api/v1/prompts/", headers=headers, json=first_payload)
    assert first_resp.status_code == 201

    # 再次提交相同的名称但不同版本，验证版本追加与字段更新
    second_payload = {
        "name": "多版本提示",
        "version": "v2",
        "content": "第二版优化内容",
        "description": "更精准的提示词",
        "author": "editor",
        "class_name": "知识库",
        "class_description": "知识库分类补充说明",
        "tag_ids": [tag_primary.id, tag_primary.id, tag_secondary.id],
    }
    second_resp = client.post("/api/v1/prompts/", headers=headers, json=second_payload)
    assert second_resp.status_code == 201
    data = second_resp.json()

    # 验证版本数量、当前版本、描述与作者均被更新
    assert data["current_version"]["version"] == "v2"
    assert len(data["versions"]) == 2
    assert data["description"] == "更精准的提示词"
    assert data["author"] == "editor"
    assert [tag["id"] for tag in data["tags"]] == [tag_primary.id, tag_secondary.id]

    prompt_class = db_session.get(PromptClass, data["prompt_class"]["id"])
    assert prompt_class is not None
    assert prompt_class.description == "知识库分类补充说明"


def test_create_prompt_conflicting_version_returns_400(
    client: TestClient, db_session: Session
) -> None:
    """再次创建已存在版本时应返回 400"""
    # 首次创建 Prompt，后续将以同版本重复提交
    headers = _auth_headers(db_session)

    initial_payload = {
        "name": "版本冲突",
        "version": "v1",
        "content": "初始版本",
        "class_name": "冲突演示",
    }
    initial_resp = client.post(
        "/api/v1/prompts/", headers=headers, json=initial_payload
    )
    assert initial_resp.status_code == 201

    # 使用相同版本再次创建，验证重复版本被拒绝
    conflict_payload = {
        "name": "版本冲突",
        "version": "v1",
        "content": "重复内容",
        "class_name": "冲突演示",
    }
    conflict_resp = client.post(
        "/api/v1/prompts/", headers=headers, json=conflict_payload
    )
    assert conflict_resp.status_code == 400


def test_list_prompts_with_query_filter(client: TestClient, db_session: Session):
    """模糊搜索参数应支持按照名称或分类过滤"""
    # 创建两个不同分类的 Prompt，确保搜索能区分结果
    headers = _auth_headers(db_session)
    client.post(
        "/api/v1/prompts/",
        headers=headers,
        json={
            "name": "客服问候",
            "version": "v1",
            "content": "您好，很高兴为您服务",
            "author": "service",
            "class_name": "客服场景",
        },
    )
    client.post(
        "/api/v1/prompts/",
        headers=headers,
        json={
            "name": "订单提醒",
            "version": "v1",
            "content": "请告知客户订单发货进度",
            "author": "order",
            "class_name": "通知场景",
        },
    )

    # 根据 class_name 关键词进行模糊搜索，确认仅返回匹配项
    search_resp = client.get("/api/v1/prompts/", headers=headers, params={"q": "客服"})
    assert search_resp.status_code == 200
    results = search_resp.json()
    assert len(results) == 1
    assert results[0]["name"] == "客服问候"


def test_update_prompt_switch_class_and_activate_version(
    client: TestClient, db_session: Session
):
    """更新接口应支持切换分类、追加版本并激活历史版本"""
    # 准备两个分类和两个标签，便于验证分类切换与标签顺序
    origin_class = PromptClass(name="初始分类")
    target_class = PromptClass(name="目标分类")
    tag_a = PromptTag(name="高优先级", color="#EF4444")
    tag_b = PromptTag(name="低优先级", color="#22C55E")
    db_session.add_all([origin_class, target_class, tag_a, tag_b])
    db_session.commit()

    # 创建初始 Prompt，记录首个版本用于后续激活
    headers = _auth_headers(db_session)
    create_resp = client.post(
        "/api/v1/prompts/",
        headers=headers,
        json={
            "name": "复杂更新",
            "version": "v1",
            "content": "版本一内容",
            "class_id": origin_class.id,
            "tag_ids": [tag_a.id],
        },
    )
    assert create_resp.status_code == 201
    prompt = create_resp.json()
    prompt_id = prompt["id"]
    original_version_id = prompt["current_version"]["id"]

    # 追加新版本并切换分类，同时检查标签去重后顺序
    update_resp = client.put(
        f"/api/v1/prompts/{prompt_id}",
        headers=headers,
        json={
            "version": "v2",
            "content": "版本二内容",
            "class_id": target_class.id,
            "name": "复杂更新·第二版",
            "description": "第二版描述",
            "author": "architect",
            "tag_ids": [tag_b.id, tag_b.id, tag_a.id],
        },
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["name"] == "复杂更新·第二版"
    assert updated["description"] == "第二版描述"
    assert updated["author"] == "architect"
    assert updated["prompt_class"]["id"] == target_class.id
    assert updated["current_version"]["version"] == "v2"
    assert [tag["id"] for tag in updated["tags"]] == [tag_b.id, tag_a.id]

    # 激活旧版本，验证 activate_version_id 正常工作
    activate_resp = client.put(
        f"/api/v1/prompts/{prompt_id}",
        headers=headers,
        json={"activate_version_id": original_version_id},
    )
    assert activate_resp.status_code == 200
    activated = activate_resp.json()
    assert activated["current_version"]["id"] == original_version_id

    # 提供不存在的版本 ID，触发目标版本校验失败的分支
    invalid_target_resp = client.put(
        f"/api/v1/prompts/{prompt_id}",
        headers=headers,
        json={"activate_version_id": 999999},
    )
    assert invalid_target_resp.status_code == 400


def test_update_prompt_activate_version_conflict(
    client: TestClient, db_session: Session
) -> None:
    """同时传入 activate_version_id 与新版本信息应被拒绝"""
    # 先创建一个 Prompt，并通过更新新增一个版本
    headers = _auth_headers(db_session)

    create_resp = client.post(
        "/api/v1/prompts/",
        headers=headers,
        json={
            "name": "版本冲突检查",
            "version": "v1",
            "content": "版本一",
            "class_name": "冲突分类",
        },
    )
    prompt_id = create_resp.json()["id"]
    client.put(
        f"/api/v1/prompts/{prompt_id}",
        headers=headers,
        json={"version": "v2", "content": "版本二"},
    )

    # 同时提交 activate_version_id 与 version/content，触发冲突校验
    conflict_resp = client.put(
        f"/api/v1/prompts/{prompt_id}",
        headers=headers,
        json={
            "activate_version_id": create_resp.json()["current_version"]["id"],
            "version": "v3",
            "content": "版本三",
        },
    )
    assert conflict_resp.status_code == 400


def test_update_prompt_duplicate_version_returns_400(
    client: TestClient, db_session: Session
) -> None:
    """更新同名版本时应返回 400 状态码"""
    # 步骤一：创建基础 Prompt，为后续版本冲突测试铺垫
    headers = _auth_headers(db_session)

    create_resp = client.post(
        "/api/v1/prompts/",
        headers=headers,
        json={
            "name": "更新冲突",
            "version": "v1",
            "content": "初始版本",
            "class_name": "更新测试",
        },
    )
    assert create_resp.status_code == 201
    prompt_id = create_resp.json()["id"]

    # 步骤二：通过更新接口新增一个新的版本作为基准
    second_resp = client.put(
        f"/api/v1/prompts/{prompt_id}",
        headers=headers,
        json={"version": "v2", "content": "第二版"},
    )
    assert second_resp.status_code == 200

    # 步骤三：再次提交相同版本号，验证会被服务端拒绝
    conflict_resp = client.put(
        f"/api/v1/prompts/{prompt_id}",
        headers=headers,
        json={"version": "v2", "content": "重复版本"},
    )
    assert conflict_resp.status_code == 400


def test_update_prompt_activate_version_non_member(
    client: TestClient, db_session: Session
) -> None:
    """激活其他 Prompt 的版本时应返回 400"""
    # 分别创建两个 Prompt，获取第二个 Prompt 的版本 ID
    headers = _auth_headers(db_session)

    first_resp = client.post(
        "/api/v1/prompts/",
        headers=headers,
        json={
            "name": "主实体",
            "version": "v1",
            "content": "主实体内容",
            "class_name": "主分类",
        },
    )
    second_resp = client.post(
        "/api/v1/prompts/",
        headers=headers,
        json={
            "name": "干扰实体",
            "version": "v1",
            "content": "干扰实体内容",
            "class_name": "干扰分类",
        },
    )
    foreign_version_id = second_resp.json()["current_version"]["id"]

    # 尝试在第一个 Prompt 上激活另一个 Prompt 的版本，应被拒绝
    invalid_resp = client.put(
        f"/api/v1/prompts/{first_resp.json()['id']}",
        headers=headers,
        json={"activate_version_id": foreign_version_id},
    )
    assert invalid_resp.status_code == 400


def test_delete_prompt_not_found(client: TestClient, db_session: Session) -> None:
    """删除不存在的 Prompt 时返回 404"""
    # 直接请求删除一个不存在的 ID，验证兜底分支
    headers = _auth_headers(db_session)

    response = client.delete("/api/v1/prompts/999999", headers=headers)
    assert response.status_code == 404
