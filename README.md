# FastAPI Demo

用户认证与 CRUD 示例项目，基于 FastAPI + SQLAlchemy + PostgreSQL。

## 功能

- JWT 认证（access token + refresh token）
- 用户名/邮箱登录
- 用户 CRUD
- Item CRUD（所有权校验）
- 统一响应格式 `{code, msg, data}`
- 全局异常处理 + 参数校验
- 请求日志（IP、路径、参数、耗时、错误堆栈）
- 日志文件轮转
- Swagger 文档（Authorize 按钮可直接测试认证接口）
- Gunicorn + Uvicorn 多进程
- Docker 容器化部署

## 项目结构

```
app/
  core/
    config.py        # pydantic-settings 配置
    database.py      # SQLAlchemy 异步引擎
    security.py      # JWT + 密码工具
    logging.py       # 日志配置（控制台 + 文件轮转）
    exceptions.py    # 全局异常处理器
    middleware.py     # 访问日志中间件
  models/
    user.py          # User 模型
    item.py          # Item 模型
  routers/
    auth.py          # 注册 / 登录 / 刷新令牌
    users.py         # 用户 CRUD
    items.py         # Item CRUD
  schemas/
    schemas.py       # Pydantic 请求/响应模型
main.py              # 应用入口
gunicorn.conf.py     # Gunicorn 配置
docker-compose.yml   # Docker Compose
Dockerfile           # 容器构建
```

## 快速开始

### 环境要求

- Python 3.12+
- PostgreSQL 16+

### 本地开发

```bash
# 安装依赖
pip install -e ".[dev]"

# 配置环境变量
cp .env.example .env
# 编辑 .env 设置数据库连接等

# 启动
python main.py
# 或热重载模式
uvicorn main:app --reload
```

### Docker 部署

```bash
# 启动所有服务（PostgreSQL + Web）
docker compose up -d --build

# 查看日志
docker compose logs -f web

# 停止
docker compose down

# 停止并清除数据卷
docker compose down -v
```

### 生产环境（非 Docker）

```bash
pip install -e .
gunicorn -c gunicorn.conf.py main:app
```

## API 文档

启动后访问：

| 地址 | 说明 |
|------|------|
| `/docs` | Swagger UI（可交互测试） |
| `/redoc` | ReDoc（只读文档） |

Swagger 使用：点击 Authorize → 输入用户名/密码 → 自动获取 token → 测试认证接口。

## 统一响应格式

**成功：**
```json
{"code": 200, "msg": "ok", "data": {...}}
```

**错误：**
```json
{"code": 404, "msg": "用户不存在", "data": null}
```

**登录（OAuth2 兼容，直接返回 token）：**
```json
{"access_token": "...", "refresh_token": "...", "token_type": "bearer"}
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `APP_NAME` | FastAPI Demo | 应用名称 |
| `DEBUG` | false | 调试模式 |
| `LOG_LEVEL` | INFO | 日志级别 |
| `LOG_DIR` | logs | 日志目录 |
| `DATABASE_URL` | postgresql+asyncpg://... | 数据库连接 |
| `SECRET_KEY` | change-me-... | JWT 签名密钥 |
| `ALGORITHM` | HS256 | JWT 算法 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Access token 过期时间 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token 过期时间 |
| `WORKERS` | 4 | Gunicorn worker 数 |
| `BIND` | 0.0.0.0:8000 | 监听地址 |

## 数据库迁移

```bash
# 生成迁移
alembic revision --autogenerate -m "description"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```
