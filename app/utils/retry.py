"""
Tenacity 重试工具
提供常用的重试装饰器和函数
"""

import logging
from typing import Any

from httpx import HTTPStatusError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)


# 数据库操作重试装饰器
db_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=5),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.INFO),
    reraise=True,
)


# 外部 API 调用重试装饰器（仅重试连接和超时错误）
api_retry = retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),
    before_sleep=before_sleep_log(logger, logging.INFO),
    reraise=True,
)

# 外部 API 调用重试装饰器（包含 HTTP 错误重试）
# 注意：这会重试所有 HTTP 错误，包括 4xx 和 5xx
api_retry_with_http_errors = retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, min=2, max=30),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, HTTPStatusError)),
    before_sleep=before_sleep_log(logger, logging.INFO),
    reraise=True,
)


# 文件操作重试装饰器
file_retry = retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=3),
    retry=retry_if_exception_type((IOError, OSError)),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)


# 缓存操作重试装饰器
cache_retry = retry(
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=0.5, min=0.5, max=2),
    retry=retry_if_exception_type(ConnectionError),
    before_sleep=before_sleep_log(logger, logging.DEBUG),
)


# 使用示例
if __name__ == "__main__":
    import asyncio
    import random

    @db_retry
    async def example_db_query(query: str) -> dict[str, Any]:
        """数据库查询示例"""
        if random.random() < 0.3:
            raise ConnectionError("数据库连接失败")
        return {"query": query, "result": "success"}

    @api_retry
    async def example_api_call(endpoint: str) -> dict[str, Any]:
        """API 调用示例"""
        if random.random() < 0.4:
            raise ConnectionError(f"API {endpoint} 连接失败")
        return {"endpoint": endpoint, "status": "success"}

    @file_retry
    def example_file_operation(filepath: str) -> dict[str, Any]:
        """文件操作示例"""
        if random.random() < 0.5:
            raise OSError(f"无法打开文件 {filepath}")
        return {"file": filepath, "status": "opened"}

    @cache_retry
    async def example_cache_operation(key: str) -> dict[str, Any]:
        """缓存操作示例"""
        if random.random() < 0.3:
            raise ConnectionError("Redis 连接失败")
        return {"key": key, "value": "cached_value"}

    # 测试示例
    async def test_examples() -> None:
        """测试各种重试场景"""
        print("=== Tenacity 重试工具测试 ===\n")

        # 测试数据库查询
        print("1. 数据库查询重试测试:")
        try:
            result = await example_db_query("SELECT * FROM users")
            print(f"   结果: {result}\n")
        except Exception as e:
            print(f"   失败: {e}\n")

        # 测试 API 调用
        print("2. API 调用重试测试:")
        try:
            result = await example_api_call("/api/users")
            print(f"   结果: {result}\n")
        except Exception as e:
            print(f"   失败: {e}\n")

        # 测试文件操作
        print("3. 文件操作重试测试:")
        try:
            result = example_file_operation("/tmp/test.txt")
            print(f"   结果: {result}\n")
        except Exception as e:
            print(f"   失败: {e}\n")

        # 测试缓存操作
        print("4. 缓存操作重试测试:")
        try:
            result = await example_cache_operation("user:123")
            print(f"   结果: {result}\n")
        except Exception as e:
            print(f"   失败: {e}\n")

    asyncio.run(test_examples())
