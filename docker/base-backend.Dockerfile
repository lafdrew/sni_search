FROM python:3.11-slim AS base

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv 包管理器
RUN pip install --no-cache-dir uv

WORKDIR /app

# 仅复制依赖清单文件（这些文件很少变化）
COPY pyproject.toml uv.lock ./

# 安装 Python 依赖
RUN uv sync --no-dev --frozen

# 设置环境变量
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH" \
    PYTHONUNBUFFERED=1

# 可选：预下载嵌入模型（加快首次启动）
# 注释掉以减小镜像大小，让容器启动时自动下载
# RUN python -c "from sentence_transformers import SentenceTransformer; \
#     SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"
