# Docker 部署指南

## 快速开始（3 步部署）

### 步骤 1: 下载配置文件

```bash
# 下载 docker-compose.yml 和环境变量模板
curl -O https://raw.githubusercontent.com/yourname/sni-rag/master/docker-compose.yml
curl -O https://raw.githubusercontent.com/yourname/sni-rag/master/.env.example
```

### 步骤 2: 配置环境变量

**选项 A: 创建新配置**
```bash
# 复制模板
cp .env.example .env

# 编辑配置文件，填入你的 API Key
nano .env
# 或使用你喜欢的编辑器: vim, code, etc.
```

**选项 B: 使用加密的配置文件**

如果你已经有加密的 `.env.7z` 文件：

```bash
# 下载加密工具
curl -O https://raw.githubusercontent.com/yourname/sni-rag/master/encrypt-env.sh
chmod +x encrypt-env.sh

# 解密配置文件
./encrypt-env.sh --decrypt .env.7z
# 输入解密密码
```

### 步骤 3: 启动服务

```bash
docker-compose up -d
```

服务将在以下地址可用：
- **前端界面**: http://localhost
- **API 服务**: http://localhost:9000
- **Qdrant 控制台**: http://localhost:6333/dashboard

---

## 加密配置文件（可选，推荐）

### 为什么要加密？

- ✅ 安全备份配置文件到云存储
- ✅ 团队成员间安全分享配置
- ✅ 可以将 `.env.7z` 提交到私有或公开仓库

### 加密步骤

```bash
# 1. 下载加密工具
curl -O https://raw.githubusercontent.com/yourname/sni-rag/master/encrypt-env.sh
chmod +x encrypt-env.sh

# 2. 加密 .env 文件
./encrypt-env.sh --encrypt .env
# 输入加密密码（至少 8 位，推荐使用强密码）

# 3. 生成 .env.7z 文件
# 现在可以安全地上传 .env.7z
```

### 解密步骤

```bash
# 从云存储或版本控制下载 .env.7z

# 解密
./encrypt-env.sh --decrypt .env.7z
# 输入解密密码

# 现在可以使用 .env 文件启动服务
docker-compose up -d
```

### 加密技术细节

- **格式**: 7-Zip（.7z）
- **算法**: AES-256 加密
- **特性**:
  - 高压缩率（通常压缩 50-70%）
  - 文件名加密（隐藏文件列表）
  - 跨平台支持（Windows/Linux/macOS）
- **工具**: 7-Zip / p7zip（开源免费）

**安装 7-Zip**：
```bash
# Ubuntu/Debian
sudo apt-get install p7zip-full

# macOS
brew install p7zip

# Windows
# 下载安装: https://www.7-zip.org/
```

---

## 配置说明

### 必填配置

| 配置项 | 说明 | 获取方式 |
|--------|------|---------|
| `ANTHROPIC_API_KEY` | Claude API 密钥 | https://console.anthropic.com/settings/keys |
| `LLM_PROVIDER` | LLM 提供者 | `claude` (默认) 或 `openai` |
| `CLAUDE_MODEL` | Claude 模型 | 默认: `claude-sonnet-4-5-20250929` |

### 可选配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `SEARCH_API` | `duckduckgo` | 搜索引擎（无需 API Key） |
| `CRAWLER_ENGINE` | `jina` | 网页爬虫 |
| `TGT_LIBRARY_ENABLED` | `true` | TGT 标准库 |
| `TAVILY_API_KEY` | (可选) | Tavily 搜索引擎 API Key |
| `JINA_API_KEY` | (可选) | Jina 爬虫 API Key |

完整配置参考 `.env.example` 文件中的注释。

---

## 检查服务状态

```bash
# 查看容器状态
docker-compose ps

# 查看实时日志
docker-compose logs -f

# 查看后端日志
docker-compose logs -f backend

# 健康检查
curl http://localhost:9000/health
```

---

## 数据初始化（可选）

### 初始化 TGT 标准库

```bash
docker-compose exec backend python scripts/init_tgt_library.py
```

### 导入 SNI 数据

```bash
# 1. 将数据文件放到 results/ 目录
mkdir -p results
cp your-data.json results/

# 2. 导入数据
docker-compose exec backend python -m src.import_data --data-dir /app/results
```

---

## 更新到最新版本

```bash
# 1. 拉取最新镜像
docker-compose pull

# 2. 重启服务（.env 配置会保留）
docker-compose up -d --force-recreate

# 3. 查看版本
docker-compose exec backend python -c "import src; print(src.__version__)"
```

---

## 常见问题

### Q1: 后端启动失败，提示 "请设置 ANTHROPIC_API_KEY"

**原因**: .env 文件不存在或配置不正确。

**解决**:
```bash
# 检查 .env 文件是否存在
ls -la .env

# 如果不存在，从模板创建
cp .env.example .env
nano .env

# 或解密已有的加密文件
./encrypt-env.sh --decrypt .env.7z
```

### Q2: 如何切换到 OpenAI？

编辑 `.env` 文件：
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-key-here
OPENAI_MODEL=gpt-4-turbo-preview
```

然后重启服务：
```bash
docker-compose restart backend
```

### Q3: 忘记了加密密码怎么办？

**抱歉，加密密码无法找回。** 你需要：
1. 重新创建 `.env` 文件
2. 使用新密码重新加密

建议使用密码管理器保存加密密码。

### Q4: .env 文件会被提交到 Git 吗？

**不会。** `.env` 文件已在 `.gitignore` 中排除。只有加密的 `.env.7z` 可以安全提交。

### Q5: 如何在多台机器间同步配置？

```bash
# 机器 A（加密）
./encrypt-env.sh --encrypt .env
# 上传 .env.7z 到云存储或版本控制

# 机器 B（解密）
# 下载 .env.7z
./encrypt-env.sh --decrypt .env.7z
docker-compose up -d
```

---

## 高级配置

### 1. 使用多个环境配置

```bash
# 开发环境
cp .env.example .env.dev
# 编辑 .env.dev

# 生产环境
cp .env.example .env.prod
# 编辑 .env.prod

# 启动指定环境
cp .env.dev .env && docker-compose up -d
```

### 2. 调整内存限制

编辑 `docker-compose.yml`：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

### 3. 增加并行搜索

编辑 `conf.yaml`:

```yaml
SEARCH_ENGINE:
  max_concurrent_requests: 8  # 默认 4
```

---

## 停止和卸载

```bash
# 停止服务（保留数据和配置）
docker-compose down

# 停止并删除数据卷（会清空 Qdrant 数据）
docker-compose down -v

# 删除镜像
docker rmi yourname/sni-backend:latest
docker rmi yourname/sni-frontend:latest
docker rmi qdrant/qdrant:latest

# 清理配置文件（可选）
rm -f .env .env.7z
```

---

## 安全最佳实践

### ✅ 推荐做法
- 使用加密工具保护 `.env` 文件
- `.env.7z` 可以安全提交到版本控制
- 定期更换 API Key
- 使用密码管理器保存加密密码
- 利用压缩特性减少网络传输

### ❌ 不推荐做法
- 将明文 `.env` 文件提交到 Git
- 在公开渠道分享 `.env` 文件
- 使用弱密码加密（少于 8 位）
- 丢失加密密码（无法恢复）

### 清理敏感信息

```bash
# 删除明文配置
rm -f .env

# 清理容器（环境变量会清除）
docker-compose down

# 仅保留加密文件
ls -la .env.7z  # 这个可以安全保存和分享
```

---

## 技术支持

- **问题反馈**: https://github.com/yourname/sni-rag/issues
- **文档**: https://github.com/yourname/sni-rag/blob/master/README.md
- **Docker Hub**:
  - 后端: https://hub.docker.com/r/yourname/sni-backend
  - 前端: https://hub.docker.com/r/yourname/sni-frontend
