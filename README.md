# SNI RAG

SNI Recognition System with LangGraph RAG.

## Docker 部署（推荐）

### 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/lafdrew/sni_search.git
cd sni_search

# 2. 配置环境变量
使用7z 解压.env.7z文件 确保.env文件在项目根目录中(.env中有配置好的llm api和websearch api)

# 3. 启动服务
docker compose up -d
```



| 服务 | 地址 | 说明 |
|------|------|------|
| 前端界面 | http://localhost:3000 | Web UI |
| 后端 API | http://localhost:9000 | REST API |
| Qdrant 控制台 | http://localhost:6333/dashboard | 数据库管理 |




访问 http://localhost:3000 使用前端界面。



或者
```bash
# 基本查询
curl -X POST http://localhost:9000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "example.com"}'



## 手动配置（开发模式）

如果你需要本地开发或自定义配置，可以按照以下步骤手动安装和启动各个服务。



### 1. 安装 Docker

参考官网教程

### 2. 安装 uv（Python 包管理器）

**Linux / macOS:**
```bash
# 使用官方安装脚本
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv
```

**Windows (PowerShell):**
```powershell
# 使用官方安装脚本
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或使用 pip
pip install uv
```

**验证安装:**
```bash
uv --version
```

### 3. 安装 Python 依赖

```bash
# 在项目根目录执行
cd sni_search

# 安装所有依赖
uv sync



### 4. 配置环境变量

解压.env.7z 确保.env在项目根目录中

### 5. 下载嵌入模型（离线使用）




```bash
# 下载模型到本地 data/models/embeddings 目录
 uv run python scripts/download_embedding_model.py --model                               sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# 下载完成后，修改 .env 文件中的 EMBEDDING_MODEL
# EMBEDDING_MODEL=./data/models/embeddings
```

**验证模型：**

```bash
# 检查模型文件是否下载成功
ls -la data/models/embeddings/

# 应该包含以下文件：
# config.json, model.safetensors, tokenizer.json, 等
```

### 6. 启动 Qdrant 向量数据库

**方式一：使用项目预置数据启动（推荐）**

```bash
# 使用 data/qdrant 目录中的预置数据启动 Qdrant
# 预置数据包括少量样本数据
docker pull qdrant/qdrant

docker run -d \
  --name sni-qdrant \
  -p 6333:6333 \
  -v $(pwd)/data/qdrant:/qdrant/storage:z \
  qdrant/qdrant

# 查看日志确认启动成功
docker logs -f sni-qdrant


```

**验证 Qdrant 运行状态:**

```bash
# 访问 Qdrant 控制台
http://localhost:6333/dashboard

# 或使用 curl 检查健康状态
curl http://localhost:6333/
```


### 7. 简单测试（不需要起后端服务）

运行多轮搜索演示（修改test_multi_round_search.py的test_query改变要查询的sni）
```bash
uv run python demo/test_multi_round_search.py
```


### 8. 启动后端服务

```bash
#使用 uv 运行
uv run python -m src.api_server

```

**验证后端运行状态:**

```bash
# 健康检查
curl http://localhost:9000/health

# 应返回: {"status": "ok"}

# 测试接口
curl -X POST http://localhost:9000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "example.com"}'
```

### 9. 启动前端服务（可选,方便查看流程）



```bash
# 进入前端目录
cd frontend

# 安装依赖（首次运行）
npm install


# 启动开发服务器
npm run dev

# 前端默认运行在 http://localhost:3000
```




### 服务启动顺序推荐

1. 启动 Qdrant（必须）
2. 启动后端（依赖 Qdrant）
3. 启动前端（依赖后端）




