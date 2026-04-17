"""单元测试 - security 模块"""

import pytest

from apps.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestPassword:
    def test_hash_and_verify(self):
        hashed = hash_password("secret123")
        assert verify_password("secret123", hashed)

    def test_wrong_password(self):
        hashed = hash_password("secret123")
        assert not verify_password("wrong", hashed)

    def test_different_hash_each_time(self):
        h1 = hash_password("same")
        h2 = hash_password("same")
        assert h1 != h2  # 不同盐值


class TestAccessToken:
    def test_create_and_decode(self):
        token = create_access_token(data={"sub": "alice"})
        payload = decode_access_token(token)
        assert payload["sub"] == "alice"
        assert payload["type"] == "access"

    def test_invalid_token_raises_401(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            decode_access_token("invalid.token.here")
        assert exc_info.value.status_code == 401


class TestRefreshToken:
    def test_create_and_decode(self):
        token = create_refresh_token(data={"sub": "alice"})
        payload = decode_access_token(token)
        assert payload["sub"] == "alice"
        assert payload["type"] == "refresh"

    def test_token_type_different_from_access(self):
        at = create_access_token(data={"sub": "alice"})
        rt = create_refresh_token(data={"sub": "alice"})
        at_payload = decode_access_token(at)
        rt_payload = decode_access_token(rt)
        assert at_payload["type"] == "access"
        assert rt_payload["type"] == "refresh"
