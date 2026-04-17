"""接口测试 - users 路由"""

from httpx import AsyncClient


class TestUsers:
    async def test_get_current_user(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/users/me", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["username"] == "testuser"

    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        resp = await client.get("/api/users/me")
        assert resp.status_code == 401

    async def test_list_users(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/users/", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["total"] >= 1
        assert len(body["data"]["items"]) >= 1

    async def test_get_user_by_id(self, client: AsyncClient, auth_headers: dict):
        # 先获取当前用户
        me_resp = await client.get("/api/users/me", headers=auth_headers)
        user_id = me_resp.json()["data"]["id"]

        resp = await client.get(f"/api/users/{user_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["id"] == user_id

    async def test_get_user_not_found(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/users/99999", headers=auth_headers)
        assert resp.status_code == 404

    async def test_update_user_email(self, client: AsyncClient, auth_headers: dict):
        resp = await client.put(
            "/api/users/me",
            headers=auth_headers,
            json={
                "email": "newemail@example.com",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["email"] == "newemail@example.com"

    async def test_update_user_password(self, client: AsyncClient, auth_headers: dict):
        resp = await client.put(
            "/api/users/me",
            headers=auth_headers,
            json={
                "password": "newsecret456",
            },
        )
        assert resp.status_code == 200

        # 用新密码登录
        login_resp = await client.post(
            "/api/auth/login",
            data={
                "username": "testuser",
                "password": "newsecret456",
            },
        )
        assert login_resp.status_code == 200

    async def test_delete_user(self, client: AsyncClient):
        # 注册一个新用户
        await client.post(
            "/api/auth/register",
            json={
                "username": "deleteme",
                "email": "delete@example.com",
                "password": "secret123",
            },
        )
        login_resp = await client.post(
            "/api/auth/login",
            data={
                "username": "deleteme",
                "password": "secret123",
            },
        )
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.delete("/api/users/me", headers=headers)
        assert resp.status_code == 204

        # 验证用户已删除（登录应失败）
        login_resp2 = await client.post(
            "/api/auth/login",
            data={
                "username": "deleteme",
                "password": "secret123",
            },
        )
        assert login_resp2.status_code == 401
