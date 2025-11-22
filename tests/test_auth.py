from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_signup_and_login_flow(client: TestClient, db_session: Session) -> None:
    """用户可以注册账号并通过用户名密码登录获取访问令牌。"""

    signup_resp = client.post(
        "/api/v1/auth/signup",
        json={"username": "alice", "password": "password123"},
    )
    assert signup_resp.status_code == 201
    user_data = signup_resp.json()
    assert user_data["username"] == "alice"
    assert isinstance(user_data["id"], int)

    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "alice", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert token_data["token_type"] == "bearer"
    assert token_data["access_token"]

    me_resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["username"] == "alice"


def test_signup_duplicate_username_returns_400(
    client: TestClient, db_session: Session
) -> None:
    """重复注册相同用户名时应返回 400。"""

    client.post(
        "/api/v1/auth/signup",
        json={"username": "bob", "password": "password123"},
    )
    resp = client.post(
        "/api/v1/auth/signup",
        json={"username": "bob", "password": "anotherpass"},
    )
    assert resp.status_code == 400


def test_login_with_invalid_credentials_returns_400(
    client: TestClient, db_session: Session
) -> None:
    """使用错误密码登录时应返回 400。"""

    client.post(
        "/api/v1/auth/signup",
        json={"username": "charlie", "password": "password123"},
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "charlie", "password": "wrong-password"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 400
