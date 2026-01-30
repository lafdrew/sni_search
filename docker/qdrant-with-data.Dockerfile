FROM qdrant/qdrant:latest

# 复制预置的 Qdrant 数据（作为基础数据）
COPY data/qdrant/ /qdrant/preloaded_data/

# 复制初始化脚本
COPY docker/qdrant-init.sh /qdrant-init.sh

# 设置权限
RUN chmod +x /qdrant-init.sh && \
    chmod -R 755 /qdrant/preloaded_data

# 使用自定义 entrypoint
ENTRYPOINT ["/qdrant-init.sh"]
