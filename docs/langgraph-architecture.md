# LangGraph 在 SNI Search 项目中的应用

## 目录
- [概述](#概述)
- [什么是 LangGraph](#什么是-langgraph)
- [项目架构](#项目架构)
- [工作流设计](#工作流设计)
- [状态管理](#状态管理)
- [节点实现](#节点实现)
- [流程控制](#流程控制)
- [使用示例](#使用示例)
- [关键特性](#关键特性)

---

## 概述

SNI Search 是一个基于 LangGraph 构建的多轮迭代搜索系统，用于识别和分析 SNI（Server Name Indication）域名信息。该系统通过 **LangGraph** 实现了一个复杂的多阶段工作流，包含向量搜索、Web搜索、关键词提取和结果综合等步骤。

### 项目特点
- 使用 LangGraph 构建有状态的 Agent 工作流
- 支持多轮迭代搜索策略（最多8轮Web搜索）
- 100% Python 代码控制流程，确保可靠性
- 支持多种 LLM 提供商（Claude、OpenAI）
- 并行搜索能力（asyncio + 并发控制）

---

## 什么是 LangGraph

LangGraph 是 LangChain 生态系统中的一个框架，用于构建有状态、多步骤的 Agent 工作流。它提供了：

### 核心概念
1. **状态图（StateGraph）**: 使用图结构组织工作流
2. **节点（Nodes）**: 执行特定任务的函数
3. **边（Edges）**: 连接节点，定义执行顺序
4. **状态（State）**: 在节点间传递的共享数据

### 为什么选择 LangGraph
- **可视化工作流**: 清晰的图结构，易于理解和维护
- **状态管理**: 自动管理节点间的数据传递
- **灵活控制**: 支持条件分支、循环等复杂逻辑
- **异步支持**: 原生支持异步执行和并行处理
- **可观测性**: 内置对 LangSmith 的支持，方便调试和监控

---

## 项目架构

### 文件结构
```
src/
├── graph/
│   ├── __init__.py
│   ├── builder.py          # 创建和编译 LangGraph 工作流
│   ├── state.py            # 定义工作流状态（TypedDict）
│   └── nodes.py            # 实现所有工作流节点
├── tools/
│   ├── sni_tools.py        # SNI 数据库查询工具
│   ├── search.py           # Web 搜索工具
│   └── crawler/            # 网页爬取工具
├── prompts/
│   └── template.py         # Jinja2 模板系统
└── config.py               # 配置管理
```

### 核心组件关系
```
┌─────────────────────────────────────────────────┐
│           create_sni_graph()                    │
│         (builder.py)                            │
│                                                 │
│  ┌────────────────────────────────────────┐   │
│  │   StateGraph(SNIAgentState)            │   │
│  │                                        │   │
│  │   ┌──────────────────┐                │   │
│  │   │  Workflow Nodes  │                │   │
│  │   │  (nodes.py)      │                │   │
│  │   └──────────────────┘                │   │
│  │           │                            │   │
│  │           ├─ sni_exact_query          │   │
│  │           ├─ sni_vector_query         │   │
│  │           ├─ initial_web_search       │   │
│  │           ├─ keyword_extraction       │   │
│  │           ├─ round1_planning          │   │
│  │           ├─ round1_parallel_search   │   │
│  │           ├─ round2_planning          │   │
│  │           ├─ round2_parallel_search   │   │
│  │           ├─ final_search_planning    │   │
│  │           ├─ final_search             │   │
│  │           └─ synthesize               │   │
│  │                                        │   │
│  └────────────────────────────────────────┘   │
│                                                 │
│  Compiled Graph → Ready for Execution          │
└─────────────────────────────────────────────────┘
```

---

## 工作流设计

### 完整工作流图

```
START
  ↓
┌─────────────────────┐
│ sni_exact_query     │  # 1. 精确匹配查询
└─────────────────────┘
          ↓
    [Decision: 是否找到精确匹配？]
          ↓
    ┌─────┴─────┐
    │           │
  [Yes]       [No]
    │           │
    │     ┌─────────────────────┐
    │     │ vector_search       │  # 2. 向量相似度搜索
    │     └─────────────────────┘
    │               ↓
    │     ┌─────────────────────┐
    │     │ initial_web_search  │  # 3. 初始Web搜索（爬取首页）
    │     └─────────────────────┘
    │               ↓
    │     ┌─────────────────────┐
    │     │ keyword_extraction  │  # 4. 关键词提取（LLM）
    │     └─────────────────────┘
    │               ↓
    │     ┌─────────────────────┐
    │     │ round1_planning     │  # 5. Round 1规划（生成4个查询）
    │     └─────────────────────┘
    │               ↓
    │     ┌─────────────────────┐
    │     │ round1_search       │  # 6. Round 1搜索（4次并行）
    │     └─────────────────────┘
    │               ↓
    │     ┌─────────────────────┐
    │     │ round2_planning     │  # 7. Round 2规划（提取2个关键词）
    │     └─────────────────────┘
    │               ↓
    │     ┌─────────────────────┐
    │     │ round2_search       │  # 8. Round 2搜索（2次并行）
    │     └─────────────────────┘
    │               ↓
    │     ┌─────────────────────┐
    │     │ final_planning      │  # 9. 最终搜索规划
    │     └─────────────────────┘
    │               ↓
    │     ┌─────────────────────┐
    │     │ final_search        │  # 10. 最终综合搜索
    │     └─────────────────────┘
    │               ↓
    └─────────┬─────┘
              ↓
    ┌─────────────────────┐
    │ synthesize          │  # 11. 综合所有结果
    └─────────────────────┘
              ↓
            END
```

### 多轮搜索策略

**总计最多 8 轮 Web 搜索**：
1. **初始搜索** (1次): 直接爬取 SNI 域名首页
2. **Round 1** (4次): 基于关键词的多角度并行搜索
3. **Round 2** (2次): 基于组织机构的精准搜索
4. **Final** (1次): 综合验证搜索

---

## 状态管理

### SNIAgentState 定义

状态是 LangGraph 的核心，所有节点共享同一个状态对象：

```python
class SNIAgentState(TypedDict):
    """工作流状态定义"""

    # 基础信息
    messages: List[BaseMessage]        # 对话历史
    query: str                         # 用户原始查询
    locale: str                        # 语言环境

    # 数据库搜索结果
    sni_exact_results: Optional[List[Dict[str, Any]]]    # 精确匹配结果
    sni_vector_results: Optional[List[Dict[str, Any]]]   # 向量搜索结果

    # 关键词和增强
    extracted_keywords: Optional[List[str]]              # 提取的关键词
    enhanced_query: Optional[str]                        # 增强后的查询

    # 多轮搜索结果
    initial_search_result: Optional[str]                 # 初始搜索结果
    round1_queries: Optional[List[str]]                  # Round 1的4个查询
    round1_results: Optional[List[Dict[str, Any]]]       # Round 1搜索结果
    round2_keywords: Optional[List[str]]                 # Round 2的2个关键词
    round2_results: Optional[List[Dict[str, Any]]]       # Round 2搜索结果
    final_search_query: Optional[str]                    # 最终搜索查询
    final_search_result: Optional[str]                   # 最终搜索结果

    # 最终输出
    final_answer: Optional[str]                          # 综合答案
```

### 状态传递机制

LangGraph 自动管理状态在节点间的传递：

```python
def some_node(state: SNIAgentState) -> Dict[str, Any]:
    """节点函数签名"""
    # 1. 读取状态
    query = state["query"]
    previous_results = state.get("round1_results", [])

    # 2. 执行业务逻辑
    new_results = process_something(query, previous_results)

    # 3. 返回状态更新（只需返回变化的字段）
    return {
        "round2_results": new_results,
        "some_new_field": "new value"
    }
```

---

## 节点实现

### 节点类型分类

项目中的节点可以分为以下几类：

#### 1. 数据查询节点
```python
def sni_exact_query_node(self, state: SNIAgentState) -> Dict[str, Any]:
    """查询 SNI 数据库（精确匹配）"""
    results = self.tools.search_sni_exact(state["query"])
    return {"sni_exact_results": results}

def sni_vector_query_node(self, state: SNIAgentState) -> Dict[str, Any]:
    """查询 SNI 数据库（向量相似度）"""
    results = self.tools.search_sni_vector(state["query"], top_k=5)
    return {"sni_vector_results": results}
```

#### 2. LLM 推理节点
```python
def keyword_extraction_node(self, state: SNIAgentState) -> Dict[str, Any]:
    """使用 LLM 从结果中提取关键词"""
    # 构造 prompt
    prompt = apply_prompt_variables(
        "keyword_extraction",
        variables={
            "query": state["query"],
            "results_summary": format_results(state["sni_vector_results"])
        }
    )

    # 调用 LLM
    response = self.llm.invoke([{"role": "user", "content": prompt}])

    # 解析 JSON 响应
    result = json.loads(response.content)

    return {
        "extracted_keywords": result["keywords"],
        "enhanced_query": result["enhanced_query"]
    }
```

#### 3. 异步搜索节点
```python
async def round1_parallel_search_node(self, state: SNIAgentState) -> Dict[str, Any]:
    """并行执行 4 个搜索查询"""
    queries = state.get("round1_queries", [])

    # 使用 Semaphore 控制并发
    semaphore = asyncio.Semaphore(4)

    async def search_with_limit(query: str) -> Dict:
        async with semaphore:
            result = await web_search_tool.ainvoke(query)
            return {"query": query, "result": result, "success": True}

    # 并行执行所有搜索
    results = await asyncio.gather(*[search_with_limit(q) for q in queries])

    return {"round1_results": results}
```

#### 4. 综合节点
```python
def synthesize_node(self, state: SNIAgentState) -> Dict[str, Any]:
    """综合所有搜索结果，生成最终答案"""
    # 收集所有数据源
    context_parts = []

    if state.get("sni_exact_results"):
        context_parts.append(f"Exact: {state['sni_exact_results']}")
    if state.get("round1_results"):
        context_parts.append(f"Round1: {state['round1_results']}")
    # ... 收集更多来源

    context = "\n\n".join(context_parts)

    # 使用 LLM 综合答案
    synthesis_prompt = apply_prompt_variables(
        "synthesis",
        variables={"query": state["query"], "context": context}
    )

    response = self.llm.invoke([
        {"role": "system", "content": get_prompt_template("sni_agent")},
        {"role": "user", "content": synthesis_prompt}
    ])

    return {"final_answer": response.content}
```

---

## 流程控制

### 1. 创建和编译工作流

```python
# src/graph/builder.py
def create_sni_graph(qdrant_url=None, api_key=None, model=None, locale="en-US"):
    """创建和编译 SNI Agent 工作流"""

    # 1. 初始化组件
    tools = SNITools(qdrant_url=qdrant_url)
    llm = _create_llm(provider=settings.LLM_PROVIDER, api_key=api_key, model=model)
    nodes = SNIWorkflowNodes(tools, llm, locale)

    # 2. 创建状态图
    workflow = StateGraph(SNIAgentState)

    # 3. 添加节点
    workflow.add_node("sni_exact_query", nodes.sni_exact_query_node)
    workflow.add_node("vector_search", nodes.sni_vector_query_node)
    workflow.add_node("initial_web_search", nodes.initial_web_search_node)
    # ... 添加更多节点

    # 4. 设置入口点
    workflow.set_entry_point("sni_exact_query")

    # 5. 添加边（定义执行顺序）
    workflow.add_conditional_edges(
        "sni_exact_query",
        should_try_vector_search,  # 决策函数
        {
            "vector_search": "vector_search",
            "synthesize": "synthesize"
        }
    )

    workflow.add_edge("vector_search", "initial_web_search")
    workflow.add_edge("initial_web_search", "keyword_extraction")
    # ... 添加更多边

    workflow.add_edge("synthesize", END)

    # 6. 编译图
    compiled_graph = workflow.compile()

    return compiled_graph
```

### 2. 条件分支

使用纯 Python 函数实现条件分支（100% 可靠）：

```python
def should_try_vector_search(state: SNIAgentState) -> str:
    """决策函数：是否需要向量搜索？"""
    exact_results = state.get("sni_exact_results")

    # 如果精确匹配找到结果，直接跳到综合步骤
    if exact_results and exact_results.get("match_count", 0) > 0:
        logger.info("Found exact match → skip to synthesize")
        return "synthesize"

    # 否则，继续向量搜索
    logger.info("No exact match → proceed to vector search")
    return "vector_search"
```

### 3. 执行工作流

```python
# 同步执行
result = graph.invoke(initial_state)

# 异步执行
result = await graph.ainvoke(initial_state)

# 流式执行（获取中间状态）
async for state in graph.astream(initial_state):
    print(f"Current state: {state}")
```

---

## 使用示例

### 完整示例

```python
import asyncio
from src.graph.builder import create_sni_graph

async def main():
    # 1. 创建工作流图
    graph = create_sni_graph()

    # 2. 准备初始状态
    initial_state = {
        "messages": [],
        "query": "tclandroidicsapp.accu-weather.com",
        "sni_exact_results": None,
        "sni_vector_results": None,
        "final_answer": None,
        "locale": "en-US",
        # ... 其他字段初始化为 None
    }

    # 3. 执行工作流
    result = await graph.ainvoke(initial_state)

    # 4. 查看结果
    print(f"Query: {result['query']}")
    print(f"Final Answer: {result['final_answer']}")

    # 查看中间结果
    if result.get('round1_queries'):
        print(f"Round 1 Queries: {result['round1_queries']}")
    if result.get('round2_keywords'):
        print(f"Round 2 Keywords: {result['round2_keywords']}")

asyncio.run(main())
```

### API 服务器集成

```python
# src/api_server.py
from fastapi import FastAPI
from src.graph.builder import create_sni_graph

app = FastAPI()
graph = create_sni_graph()

@app.post("/search")
async def search_sni(query: str, locale: str = "en-US"):
    initial_state = {
        "query": query,
        "locale": locale,
        # ... 初始化其他字段
    }

    result = await graph.ainvoke(initial_state)

    return {
        "query": result["query"],
        "answer": result["final_answer"],
        "sources": {
            "exact_match": result.get("sni_exact_results"),
            "vector_search": result.get("sni_vector_results"),
            "web_searches": {
                "round1": result.get("round1_results"),
                "round2": result.get("round2_results"),
                "final": result.get("final_search_result")
            }
        }
    }
```

---

## 关键特性

### 1. 多 LLM 提供商支持

```python
# 支持 Claude
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=your-key
CLAUDE_MODEL=claude-3-opus-20240229

# 支持 OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4-turbo-preview
```

### 2. 并发控制

使用 `asyncio.Semaphore` 控制并行搜索的并发数：

```python
semaphore = asyncio.Semaphore(4)  # 最多4个并发请求

async def search_with_limit(query: str):
    async with semaphore:
        return await web_search_tool.ainvoke(query)
```

### 3. Prompt 模板系统

基于 Jinja2 的多语言 prompt 模板：

```python
# 自动选择语言版本
prompt = apply_prompt_variables(
    "keyword_extraction",
    variables={"query": "example.com"},
    locale="zh-CN"  # 优先使用 keyword_extraction.zh_CN.md
)
```

### 4. 可观测性

集成 LangSmith 进行调试和监控：

```python
# .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=sni-recognition
LANGCHAIN_API_KEY=your-langsmith-key
```

### 5. 错误处理

每个节点都有完善的错误处理：

```python
def some_node(self, state: SNIAgentState) -> Dict[str, Any]:
    try:
        # 业务逻辑
        result = risky_operation()
        return {"result": result}
    except Exception as e:
        logger.error(f"Node failed: {e}")
        # 返回空结果，允许工作流继续
        return {"result": None}
```

### 6. 状态可视化

可以生成 Mermaid 图表：

```python
from src.graph.builder import create_sni_graph, visualize_graph

graph = create_sni_graph()
mermaid_diagram = visualize_graph(graph)
print(mermaid_diagram)
```

---

## 总结

### LangGraph 的优势

1. **清晰的工作流结构**: 图结构使复杂流程易于理解
2. **状态管理自动化**: 无需手动传递数据
3. **灵活的控制流**: 支持条件分支、循环等
4. **异步原生支持**: 轻松实现并行处理
5. **可观测性**: 便于调试和监控

### 项目亮点

- 多轮迭代搜索策略，提高查询准确性
- 100% Python 代码控制流程，避免 LLM 决策的不确定性
- 并行搜索能力，提升执行效率
- 模块化设计，易于扩展和维护
- 多语言支持，灵活的 prompt 管理

### 扩展方向

1. 添加更多搜索引擎支持
2. 实现搜索结果缓存机制
3. 集成更多数据源（如证书透明度日志）
4. 添加实时流式输出
5. 实现工作流的动态调整

---

## 参考资源

- [LangGraph 官方文档](https://python.langchain.com/docs/langgraph)
- [LangChain 文档](https://python.langchain.com/)
- [项目 GitHub](https://github.com/your-repo/sni-search)
