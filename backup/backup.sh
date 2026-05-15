#!/bin/sh
FILE=/backups/db_$(date +%Y%m%d_%H%M%S).sql.gz

pg_dump -h db -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$FILE"

# 保留最近7天
find /backups -name "db_*.sql.gz" -mtime +7 -delete
