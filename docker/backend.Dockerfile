# 从 Base 镜像继承（包含所有依赖）
ARG BASE_IMAGE=yourname/sni-backend-base:latest
FROM ${BASE_IMAGE}

WORKDIR /app

# 复制应用源代码（经常变化）
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY conf.yaml ./

# 创建必要的目录
RUN mkdir -p /app/results /app/models /app/data

# 暴露端口
EXPOSE 9000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:9000/health || exit 1

# 启动命令
CMD ["python", "-m", "src.api_server"]
