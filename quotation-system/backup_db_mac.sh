#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

DB_FILE="quotation_system.db"
BACKUP_DIR="$HOME/Documents/quotation_system_backups"

if [ ! -f "$DB_FILE" ]; then
  echo "未找到数据库文件：$(pwd)/${DB_FILE}"
  echo "请确认报价系统已初始化，或当前目录是否正确。"
  exit 1
fi

mkdir -p "$BACKUP_DIR"

TIMESTAMP="$(date '+%Y%m%d_%H%M%S')"
BACKUP_FILE="$BACKUP_DIR/quotation_system_${TIMESTAMP}.db"

cp "$DB_FILE" "$BACKUP_FILE"

echo "数据库备份完成："
echo "$BACKUP_FILE"
