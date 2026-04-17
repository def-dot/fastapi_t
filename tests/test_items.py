"""接口测试 - items 路由"""

from httpx import AsyncClient


class TestItems:
    async def test_create_item(self, client: AsyncClient, auth_headers: dict):
        resp = await client.post(
            "/api/items/",
            headers=auth_headers,
            json={
                "title": "My Item",
                "description": "Some details",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["data"]["title"] == "My Item"
        assert body["data"]["description"] == "Some details"

    async def test_create_item_unauthorized(self, client: AsyncClient):
        resp = await client.post("/api/items/", json={"title": "No auth"})
        assert resp.status_code == 401

    async def test_list_items(self, client: AsyncClient, auth_headers: dict):
        await client.post("/api/items/", headers=auth_headers, json={"title": "Item 1"})
        resp = await client.get("/api/items/", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["total"] >= 1

    async def test_list_my_items(self, client: AsyncClient, auth_headers: dict):
        await client.post("/api/items/", headers=auth_headers, json={"title": "My Item"})
        resp = await client.get("/api/items/me", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["total"] >= 1

    async def test_get_item_by_id(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post("/api/items/", headers=auth_headers, json={"title": "Get Me"})
        item_id = create_resp.json()["data"]["id"]

        resp = await client.get(f"/api/items/{item_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "Get Me"

    async def test_get_item_not_found(self, client: AsyncClient, auth_headers: dict):
        resp = await client.get("/api/items/99999", headers=auth_headers)
        assert resp.status_code == 404

    async def test_update_item_owner(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post("/api/items/", headers=auth_headers, json={"title": "Old Title"})
        item_id = create_resp.json()["data"]["id"]

        resp = await client.put(f"/api/items/{item_id}", headers=auth_headers, json={"title": "New Title"})
        assert resp.status_code == 200
        assert resp.json()["data"]["title"] == "New Title"

    async def test_update_item_not_owner(self, client: AsyncClient):
        # 用户 A 创建 item
        await client.post(
            "/api/auth/register",
            json={
                "username": "owner",
                "email": "owner@example.com",
                "password": "secret123",
            },
        )
        login_a = await client.post("/api/auth/login", data={"username": "owner", "password": "secret123"})
        headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}

        create_resp = await client.post("/api/items/", headers=headers_a, json={"title": "Owned Item"})
        item_id = create_resp.json()["data"]["id"]

        # 用户 B 尝试修改
        await client.post(
            "/api/auth/register",
            json={
                "username": "thief",
                "email": "thief@example.com",
                "password": "secret123",
            },
        )
        login_b = await client.post("/api/auth/login", data={"username": "thief", "password": "secret123"})
        headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

        resp = await client.put(f"/api/items/{item_id}", headers=headers_b, json={"title": "Hacked"})
        assert resp.status_code == 403

    async def test_delete_item_owner(self, client: AsyncClient, auth_headers: dict):
        create_resp = await client.post("/api/items/", headers=auth_headers, json={"title": "Delete Me"})
        item_id = create_resp.json()["data"]["id"]

        resp = await client.delete(f"/api/items/{item_id}", headers=auth_headers)
        assert resp.status_code == 204

        # 确认已删除
        get_resp = await client.get(f"/api/items/{item_id}", headers=auth_headers)
        assert get_resp.status_code == 404

    async def test_delete_item_not_owner(self, client: AsyncClient):
        # 用户 A 创建 item
        await client.post(
            "/api/auth/register",
            json={
                "username": "owner2",
                "email": "owner2@example.com",
                "password": "secret123",
            },
        )
        login_a = await client.post("/api/auth/login", data={"username": "owner2", "password": "secret123"})
        headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}

        create_resp = await client.post("/api/items/", headers=headers_a, json={"title": "Protected"})
        item_id = create_resp.json()["data"]["id"]

        # 用户 B 尝试删除
        await client.post(
            "/api/auth/register",
            json={
                "username": "thief2",
                "email": "thief2@example.com",
                "password": "secret123",
            },
        )
        login_b = await client.post("/api/auth/login", data={"username": "thief2", "password": "secret123"})
        headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

        resp = await client.delete(f"/api/items/{item_id}", headers=headers_b)
        assert resp.status_code == 403
