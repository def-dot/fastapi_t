#!/bin/bash
set -euo pipefail

ENV_FILE=".env.production"
COMPOSE_FILES="-f compose.yml -f compose.prod.yml"
DC="docker compose --env-file $ENV_FILE $COMPOSE_FILES"

echo "===== 生产环境部署 ====="

# ---------- 1. 拉取最新镜像 ----------
echo ""
echo "[1/6] 拉取最新镜像..."
$DC pull backend db_migrate

# ---------- 2. 备份数据库 ----------
echo ""
echo "[2/6] 备份数据库..."
$DC exec db_backup /usr/local/bin/backup.sh
echo "备份完成。"

# ---------- 3. 启动服务（不含迁移） ----------
echo ""
echo "[3/6] 启动服务..."
$DC up -d

# ---------- 4. 执行数据库迁移 ----------
echo ""
echo "[4/6] 执行数据库迁移..."
if ! $DC run --rm db_migrate; then
    echo ""
    echo "!!! 迁移失败 !!!"
    echo "恢复步骤："
    echo "  1. 查看最新备份： ls -lt backups/"
    echo "  2. 恢复数据库：   gunzip -c backups/db_XXX.sql.gz | $DC exec -T db psql -U postgres fastapi_template"
    echo "  3. 回滚镜像：     修改 .env.production 中 DOCKER_TAG 为上一个版本"
    echo "  4. 重新部署：     bash deploy.sh"
    exit 1
fi

# ---------- 5. 健康检查 ----------
echo ""
echo "[5/6] 健康检查..."
HEALTH_URL="http://localhost:8000/health"
MAX_RETRIES=30
for i in $(seq 1 $MAX_RETRIES); do
    if curl -sf "$HEALTH_URL" > /dev/null 2>&1; then
        echo "健康检查通过。"
        break
    fi
    if [ "$i" -eq "$MAX_RETRIES" ]; then
        echo "健康检查失败（已重试 $MAX_RETRIES 次）。"
        echo "查看日志： $DC logs backend"
        exit 1
    fi
    sleep 2
done

# ---------- 6. 清理旧镜像 ----------
echo ""
echo "[6/6] 清理旧镜像..."
docker image prune -f

echo ""
echo "===== 部署完成 ====="
