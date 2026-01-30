FROM python:3.12-slim AS base

# 换清华源加速
RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv 包管理器
RUN pip install --no-cache-dir uv -i https://pypi.tuna.tsinghua.edu.cn/simple

# 配置 uv 使用清华源（PyTorch CPU 索引在 pyproject.toml 中配置）
ENV UV_EXTRA_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app

# 仅复制依赖清单文件
COPY pyproject.toml README.md ./

# 安装依赖（pyproject.toml 已配置使用 PyTorch CPU 索引）
RUN uv sync --no-dev

# 设置环境变量
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app:$PYTHONPATH" \
    PYTHONUNBUFFERED=1

# 复制本地嵌入模型到镜像
COPY data/models/embeddings /app/models/embeddings

# 设置默认使用本地模型
ENV EMBEDDING_MODEL=/app/models/embeddings
