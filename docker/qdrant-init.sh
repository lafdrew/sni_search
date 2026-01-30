#!/bin/bash
# Qdrant 初始化脚本 - 首次启动时导入预置数据

set -e

STORAGE_DIR="/qdrant/storage"
PRELOADED_DIR="/qdrant/preloaded_data"
INIT_FLAG="${STORAGE_DIR}/.initialized_from_image"

echo "=== Qdrant 数据初始化 ==="

# 检查存储目录是否为空（首次启动）
if [ -z "$(ls -A $STORAGE_DIR 2>/dev/null)" ]; then
    echo "存储目录为空，初始化预置数据..."

    if [ -d "$PRELOADED_DIR" ] && [ "$(ls -A $PRELOADED_DIR 2>/dev/null)" ]; then
        echo "从预置数据目录复制到 volume..."
        cp -r "$PRELOADED_DIR"/* "$STORAGE_DIR/"
        chmod -R 755 "$STORAGE_DIR"
        touch "$INIT_FLAG"
        echo "✓ 预置数据导入完成"
    else
        echo "⚠ 无预置数据，使用空存储启动"
    fi
else
    echo "存储目录已有数据，跳过初始化"
    if [ -f "$INIT_FLAG" ]; then
        echo "✓ 数据来自镜像预置"
    fi
fi

echo "=== 启动 Qdrant ==="

# 启动 Qdrant
exec /qdrant/entrypoint.sh "$@"
