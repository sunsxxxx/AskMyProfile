#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "错误：未找到 docker 命令。" >&2
  exit 1
fi

docker compose config --quiet

if ! docker compose ps --status running --services | grep -qx "backend"; then
  echo "错误：backend 服务尚未运行，请先执行 ./build-start-backend.sh。" >&2
  exit 1
fi

docker compose exec -T backend python -m app.scripts.reindex

echo "知识库索引已重建。"
