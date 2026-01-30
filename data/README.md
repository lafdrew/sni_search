# Data Directory

此目录用于存储运行时数据，不会被提交到 Git。

## 目录结构

```
data/
├── qdrant/     # Qdrant 向量数据库持久化存储
├── results/    # SNI 查询结果和导出数据
└── models/     # 本地下载的模型文件（可选）
```

## 各目录说明

### qdrant/
- **作用**: Qdrant 向量数据库的持久化存储
- **内容**: 向量索引、集合数据、元数据
- **警告**: 删除此目录会导致所有向量数据丢失

### results/
- **作用**: SNI 查询结果、导入的原始数据
- **内容**: JSON 文件、导出报告
- **说明**: 可以安全删除，不影响系统运行

### models/
- **作用**: 本地模型文件（离线使用）
- **内容**: SentenceTransformer 嵌入模型
- **说明**: 可选，如果不使用本地模型，此目录为空

## Docker Volume 映射

在 `docker-compose.yml` 中配置：

```yaml
volumes:
  - ./data/qdrant:/qdrant/storage   # Qdrant 数据
  - ./data/results:/app/results     # 查询结果
  - ./data/models:/app/models:ro    # 本地模型（只读）
```

## 备份建议

```bash
# 备份整个 data 目录
tar czf sni-data-backup.tar.gz data/

# 只备份 Qdrant 数据
tar czf qdrant-backup.tar.gz data/qdrant/
```
