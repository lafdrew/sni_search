# SNI RAG

SNI Recognition System with LangGraph RAG.

## Docker 部署（推荐）

### 快速开始

```bash
# 1. 下载配置文件
curl -O https://raw.githubusercontent.com/yourname/sni-rag/master/docker-compose.yml
curl -O https://raw.githubusercontent.com/yourname/sni-rag/master/.env.example

# 2. 配置环境变量
cp .env.example .env
nano .env  # 填入你的 ANTHROPIC_API_KEY

# 3. 启动服务
docker-compose up -d
```

访问 http://localhost 使用前端界面。

### 配置加密（可选，推荐）

保护敏感配置文件：

```bash
# 下载加密工具
curl -O https://raw.githubusercontent.com/yourname/sni-rag/master/encrypt-env.sh
chmod +x encrypt-env.sh

# 加密 .env 文件
./encrypt-env.sh --encrypt .env
# 生成 .env.7z 文件（压缩 + AES-256 加密）

# 解密使用
./encrypt-env.sh --decrypt .env.7z
```

**特性**：
- 高压缩率（减少 50-70% 大小）
- AES-256 加密保护
- 文件名加密（隐藏内容列表）
- 跨平台支持

详细文档: [Docker 部署指南](docs/DOCKER_DEPLOYMENT.md)

### Docker Hub 镜像

- **后端**: `docker pull yourname/sni-backend:latest`
- **前端**: `docker pull yourname/sni-frontend:latest`

### 架构图

```
前端 (Nginx) ←→ 后端 (FastAPI) ←→ Qdrant (向量数据库)
    :80              :9000               :6333
```

### 安全说明

- `.env` 文件包含敏感信息，已在 `.gitignore` 中排除
- 使用 `encrypt-env.sh` 工具加密配置文件（7-Zip AES-256）
- `.env.7z` 加密文件可以安全提交到版本控制或云存储
- 压缩后体积减小 50-70%，便于网络传输

---

## Installation

```bash
uv sync
```

## Usage

### Import Data

```bash
uv run python -m src.import_data --data-dir ./results
```

### Run API Server

```bash
uv run python -m src.api_server
```
