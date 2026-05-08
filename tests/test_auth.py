"""接口测试 - auth 路由"""

from httpx import AsyncClient


class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        resp = await client.post(
            "/api/auth/register",
            json={
                "username": "alice",
                "email": "alice@example.com",
                "password": "secret123",
                "confirm_password": "secret123",
            },
        )
        assert resp.status_code == 400
        assert resp.status_code == 201
        body = resp.json()
        assert body["code"] == 201
        assert body["data"]["username"] == "alice"
        assert body["data"]["email"] == "alice@example.com"
        assert "password" not in body["data"]

    async def test_register_duplicate_username(self, client: AsyncClient):
        await client.post(
            "/api/auth/register",
            json={
                "username": "bob",
                "email": "bob@example.com",
                "password": "secret",
                "confirm_password": "secret",
            },
        )
        resp = await client.post(
            "/api/auth/register",
            json={
                "username": "bob",
                "email": "bob2@example.com",
                "password": "secret",
                "confirm_password": "secret",
            },
        )
        assert resp.status_code == 400
        assert resp.json()["msg"] == "用户名已存在"

    async def test_register_duplicate_email(self, client: AsyncClient):
        await client.post(
            "/api/auth/register",
            json={
                "username": "charlie",
                "email": "charlie@example.com",
                "password": "secret",
                "confirm_password": "secret",
            },
        )
        resp = await client.post(
            "/api/auth/register",
            json={
                "username": "charlie2",
                "email": "charlie@example.com",
                "password": "secret",
                "confirm_password": "secret",
            },
        )
        assert resp.status_code == 400
        assert resp.json()["msg"] == "邮箱已注册"

    async def test_register_missing_fields(self, client: AsyncClient):
        resp = await client.post("/api/auth/register", json={"username": "dave"})
        assert resp.status_code == 422


class TestLogin:
    async def test_login_with_username(self, client: AsyncClient):
        await client.post(
            "/api/auth/register",
            json={
                "username": "alice",
                "email": "alice@example.com",
                "password": "secret123",
                "confirm_password": "secret123",
            },
        )
        resp = await client.post(
            "/api/auth/login",
            data={
                "username": "alice",
                "password": "secret123",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"

    async def test_login_with_email(self, client: AsyncClient):
        await client.post(
            "/api/auth/register",
            json={
                "username": "bob",
                "email": "bob@example.com",
                "password": "secret123",
                "confirm_password": "secret123",
            },
        )
        resp = await client.post(
            "/api/auth/login",
            data={
                "username": "bob@example.com",
                "password": "secret123",
            },
        )
        assert resp.status_code == 200

    async def test_login_wrong_password(self, client: AsyncClient):
        await client.post(
            "/api/auth/register",
            json={
                "username": "carol",
                "email": "carol@example.com",
                "password": "secret123",
                "confirm_password": "secret123",
            },
        )
        resp = await client.post(
            "/api/auth/login",
            data={
                "username": "carol",
                "password": "wrong",
            },
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post(
            "/api/auth/login",
            data={
                "username": "nobody",
                "password": "secret",
            },
        )
        assert resp.status_code == 401


class TestRefresh:
    async def test_refresh_success(self, client: AsyncClient):
        await client.post(
            "/api/auth/register",
            json={
                "username": "alice",
                "email": "alice@example.com",
                "password": "secret123",
                "confirm_password": "secret123",
            },
        )
        login_resp = await client.post(
            "/api/auth/login",
            data={
                "username": "alice",
                "password": "secret123",
                "confirm_password": "secret123",
            },
        )
        refresh_token = login_resp.json()["refresh_token"]

        resp = await client.post(
            "/api/auth/refresh",
            json={
                "refresh_token": refresh_token,
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body

    async def test_refresh_with_access_token_fails(self, client: AsyncClient):
        await client.post(
            "/api/auth/register",
            json={
                "username": "bob",
                "email": "bob@example.com",
                "password": "secret123",
                "confirm_password": "secret123",
            },
        )
        login_resp = await client.post(
            "/api/auth/login",
            data={
                "username": "bob",
                "password": "secret123",
            },
        )
        access_token = login_resp.json()["access_token"]

        resp = await client.post(
            "/api/auth/refresh",
            json={
                "refresh_token": access_token,
            },
        )
        assert resp.status_code == 401

    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        resp = await client.post(
            "/api/auth/refresh",
            json={
                "refresh_token": "invalid.token.here",
            },
        )
        assert resp.status_code == 401
