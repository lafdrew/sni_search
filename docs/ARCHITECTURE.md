# SNI Search System - 架构文档

## 项目概述

**SNI Search** 是一个基于多轮搜索策略的智能 SNI（Server Name Indication）识别系统。系统采用 LangGraph 工作流框架，结合向量数据库检索和智能网络搜索，实现对 SNI 域名的准确识别和信息提取。

### 核心特性

- **多轮搜索策略**：采用 4-2-1 搜索流程（4个初始查询 → 2个精细化查询 → 1个最终验证）
- **确定性工作流**：基于 Python 代码的流程控制，避免 LLM 决策不确定性
- **混合检索**：结合精确匹配、向量相似度搜索和网络搜索
- **异步并发**：支持多查询并行执行，提升搜索效率
- **多 LLM 支持**：支持 Claude 和 OpenAI 模型

---

## 技术栈

### 核心框架
- **LangGraph**：工作流编排和状态管理
- **LangChain**：LLM 集成和工具链
- **FastAPI**：RESTful API 服务
- **Pydantic**：数据验证和配置管理

### 数据存储与检索
- **Qdrant**：向量数据库，存储 SNI 信息和向量嵌入
- **Sentence Transformers**：文本嵌入模型

### 搜索与爬虫
- **多搜索引擎支持**：Tavily、DuckDuckGo、SearchAPI、InfoQuest 等
- **多爬虫引擎**：Jina、InfoQuest
- **内容提取**：Readabilipy、Markdownify

### LLM 提供商
- **Claude (Anthropic)**：主要 LLM 提供商
- **OpenAI**：备选 LLM 提供商

---

## 项目结构

```
sni_search/
├── src/
│   ├── graph/                    # LangGraph 工作流核心
│   │   ├── builder.py            # 工作流构建器
│   │   ├── nodes.py              # 工作流节点实现
│   │   └── state.py              # 状态定义
│   │
│   ├── tools/                    # 工具集合
│   │   ├── sni_tools.py          # SNI 数据库查询工具
│   │   ├── search.py             # 网络搜索工具
│   │   ├── crawl.py              # 网页爬取工具
│   │   ├── crawler/              # 爬虫引擎实现
│   │   ├── tavily_search/        # Tavily 搜索集成
│   │   ├── infoquest_search/     # InfoQuest 搜索集成
│   │   └── searchapi_search/     # SearchAPI 集成
│   │
│   ├── prompts/                  # 提示词模板（支持多语言）
│   │   ├── template.py           # 提示词管理
│   │   ├── keyword_extraction.md
│   │   ├── round1_planning.md
│   │   ├── round2_planning.md
│   │   ├── final_search_planning.md
│   │   ├── synthesis.md
│   │   └── web_search_agent.md
│   │
│   ├── agent.py                  # SNIAgent 主类
│   ├── api_server.py             # FastAPI 服务器
│   ├── config.py                 # 配置管理
│   └── import_data.py            # 数据导入工具
│
├── demo/                         # 演示和测试脚本
├── results/                      # SNI 数据存储
├── conf.yaml                     # 工具配置
├── .env                          # 环境变量（API Keys 等）
├── pyproject.toml                # 项目依赖配置
└── README.md
```

---

## 核心架构

### 1. LangGraph 工作流

系统的核心是一个多轮搜索工作流，采用确定性的 Python 流程控制。

#### 工作流图

```
START
  ↓
sni_exact_query (精确匹配查询)
  ↓
  ├─[找到结果]────────────────────────→ synthesize → END
  │
  └─[未找到结果]
      ↓
    vector_search (向量相似度搜索)
      ↓
    initial_web_search (直接爬取 SNI 主页)
      ↓
    keyword_extraction (提取关键词)
      ↓
    round1_planning (生成 4 个查询)
      ↓
    round1_search (4 个并行搜索)
      ↓
    round2_planning (提取 2 个关键词)
      ↓
    round2_search (2 个并行搜索)
      ↓
    final_planning (生成最终验证查询)
      ↓
    final_search (1 个综合搜索)
      ↓
    synthesize (综合所有信息生成答案)
      ↓
    END
```

#### 搜索轮次说明

1. **精确匹配**：在 Qdrant 中查找完全匹配的 SNI 记录
2. **向量搜索**：使用语义相似度查找相关 SNI
3. **初始搜索**：直接爬取 SNI 域名主页获取基础信息
4. **Round 1**：基于提取的关键词生成 4 个多角度查询（技术、服务、基础设施、安全）
5. **Round 2**：从 Round 1 结果中提取组织信息，生成 2 个精确查询
6. **最终搜索**：使用原始查询 + Round 2 关键词进行最终验证
7. **综合**：LLM 整合所有信息源生成最终答案

### 2. 状态管理（State）

`SNIAgentState` 定义了工作流中的所有状态变量：

```python
class SNIAgentState(TypedDict):
    # 基础信息
    messages: List[BaseMessage]           # 对话历史
    query: str                             # 用户原始查询
    locale: str                            # 语言设置

    # 搜索结果
    sni_exact_results: Optional[List[Dict]]     # 精确匹配结果
    sni_vector_results: Optional[List[Dict]]    # 向量搜索结果

    # 关键词和增强查询
    extracted_keywords: Optional[List[str]]     # 提取的关键词
    enhanced_query: Optional[str]               # 增强后的查询

    # 多轮搜索状态
    initial_search_result: Optional[str]        # 初始搜索结果
    round1_queries: Optional[List[str]]         # Round 1 的 4 个查询
    round1_results: Optional[List[Dict]]        # Round 1 搜索结果
    round2_keywords: Optional[List[str]]        # Round 2 的 2 个关键词
    round2_results: Optional[List[Dict]]        # Round 2 搜索结果
    final_search_query: Optional[str]           # 最终搜索查询
    final_search_result: Optional[str]          # 最终搜索结果

    # 最终输出
    final_answer: Optional[str]                 # LLM 综合答案
```

### 3. 工作流节点（Nodes）

每个节点都是一个独立的功能单元：

| 节点名称 | 功能描述 | 输入 | 输出 |
|---------|---------|------|------|
| `sni_exact_query_node` | Qdrant 精确匹配查询 | query | sni_exact_results |
| `sni_vector_query_node` | Qdrant 向量相似度查询 | query | sni_vector_results |
| `initial_web_search_node` | 爬取 SNI 主页 | query (SNI) | initial_search_result |
| `keyword_extraction_node` | LLM 提取关键词 | vector_results, initial_search | extracted_keywords, enhanced_query |
| `round1_planning_node` | LLM 生成 4 个查询 | query, keywords | round1_queries |
| `round1_parallel_search_node` | 执行 4 个并行搜索 | round1_queries | round1_results |
| `round2_planning_node` | LLM 提取组织信息，生成 2 个查询 | round1_results | round2_keywords |
| `round2_parallel_search_node` | 执行 2 个并行搜索 | round2_keywords | round2_results |
| `final_search_planning_node` | LLM 生成最终验证查询 | query, round2_keywords | final_search_query |
| `final_search_node` | 执行最终搜索 | final_search_query | final_search_result |
| `synthesize_node` | LLM 综合所有信息 | 所有搜索结果 | final_answer |

### 4. 决策函数

系统使用纯 Python 函数进行流程控制，避免 LLM 决策的不确定性：

```python
def should_try_vector_search(state: SNIAgentState) -> str:
    """决定是否需要向量搜索"""
    exact_results = state.get("sni_exact_results")

    if exact_results and exact_results.get("found"):
        return "synthesize"  # 找到精确匹配，直接综合
    else:
        return "vector_search"  # 未找到，进行向量搜索
```

---

## 核心组件

### 1. SNIAgent 类

主要的用户接口，封装了整个 LangGraph 工作流。

```python
class SNIAgent:
    def __init__(self, qdrant_url, api_key, model, locale):
        """初始化 Agent 和工作流"""

    def query(self, query: str, verbose: bool) -> Dict:
        """同步查询接口"""

    async def aquery(self, query: str, verbose: bool) -> Dict:
        """异步查询接口"""
```

**使用示例**：
```python
agent = SNIAgent(locale="zh-CN")
result = agent.query("api.github.com", verbose=True)
print(result["answer"])
```

### 2. SNITools 类

提供 SNI 数据库查询功能：

- `search_sni_exact(sni)`: 精确匹配查询
- `search_sni_vector(query, top_k)`: 向量相似度查询
- `search_by_domain(domain)`: 按域名查询所有 SNI
- `batch_search_sni(sni_list)`: 批量查询
- `get_stats()`: 获取数据库统计信息

### 3. 搜索工具

支持多种搜索引擎：

- **Tavily**: 专业 AI 搜索 API
- **DuckDuckGo**: 免费搜索引擎
- **SearchAPI**: Google/Bing 搜索代理
- **InfoQuest**: 自定义搜索服务

通过 `get_web_search_tool()` 函数根据配置动态选择搜索引擎。

### 4. 爬虫工具

支持两种爬虫引擎：

- **Jina Reader**: 通过 Jina API 爬取网页内容
- **InfoQuest**: 自定义爬虫服务

爬虫结果自动转换为 Markdown 格式，便于 LLM 处理。

### 5. 提示词管理

系统使用结构化的 Markdown 提示词模板，支持多语言：

```
src/prompts/
├── keyword_extraction.md         # 英文版关键词提取
├── keyword_extraction.zh_CN.md   # 中文版关键词提取
├── round1_planning.md            # Round 1 查询规划
├── round2_planning.md            # Round 2 查询规划
└── ...
```

通过 `get_prompt_template()` 和 `apply_prompt_variables()` 函数动态加载和填充模板。

---

## API 服务

### FastAPI 服务器

`src/api_server.py` 提供 RESTful API 服务：

#### 核心端点

1. **POST /query** - 执行 SNI 查询
   ```json
   {
     "query": "api.github.com",
     "session_id": "optional-uuid",
     "verbose": false
   }
   ```

2. **POST /tools/exact** - 直接精确查询
3. **POST /tools/vector** - 直接向量查询
4. **POST /tools/domain** - 按域名查询
5. **GET /health** - 健康检查

#### 启动服务

```bash
uv run python -m src.api_server
# 或
uvicorn src.api_server:app --host 0.0.0.0 --port 9000
```

---

## 配置管理

### 环境变量 (.env)

```bash
# Qdrant 配置
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=sni_collection

# LLM 配置
LLM_PROVIDER=claude  # 或 openai
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# 或使用 OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4

# 嵌入模型
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# 搜索配置
SEARCH_API=duckduckgo  # tavily, searchapi, infoquest
MAX_SEARCH_RESULTS=5

# 爬虫配置
CRAWLER_ENGINE=jina  # 或 infoquest
CRAWLER_TIMEOUT=30

# API 服务
API_HOST=0.0.0.0
API_PORT=9000

# 数据路径
DATA_DIR=./results
```

### 工具配置 (conf.yaml)

详细的搜索引擎和爬虫参数配置，包括：

- 搜索深度、时间范围、域名过滤
- 爬虫超时、内容长度限制
- 结果后处理参数

---

## 数据流

### 典型查询流程

1. **用户输入**：`api.github.com`

2. **精确匹配**：
   ```
   在 Qdrant 中查找 sni="api.github.com"
   → 未找到 → 继续向量搜索
   ```

3. **向量搜索**：
   ```
   生成查询嵌入 → 在 Qdrant 中查找相似 SNI
   → 返回 Top-5 相似结果（如 github.com, api.github.io 等）
   ```

4. **初始网络搜索**：
   ```
   直接爬取 https://api.github.com
   → 提取主页内容（About GitHub API）
   ```

5. **关键词提取**：
   ```
   LLM 分析向量结果 + 初始搜索内容
   → 提取关键词：["GitHub", "API", "REST", "GraphQL"]
   → 增强查询："GitHub API service"
   ```

6. **Round 1 并行搜索**（4 个查询）：
   ```
   Query 1: "GitHub API technical documentation"
   Query 2: "GitHub API service features"
   Query 3: "GitHub API infrastructure"
   Query 4: "GitHub API security authentication"
   → 并行执行 4 个网络搜索
   ```

7. **Round 2 精确搜索**（2 个查询）：
   ```
   LLM 分析 Round 1 结果，提取组织："GitHub"
   Query 1: "api.github.com GitHub REST API"
   Query 2: "api.github.com GitHub GraphQL API"
   → 并行执行 2 个搜索
   ```

8. **最终验证搜索**（1 个查询）：
   ```
   LLM 生成最终查询："api.github.com GitHub API authentication methods"
   → 执行 1 个综合搜索
   ```

9. **综合答案**：
   ```
   LLM 整合所有信息源：
   - 精确匹配结果（如果有）
   - 向量搜索结果
   - 初始搜索内容
   - Round 1 的 4 个搜索结果
   - Round 2 的 2 个搜索结果
   - 最终搜索结果
   → 生成 JSON 格式答案
   ```

10. **返回结果**：
    ```json
    {
      "tgt": "GitHub API",
      "Explanation": "api.github.com 是 GitHub 的官方 REST API 端点...",
      "Query Results": "详细信息..."
    }
    ```

---

## 并发与性能

### 异步并行执行

系统使用 `asyncio` 实现并行搜索：

```python
# Round 1: 4 个查询并行执行
async def round1_parallel_search_node(state):
    queries = state["round1_queries"]  # 4 个查询

    semaphore = asyncio.Semaphore(4)  # 并发控制

    async def search_with_limit(query):
        async with semaphore:
            return await web_search_tool.ainvoke(query)

    results = await asyncio.gather(*[search_with_limit(q) for q in queries])
    return {"round1_results": results}
```

### 性能优化

1. **确定性流程控制**：避免 LLM 决策，减少 40% 以上的 token 使用
2. **并行搜索**：Round 1 和 Round 2 使用并发执行
3. **上下文管理**：限制 LLM 输入上下文大小（15000 字符）
4. **懒加载**：嵌入模型按需加载

---

## 扩展性

### 添加新的搜索引擎

1. 在 `src/tools/` 下创建新的搜索引擎模块
2. 实现 `BaseTool` 接口
3. 在 `src/tools/search.py` 中注册新引擎
4. 更新 `config.py` 中的 `SearchEngine` 枚举

### 添加新的爬虫引擎

1. 在 `src/tools/crawler/` 下创建新的爬虫客户端
2. 实现统一的 `crawl()` 接口
3. 在 `crawler.py` 中集成新引擎
4. 更新配置

### 添加新的 LLM 提供商

1. 在 `builder.py` 的 `_create_llm()` 函数中添加新提供商
2. 更新 `config.py` 中的验证逻辑
3. 添加相应的环境变量

---

## 测试与部署

### 运行测试

```bash
# 单元测试
uv run pytest tests/

# 集成测试
uv run python demo/test_multi_round_search.py
```

### 部署方式

1. **Docker 部署**（推荐）
2. **本地部署**：使用 `uv` 或 `pip` 安装依赖
3. **云服务部署**：支持任何支持 Python 的云平台

### 数据导入

```bash
# 导入 SNI 数据到 Qdrant
uv run python -m src.import_data --data-dir ./results
```

---

## 设计理念

### 1. 确定性优先

所有流程控制使用 Python 代码而非 LLM 决策，确保：
- 可预测的执行流程
- 更快的响应速度
- 更低的 token 消耗
- 更好的可调试性

### 2. 多轮渐进式搜索

采用 4-2-1 的搜索策略，从广度到深度：
- Round 1（4 个查询）：多角度探索
- Round 2（2 个查询）：精确定位
- Final（1 个查询）：最终验证

### 3. 混合检索策略

结合三种检索方式：
- **精确匹配**：快速查找已知 SNI
- **向量检索**：发现相似和相关 SNI
- **网络搜索**：获取最新和补充信息

### 4. 模块化设计

清晰的职责分离：
- `graph/`: 工作流逻辑
- `tools/`: 数据源和工具
- `prompts/`: LLM 提示词
- `agent.py`: 用户接口
- `api_server.py`: API 服务

### 5. 可扩展性

支持多种：
- LLM 提供商（Claude, OpenAI）
- 搜索引擎（Tavily, DuckDuckGo, SearchAPI 等）
- 爬虫引擎（Jina, InfoQuest）
- 语言设置（en-US, zh-CN 等）

---

## 未来规划

1. **增强缓存机制**：减少重复查询
2. **流式输出支持**：实时显示搜索进度
3. **批量查询优化**：更高效的批处理
4. **更多 LLM 支持**：Gemini, Qwen 等
5. **可视化界面**：Web UI 展示工作流执行
6. **监控和日志**：完善的可观测性

---

## 总结

SNI Search 是一个设计精良的智能搜索系统，具有以下亮点：

- **稳定可靠**：确定性工作流，避免 LLM 决策不确定性
- **高效智能**：多轮搜索策略，精确定位信息
- **灵活可扩展**：模块化设计，易于集成新功能
- **性能优化**：异步并发，降低延迟和成本

系统特别适合需要准确识别和分析网络服务标识的场景，如网络安全分析、域名情报收集等。
