# FastAPI Demo

用户认证与 CRUD 示例项目，基于 FastAPI + SQLModel + PostgreSQL。

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
- GitHub Actions CI/CD

## 项目结构

```
app/
  main.py            # 应用入口
  core/
    config.py        # pydantic-settings 配置
    database.py      # SQLModel 异步引擎
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
  alembic/           # 数据库迁移
gunicorn.conf.py     # Gunicorn 配置
docker-compose.yml   # Docker Compose
Dockerfile           # 容器构建
tests/               # 测试用例
```

## 快速开始

### 环境要求

- Python 3.12+
- PostgreSQL 16+（本地开发可用 SQLite）

### 1. 安装依赖

```bash
pip install -e ".[dev]"
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，按需修改（本地开发默认用 SQLite，无需额外配置 PostgreSQL）：

```ini
DATABASE_URL=sqlite+aiosqlite:///./app.db    # SQLite（默认）
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname  # PostgreSQL
SECRET_KEY=your-random-secret-key              # 生产环境务必修改
```

### 3. 启动服务

**开发模式（热重载）：**

```bash
uvicorn app.main:app --reload
```

**开发模式（单进程）：**

```bash
python -m app.main
```

**生产模式（Gunicorn 多进程）：**

```bash
fastapi run --workers ${WORKERS:-4} main.py
```

**Docker 部署（Traefik + PostgreSQL + Web）：**

```bash
# 构建并启动
docker compose up -d --build

# 查看日志
docker compose logs -f backend

# 停止
docker compose down

# 停止并清除数据卷
docker compose down -v
```

服务端口：
- **http://localhost:80** — 应用（通过 Traefik 反向代理）
- **http://localhost:8080** — Traefik Dashboard

### 4. 验证启动

```bash
curl http://localhost/health
# {"code":200,"msg":"ok","data":{"status":"ok"}}
```

### 5. 访问 API 文档

| 地址 | 说明 |
|------|------|
| http://localhost:80/docs | Swagger UI（可交互测试） |
| http://localhost:80/redoc | ReDoc（只读文档） |

Swagger 使用：点击 Authorize → 输入用户名/密码 → 自动获取 token → 测试认证接口。

### 6. 运行测试

```bash
pytest tests/ -v

# 带覆盖率报告
pytest tests/ -v --cov
```

### 7. 代码检查

```bash
# Ruff — 代码规范 + 格式化
ruff check .
ruff format --check .

# Mypy — 类型检查
mypy app/
```

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
