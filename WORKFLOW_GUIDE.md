# SNI RAG 系统完整工作流程

## 项目概述

SNI RAG 是一个基于 LangGraph 和 Claude 的智能 SNI (Server Name Indication) 识别系统，支持两种查询模式：
1. **Workflow 模式**：固定流程的 StateGraph
2. **Agent 模式**：LLM 主动决策调用工具

---

## 系统架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户输入查询                              │
│                    (例: "www.google.com")                        │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ├──────────────┬──────────────────┐
                     │              │                  │
            ┌────────▼─────┐  ┌────▼──────┐   ┌──────▼──────┐
            │   CLI 工具   │  │ API 服务器 │   │  直接调用   │
            └────────┬─────┘  └────┬──────┘   └──────┬──────┘
                     │              │                  │
                     └──────────────┴──────────────────┘
                                    │
                     ┌──────────────┴──────────────┐
                     │                              │
            ┌────────▼────────┐         ┌─────────▼────────┐
            │  Workflow 模式  │         │   Agent 模式      │
            │  (固定流程)     │         │  (智能决策)       │
            └────────┬────────┘         └─────────┬────────┘
                     │                            │
                     └────────────┬───────────────┘
                                  │
                     ┌────────────▼────────────┐
                     │      工具层 (Tools)      │
                     │  - search_sni_exact     │
                     │  - search_sni_vector    │
                     │  - search_by_domain     │
                     └────────────┬────────────┘
                                  │
                     ┌────────────▼────────────┐
                     │   Qdrant 向量数据库      │
                     │  - SNI 数据              │
                     │  - 向量嵌入              │
                     └────────────┬────────────┘
                                  │
                     ┌────────────▼────────────┐
                     │    Claude LLM           │
                     │  - 理解查询              │
                     │  - 生成答案              │
                     └────────────┬────────────┘
                                  │
                     ┌────────────▼────────────┐
                     │      结构化输出          │
                     │  {                       │
                     │    "Website/Service",    │
                     │    "Explanation",        │
                     │    "Query Results"       │
                     │  }                       │
                     └─────────────────────────┘
```

---

## 第一阶段：数据准备

### 1.1 数据导入流程

**文件**: `src/import_data.py`

```
原始 JSON 数据 (results/*.json)
    │
    ├─ 读取每个 JSON 文件
    │
    ├─ 提取字段:
    │   - sni: SNI 名称
    │   - domain: 主域名
    │   - all_snis: 关联的所有 SNI
    │   - alpn_protocols: 支持的协议
    │
    ├─ 生成向量嵌入
    │   └─ 使用 SentenceTransformer
    │       模型: paraphrase-multilingual-MiniLM-L12-v2
    │       输入: f"{sni} {domain}"
    │       输出: 384 维向量
    │
    └─ 写入 Qdrant
        ├─ 向量: embedding
        └─ Payload: {sni, domain, all_snis, alpn_protocols, ...}
```

**执行命令**:
```bash
uv run python -m src.import_data --data-dir results
```

**数据结构示例**:
```json
{
  "sni": "www.google.com",
  "domain": "google.com",
  "all_snis": ["www.google.com", "google.com", "accounts.google.com"],
  "alpn_protocols": ["h2", "http/1.1"],
  "total_count": 34
}
```

### 1.2 Qdrant 数据库结构

```
Collection: sni_domain_mapping
│
├─ Vector: [384 维 float 数组]
│
└─ Payload:
    ├─ sni: string
    ├─ domain: string
    ├─ all_snis: string[]
    ├─ alpn_protocols: string[]
    └─ total_count: integer
```

---

## 第二阶段：查询处理

### 2.1 输入接口

#### 方式 1: CLI 工具
```bash
uv run python demo/cli.py "www.google.com"
```

#### 方式 2: API 调用
```bash
# Workflow 模式
curl -X POST http://localhost:9000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "www.google.com"}'

# Agent 模式
curl -X POST http://localhost:9000/api/query/agent \
  -H "Content-Type: application/json" \
  -d '{"query": "www.google.com"}'
```

#### 方式 3: Python 代码
```python
from src.agent import create_sni_agent, stream_query

agent = create_sni_agent()
result = stream_query(agent, "www.google.com")
```

---

## 第三阶段：两种查询模式

### 模式 A: Workflow 模式 (固定流程)

**文件**: `src/graph.py`, `src/nodes.py`

#### 工作流程图

```
┌─────────────────┐
│   用户查询       │
│  "www.google.com"│
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Node 1: understand_query               │
│  ┌─────────────────────────────────┐   │
│  │ LLM 分析查询意图                 │   │
│  │ 输入: query                      │   │
│  │ 输出: query_type (exact/vector) │   │
│  │ 正则提取: SNI/域名              │   │
│  └─────────────────────────────────┘   │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Node 2: route_query                    │
│  根据 query_type 路由                   │
│  ┌──────────┬──────────┬──────────┐   │
│  │  exact   │  vector  │  domain  │   │
│  └────┬─────┴────┬─────┴────┬─────┘   │
└───────┼──────────┼──────────┼─────────┘
        │          │          │
        ▼          ▼          ▼
   ┌────────┐ ┌─────────┐ ┌──────────┐
   │ exact  │ │ vector  │ │  domain  │
   │ search │ │ search  │ │  search  │
   └────┬───┘ └────┬────┘ └────┬─────┘
        │          │            │
        └──────────┴────────────┘
                   │
                   ▼
        ┌──────────────────┐
        │ Node 3: aggregate │
        │  结果聚合          │
        │  评估是否需要更多  │
        └──────────┬────────┘
                   │
                   ▼
          ┌────────┴────────┐
          │  need_more?     │
          └────┬───────┬────┘
          yes  │       │  no
               │       │
               ▼       ▼
        ┌──────────┐  ┌──────────────┐
        │继续搜索  │  │ Node 4:       │
        │(vector)  │  │ generate_answer│
        └──────────┘  │  LLM 生成答案  │
                      └───────┬────────┘
                              │
                              ▼
                      ┌──────────────┐
                      │  最终 JSON    │
                      │  答案         │
                      └──────────────┘
```

#### 详细流程

**Step 1: understand_query (理解查询)**

```python
# 文件: src/nodes.py:34
def understand_query(self, state: SNIGraphState):
    query = state["query"]  # "www.google.com"

    # LLM 分析
    prompt = """
    分析查询类型:
    - exact: 完整 SNI 名称
    - vector: 模糊搜索
    - domain: 查询域名下所有 SNI
    """

    response = self.llm.invoke(prompt + query)
    # LLM 输出: "Type: exact"

    # 正则提取实体
    sni_list = re.findall(SNI_PATTERN, query)
    # 结果: ["www.google.com"]

    return {
        "query_type": "exact",
        "extracted_entities": {"sni_list": ["www.google.com"]},
        "step_count": 1
    }
```

**Step 2: route_query (路由决策)**

```python
# 文件: src/nodes.py:157
def route_query(self, state: SNIGraphState):
    query_type = state["query_type"]  # "exact"

    route_map = {
        "exact": "exact_search",
        "vector": "vector_search",
        "domain": "domain_search"
    }

    return route_map[query_type]  # 返回 "exact_search"
```

**Step 3: exact_search_node (精确搜索)**

```python
# 文件: src/nodes.py:177
def exact_search_node(self, state: SNIGraphState):
    sni = "www.google.com"  # 从 extracted_entities 提取

    # 调用工具
    result = self.tools.search_sni_exact(sni)

    # 工具内部: Qdrant 精确匹配
    # 文件: src/tools.py:45
    results = qdrant_client.scroll(
        collection_name="sni_domain_mapping",
        scroll_filter=Filter(
            must=[FieldCondition(key="sni", match=MatchValue(value=sni))]
        ),
        limit=100
    )

    return {
        "tool_calls": [{"tool": "search_sni_exact", "input": sni}],
        "tool_results": [result],
        "step_count": 2
    }
```

**Step 4: aggregate_results (聚合结果)**

```python
# 文件: src/nodes.py:267
def aggregate_results(self, state: SNIGraphState):
    tool_results = state["tool_results"]

    # 检查是否找到结果
    if tool_results and tool_results[0].get("found"):
        need_more = False
    else:
        need_more = True

    return {"need_more_info": need_more, "step_count": 3}
```

**Step 5: generate_answer (生成答案)**

```python
# 文件: src/nodes.py:319
def generate_answer(self, state: SNIGraphState):
    tool_results = state["tool_results"]

    # 构建上下文
    context = f"""
    Found 100 records for SNI: www.google.com
    Domains: crowdstrike.com, notion.so, wired.com, ...
    """

    # LLM 生成答案
    prompt = """
    基于以下数据生成 JSON 回答:
    {context}

    格式:
    {{
      "Website/Service": "...",
      "Explanation": "...",
      "Query Results": "..."
    }}
    """

    response = self.llm.invoke(prompt)

    return {
        "answer": response.content,  # JSON 字符串
        "step_count": 4
    }
```

---

### 模式 B: Agent 模式 (智能决策)

**文件**: `src/agent.py`

#### 工作流程图

```
┌─────────────────┐
│   用户查询       │
│  "google.com"   │
└────────┬────────┘
         │
         ▼
┌──────────────────────────────────────────────┐
│  Iteration 1: LLM 思考                        │
│  ┌────────────────────────────────────────┐  │
│  │ 输入消息:                               │  │
│  │ [                                      │  │
│  │   {role: "system", content: "你是专家...│  │
│  │    有3个工具: exact, vector, domain"}, │  │
│  │   {role: "user", content: "google.com"}│  │
│  │ ]                                      │  │
│  └────────────────────────────────────────┘  │
│                      │                        │
│                      ▼                        │
│  ┌────────────────────────────────────────┐  │
│  │ LLM 决策                                │  │
│  │ "我需要精确搜索 google.com"             │  │
│  │                                        │  │
│  │ 返回:                                   │  │
│  │ tool_calls=[{                          │  │
│  │   name: "search_sni_exact",            │  │
│  │   args: {"sni": "google.com"}          │  │
│  │ }]                                     │  │
│  └────────────────────────────────────────┘  │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │  执行工具         │
         │  search_sni_exact│
         └────────┬─────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  工具返回结果     │
         │  {found: true,   │
         │   match_count: 82}│
         └────────┬─────────┘
                  │
                  ▼
┌──────────────────────────────────────────────┐
│  Iteration 2: LLM 生成答案                    │
│  ┌────────────────────────────────────────┐  │
│  │ 输入消息:                               │  │
│  │ [                                      │  │
│  │   {role: "system", ...},               │  │
│  │   {role: "user", content: "google.com"},│  │
│  │   AIMessage(tool_calls=[...]),         │  │
│  │   ToolMessage(content="{found: true,..."│  │
│  │ ]                                      │  │
│  └────────────────────────────────────────┘  │
│                      │                        │
│                      ▼                        │
│  ┌────────────────────────────────────────┐  │
│  │ LLM 生成最终答案                        │  │
│  │ 返回:                                   │  │
│  │ content='{                             │  │
│  │   "Website/Service": "Google",         │  │
│  │   "Explanation": "...",                │  │
│  │   "Query Results": "..."               │  │
│  │ }'                                     │  │
│  └────────────────────────────────────────┘  │
└──────────────────┬───────────────────────────┘
                   │
                   ▼
         ┌─────────────────┐
         │  返回结果         │
         └─────────────────┘
```

#### 详细流程

**Iteration 1: 工具调用**

```python
# 文件: src/agent.py:101
messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": "google.com"}
]

# 调用 LLM
response = llm_with_tools.invoke(messages)

# 响应结构
AIMessage(
    content="",  # 可能为空
    tool_calls=[
        {
            "name": "search_sni_exact",
            "args": {"sni": "google.com"},
            "id": "toolu_xxx"
        }
    ]
)

# 添加到消息历史
messages.append(response)

# 执行工具
tool_result = search_sni_exact("google.com")
# 返回: {'found': True, 'sni': 'google.com', 'match_count': 82, ...}

# 添加工具结果
messages.append(ToolMessage(
    content=str(tool_result),
    tool_call_id="toolu_xxx"
))
```

**Iteration 2: 生成答案**

```python
# 此时 messages 包含:
messages = [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "google.com"},
    AIMessage(tool_calls=[...]),
    ToolMessage(content="{'found': True, ...}")
]

# 再次调用 LLM
response = llm_with_tools.invoke(messages)

# 响应结构
AIMessage(
    content='{
      "Website/Service": "Google",
      "Explanation": "Google is a multinational...",
      "Query Results": "Found 82 matches..."
    }',
    tool_calls=None  # 没有工具调用，表示完成
)

# 返回最终答案
return {
    "query": "google.com",
    "answer": response.content,
    "tool_calls": [{"tool": "search_sni_exact", "args": {...}}],
    "iterations": 2
}
```

---

## 第四阶段：工具层详解

### 工具 1: search_sni_exact (精确搜索)

**文件**: `src/tools.py:45`

```python
def search_sni_exact(sni: str):
    """精确匹配 SNI 名称"""

    # 1. Qdrant 查询
    results = qdrant_client.scroll(
        collection_name="sni_domain_mapping",
        scroll_filter=Filter(
            must=[FieldCondition(
                key="sni",
                match=MatchValue(value=sni)
            )]
        ),
        limit=100
    )

    # 2. 处理结果
    if not results[0]:
        return {"found": False, "sni": sni}

    # 3. 提取所有匹配记录
    all_matches = []
    for point in results[0]:
        all_matches.append({
            "sni": point.payload["sni"],
            "domain": point.payload["domain"],
            "all_related_snis": point.payload["all_snis"],
            "protocols": point.payload["alpn_protocols"]
        })

    return {
        "found": True,
        "sni": sni,
        "match_count": len(all_matches),
        "matches": all_matches
    }
```

### 工具 2: search_sni_vector (向量搜索)

**文件**: `src/tools.py:84`

```python
def search_sni_vector(query: str, top_k: int = 5):
    """向量相似度搜索"""

    # 1. 生成查询向量
    query_vector = sentence_transformer.encode(query).tolist()
    # 输入: "google"
    # 输出: [0.123, -0.456, 0.789, ...] (384 维)

    # 2. Qdrant 向量搜索
    results = qdrant_client.query_points(
        collection_name="sni_domain_mapping",
        query=query_vector,
        limit=top_k,
        score_threshold=0.5
    )

    # 3. 返回最相似的结果
    return [
        {
            "sni": hit.payload["sni"],
            "domain": hit.payload["domain"],
            "score": round(hit.score, 3),  # 相似度分数
            "protocols": hit.payload["alpn_protocols"]
        }
        for hit in results.points
    ]
```

### 工具 3: search_by_domain (域名搜索)

**文件**: `src/tools.py:120`

```python
def search_by_domain(domain: str, limit: int = 20):
    """搜索域名下的所有 SNI"""

    # Qdrant 查询
    results = qdrant_client.scroll(
        collection_name="sni_domain_mapping",
        scroll_filter=Filter(
            must=[FieldCondition(
                key="domain",
                match=MatchValue(value=domain)
            )]
        ),
        limit=limit
    )

    # 去重并返回
    unique_snis = []
    seen = set()
    for point in results[0]:
        sni = point.payload["sni"]
        if sni not in seen:
            seen.add(sni)
            unique_snis.append({
                "sni": sni,
                "domain": point.payload["domain"],
                "protocols": point.payload["alpn_protocols"]
            })

    return unique_snis
```

---

## 第五阶段：LLM 调用详解

### 非流式调用

```python
# 文件: src/agent.py:116
response = llm_with_tools.invoke(messages)

# 底层实现 (LangChain)
def invoke(messages):
    # 1. 构建 API 请求
    api_request = {
        "model": "claude-sonnet-4-5-20250929",
        "messages": messages,
        "tools": [
            {
                "name": "search_sni_exact",
                "description": "Exact match SNI name...",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sni": {"type": "string"}
                    }
                }
            },
            # ... 其他工具
        ],
        "temperature": 0
    }

    # 2. 发送到 Claude API
    response = requests.post(
        "https://api.lingyaai.cn/v1/messages",
        headers={"x-api-key": api_key},
        json=api_request
    )

    # 3. 解析响应
    return AIMessage(
        content=response["content"],
        tool_calls=response.get("tool_calls", [])
    )
```

### 流式调用

```python
# 文件: src/agent.py:368
for chunk in llm_with_tools.stream(messages):
    # chunk 是响应的一个片段

    # Chunk 类型:
    # 1. 元数据 chunk
    if chunk.response_metadata:
        # {'model_name': 'claude-sonnet-4-5-20250929'}
        pass

    # 2. 工具调用 chunk
    if chunk.tool_calls:
        # [{'name': 'search_sni_exact', 'args': {...}}]
        pass

    # 3. 文本内容 chunk
    if chunk.content:
        # [{'type': 'text', 'text': 'Google'}]
        print(chunk.content, end='', flush=True)

    # 4. JSON 增量 chunk
    if 'input_json_delta' in chunk.content:
        # {'partial_json': '{"sni"'}
        # {'partial_json': ': "google.com"'}
        # {'partial_json': '}'}
        pass
```

---

## 第六阶段：输出格式

### 最终输出结构

```python
{
    "query": "www.google.com",
    "answer": '{
        "Website/Service": "Google",
        "Explanation": "Google is a multinational technology company...",
        "Query Results": "Found 100 matches for www.google.com..."
    }',
    "tool_calls": [
        {"tool": "search_sni_exact", "args": {"sni": "www.google.com"}}
    ],
    "steps": 2,
    "trace": [
        {
            "iteration": 1,
            "tool": "search_sni_exact",
            "args": {"sni": "www.google.com"},
            "result": {"found": True, "match_count": 100, ...}
        }
    ]
}
```

### CLI 格式化输出

```
============================================================
Website/Service: Google

Explanation: Google is a multinational technology company...

Query Results:
------------------------------------------------------------
Found exact match for 'www.google.com' with 100 database records.
============================================================
```

---

## 性能与优化

### Token 使用统计

```
Iteration 1 (工具调用):
  Input tokens:  1,176  (系统提示 + 工具定义 + 用户查询)
  Output tokens:    59  (工具调用决策)
  Total:         1,235

Iteration 2 (生成答案):
  Input tokens:  29,063  (系统提示 + 工具定义 + 查询 + 工具结果)
  Output tokens:    213  (JSON 答案)
  Total:         29,276

总计: 30,511 tokens
```

### 响应时间

```
1. Qdrant 查询:     ~100ms
2. LLM 调用:        ~2-3s
3. 工具执行:        ~200ms
4. 总响应时间:      ~3-5s
```

---

## 关键配置

### 环境变量 (.env)

```bash
# Qdrant
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=sni_domain_mapping

# Claude API
ANTHROPIC_API_KEY=sk-xxx
ANTHROPIC_BASE_URL=https://api.lingyaai.cn

# 模型
CLAUDE_MODEL=claude-sonnet-4-5-20250929
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# API Server
API_HOST=0.0.0.0
API_PORT=9000
```

---

## 总结

### 数据流向

```
用户查询
  ↓
[CLI / API / 代码]
  ↓
[Workflow 模式 / Agent 模式]
  ↓
[工具层: exact/vector/domain search]
  ↓
[Qdrant 数据库]
  ↓
[Claude LLM 生成答案]
  ↓
结构化 JSON 输出
```

### 核心差异

| 维度 | Workflow 模式 | Agent 模式 |
|------|--------------|-----------|
| 流程 | 固定的节点顺序 | LLM 动态决策 |
| 控制 | 代码逻辑控制 | LLM 智能控制 |
| 灵活性 | 较低 | 很高 |
| Token 使用 | 较少 | 较多 |
| 适用场景 | 标准查询 | 复杂查询 |

### 技术栈

- **LLM**: Claude Sonnet 4.5
- **框架**: LangChain + LangGraph
- **向量DB**: Qdrant
- **嵌入模型**: SentenceTransformers
- **API**: FastAPI + Uvicorn
- **语言**: Python 3.11+

---

## 使用示例

### 快速开始

```bash
# 1. 安装依赖
uv sync

# 2. 配置环境
cp .env.example .env
# 编辑 .env 填入 API key

# 3. 导入数据
uv run python -m src.import_data --data-dir results

# 4. 启动 API
uv run python -m src.api_server

# 5. 测试查询
uv run python demo/cli.py "www.google.com"
```

### 流式输出演示

```bash
# 查看 LLM 完整思考过程
uv run python demo/interactive_verbose.py
```

---

**项目地址**: E:\sni_search
**文档版本**: 1.0
**更新日期**: 2025-12-18
