# Tenacity 重试库使用指南

## 安装

Tenacity 已经添加到项目依赖中，安装时会自动安装：

```bash
uv sync
```

## 基本使用

### 1. 导入预定义的重试装饰器

```python
from app.utils.retry import db_retry, api_retry, file_retry, cache_retry
```

### 2. 在异步函数中使用

```python
@api_retry
async def fetch_external_data(endpoint: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com{endpoint}")
        return response.json()
```

### 3. 在数据库操作中使用

```python
@db_retry
async def get_user_data(user_id: int, db):
    user = await db.get(User, user_id)
    return user
```

## 预定义装饰器说明

### `db_retry`
- **用途**: 数据库操作重试
- **重试次数**: 3 次
- **等待策略**: 指数退避 (1-5 秒)
- **重试异常**: ConnectionError, TimeoutError
- **适用场景**: 数据库连接不稳定、查询超时

### `api_retry`
- **用途**: 外部 API 调用重试（仅重试连接和超时错误）
- **重试次数**: 4 次
- **等待策略**: 指数退避 (2-30 秒)
- **重试异常**: ConnectionError, TimeoutError
- **注意**: 不会重试 HTTP 错误（如 404, 500 等）
- **适用场景**: 调用第三方 API、微服务通信

### `api_retry_with_http_errors`
- **用途**: 外部 API 调用重试（包含 HTTP 错误重试）
- **重试次数**: 4 次
- **等待策略**: 指数退避 (2-30 秒)
- **重试异常**: ConnectionError, TimeoutError, HTTPStatusError
- **注意**: 会重试所有 HTTP 错误（4xx 和 5xx）
- **适用场景**: 需要重试 HTTP 错误的场景（如服务器临时不可用）

### `file_retry`
- **用途**: 文件操作重试
- **重试次数**: 3 次
- **等待策略**: 指数退避 (1-3 秒)
- **重试异常**: IOError, OSError
- **适用场景**: 读写文件、文件上传下载

### `cache_retry`
- **用途**: 缓存操作重试
- **重试次数**: 2 次
- **等待策略**: 指数退避 (0.5-2 秒)
- **重试异常**: ConnectionError
- **适用场景**: Redis、Memcached 等缓存操作

## 自定义重试装饰器

如果需要自定义重试策略，可以创建自己的装饰器：

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# 创建自定义重试装饰器
custom_retry = retry(
    stop=stop_after_attempt(5),  # 最多重试 5 次
    wait=wait_exponential(multiplier=2, min=1, max=60),  # 指数退避，1-60 秒
    retry=retry_if_exception_type((ConnectionError, TimeoutError)),  # 只重试特定异常
    reraise=True  # 重试失败后重新抛出异常
)

@custom_retry
async def my_function():
    # 你的代码
    pass
```

## 在 FastAPI 路由中使用

```python
from fastapi import APIRouter, Depends, HTTPException
from app.utils.retry import api_retry
from app.core.deps import CurrentUser

router = APIRouter()

@router.get("/external-data")
async def get_external_data(current_user: CurrentUser):
    try:
        data = await fetch_external_data("/api/data")
        return {"data": data}
    except Exception as e:
        raise HTTPException(status_code=503, detail="外部服务不可用")
```

## 关于 `response.raise_for_status()`

`response.raise_for_status()` 会在 HTTP 状态码为 4xx 或 5xx 时抛出 `HTTPStatusError` 异常。

- **使用 `api_retry`**: 不会重试 HTTP 错误
- **使用 `api_retry_with_http_errors`**: 会重试 HTTP 错误

示例：

```python
# 不会重试 HTTP 错误
@api_retry
async def fetch_data():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        response.raise_for_status()  # 如果返回 500 错误，不会重试
        return response.json()

# 会重试 HTTP 错误
@api_retry_with_http_errors
async def fetch_data_with_retry():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        response.raise_for_status()  # 如果返回 500 错误，会重试
        return response.json()
```

## 注意事项

1. **幂等性**: 确保重试的操作是幂等的，避免重复执行产生副作用
2. **超时设置**: 为外部调用设置合理的超时时间
3. **日志记录**: 重试过程会自动记录日志，便于排查问题
4. **异常处理**: 重试失败后会重新抛出异常，需要在调用处处理
5. **性能考虑**: 重试会增加响应时间，根据业务需求调整重试参数

## 完整示例

查看 `app/utils/retry.py` 和 `app/routers/external_api.py` 获取更多使用示例。
