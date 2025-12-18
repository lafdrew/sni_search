# SNI识别系统 - LangGraph框架方案

## 1. 项目概述

### 1.1 设计理念
使用**LangGraph**框架构建智能SNI识别系统，通过状态图（StateGraph）管理查询流程，实现：
- 状态化的多轮对话
- 智能的工具选择和编排
- 条件路由和错误处理
- 人机协同的可控流程

### 1.2 LangGraph核心概念

```
┌─────────────────────────────────────────────────────────────┐
│                    StateGraph 状态图                         │
│                                                              │
│  ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐             │
│  │ 节点1 │───▶│ 节点2 │───▶│ 节点3 │───▶│ 结束 │             │
│  └──────┘    └──────┘    └──────┘    └──────┘             │
│      │           │                                          │
│      └───────────┘ (条件边)                                 │
│                                                              │
│  State: 在节点间传递的状态对象                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. 系统架构

### 2.1 LangGraph流程图

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ 理解查询节点  │ (LLM分析意图)
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │ 路由决策节点  │ (条件路由)
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ 精确查询工具  │   │ 向量搜索工具  │   │ 域名查询工具  │
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ 结果汇总节点  │
                    └──────┬──────┘
                           │
                    ┌──────┴──────┐
                    │  需要更多?   │ (条件判断)
                    └──────┬──────┘
                      Yes  │  No
                    ┌──────┴──────┐
                    │              ▼
                    │      ┌─────────────┐
                    │      │ 生成答案节点 │
                    │      └──────┬──────┘
                    │              │
                    └──────────────┤
                                   ▼
                            ┌─────────────┐
                            │     END     │
                            └─────────────┘
```

### 2.2 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 框架 | LangGraph | 0.2+ |
| LLM | Claude / GPT-4 | - |
| 向量DB | Qdrant | latest |
| Embedding | sentence-transformers | - |
| 状态管理 | TypedDict | - |
| 可视化 | LangGraph Studio | - |

---

## 3. 核心代码实现

### 3.1 状态定义

```python
from typing import TypedDict, List, Dict, Optional, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import operator

class SNIGraphState(TypedDict):
    """SNI查询流程的状态"""
    # 输入
    query: str                              # 用户查询

    # 中间状态
    query_type: Optional[str]               # 查询类型: exact, vector, domain, batch
    intent: Optional[str]                   # 用户意图
    extracted_entities: Optional[Dict]      # 提取的实体(SNI名称等)

    # 工具调用
    tool_calls: List[Dict]                  # 已执行的工具调用
    tool_results: List[Dict]                # 工具返回结果

    # 输出
    answer: Optional[str]                   # 最终答案
    need_more_info: bool                    # 是否需要更多信息

    # 元数据
    messages: Annotated[List[BaseMessage], operator.add]  # 消息历史
    step_count: int                         # 步骤计数
    error: Optional[str]                    # 错误信息
```

### 3.2 工具定义

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from langchain_core.tools import tool

class SNITools:
    """SNI查询工具集"""

    def __init__(self, qdrant_url: str = "http://localhost:6333"):
        self.client = QdrantClient(url=qdrant_url)
        self.model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        self.collection_name = "sni_domain_mapping"

    @tool
    def search_sni_exact(self, sni: str) -> Dict:
        """
        精确匹配SNI名称

        Args:
            sni: 完整的SNI名称

        Returns:
            SNI详细信息或None
        """
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[FieldCondition(key="sni", match=MatchValue(value=sni))]
            ),
            limit=1,
            with_payload=True
        )

        if not results[0]:
            return {"found": False, "sni": sni}

        point = results[0][0]
        return {
            "found": True,
            "sni": point.payload.get('sni'),
            "domain": point.payload.get('domain'),
            "all_related_snis": point.payload.get('all_snis', []),
            "protocols": point.payload.get('alpn_protocols', []),
            "total_count": point.payload.get('total_count')
        }

    @tool
    def search_sni_vector(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        向量相似度搜索SNI

        Args:
            query: 搜索关键词
            top_k: 返回结果数量

        Returns:
            相似的SNI列表
        """
        query_vector = self.model.encode(query).tolist()

        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k,
            score_threshold=0.7,
            with_payload=True
        )

        return [
            {
                "sni": hit.payload.get('sni'),
                "domain": hit.payload.get('domain'),
                "score": round(hit.score, 3),
                "protocols": hit.payload.get('alpn_protocols', [])
            }
            for hit in results
        ]

    @tool
    def search_by_domain(self, domain: str, limit: int = 20) -> List[Dict]:
        """
        按域名查询所有SNI

        Args:
            domain: 主域名
            limit: 返回数量限制

        Returns:
            该域名下所有SNI
        """
        results = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[FieldCondition(key="domain", match=MatchValue(value=domain))]
            ),
            limit=limit,
            with_payload=True
        )

        seen = set()
        unique_results = []
        for point in results[0]:
            sni = point.payload.get('sni')
            if sni not in seen:
                seen.add(sni)
                unique_results.append({
                    "sni": sni,
                    "domain": point.payload.get('domain'),
                    "protocols": point.payload.get('alpn_protocols', [])
                })

        return unique_results

    def get_tools(self):
        """获取所有工具"""
        return [
            self.search_sni_exact,
            self.search_sni_vector,
            self.search_by_domain
        ]
```

### 3.3 节点实现

```python
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

class SNIGraphNodes:
    """LangGraph节点定义"""

    def __init__(self, llm, tools: SNITools):
        self.llm = llm
        self.tools = tools
        self.llm_with_tools = llm.bind_tools(tools.get_tools())

    def understand_query(self, state: SNIGraphState) -> SNIGraphState:
        """节点1: 理解查询意图"""
        query = state["query"]

        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是SNI识别助手。分析用户查询，提取：
1. query_type: exact(精确查询) | vector(模糊搜索) | domain(域名查询) | batch(批量)
2. intent: 用户意图描述
3. entities: 提取的SNI名称或域名

示例：
- "www.google.com是什么" → exact, 查询SNI信息, ["www.google.com"]
- "google有哪些SNI" → domain, 查询域名SNI列表, ["google.com"]
- "类似google的网站" → vector, 模糊搜索, ["google"]
"""),
            ("human", "{query}")
        ])

        response = self.llm.invoke(prompt.format_messages(query=query))

        # 解析LLM响应（简化处理，实际应该用structured output）
        content = response.content.lower()

        if "exact" in content or "精确" in content:
            query_type = "exact"
        elif "domain" in content or "域名" in content:
            query_type = "domain"
        elif "vector" in content or "模糊" in content:
            query_type = "vector"
        else:
            query_type = "exact"  # 默认

        return {
            **state,
            "query_type": query_type,
            "intent": content,
            "step_count": state.get("step_count", 0) + 1,
            "messages": [HumanMessage(content=query)]
        }

    def route_query(self, state: SNIGraphState) -> str:
        """路由节点: 决定调用哪个工具"""
        query_type = state.get("query_type", "exact")

        # 根据查询类型路由到不同的工具节点
        if query_type == "exact":
            return "exact_search"
        elif query_type == "vector":
            return "vector_search"
        elif query_type == "domain":
            return "domain_search"
        else:
            return "exact_search"  # 默认

    def exact_search_node(self, state: SNIGraphState) -> SNIGraphState:
        """节点: 精确查询"""
        query = state["query"]

        # 提取SNI名称（简化版，实际应该更智能）
        import re
        sni_pattern = r'\b[a-zA-Z0-9][-a-zA-Z0-9]{0,62}(\.[a-zA-Z0-9][-a-zA-Z0-9]{0,62})+\.?\b'
        matches = re.findall(sni_pattern, query)
        sni = matches[0][0] if matches else query

        # 调用工具
        result = self.tools.search_sni_exact.invoke({"sni": sni})

        return {
            **state,
            "tool_calls": state.get("tool_calls", []) + [
                {"tool": "search_sni_exact", "input": sni}
            ],
            "tool_results": state.get("tool_results", []) + [result],
            "step_count": state.get("step_count", 0) + 1
        }

    def vector_search_node(self, state: SNIGraphState) -> SNIGraphState:
        """节点: 向量搜索"""
        query = state["query"]

        result = self.tools.search_sni_vector.invoke({"query": query, "top_k": 5})

        return {
            **state,
            "tool_calls": state.get("tool_calls", []) + [
                {"tool": "search_sni_vector", "input": query}
            ],
            "tool_results": state.get("tool_results", []) + [result],
            "step_count": state.get("step_count", 0) + 1
        }

    def domain_search_node(self, state: SNIGraphState) -> SNIGraphState:
        """节点: 域名查询"""
        query = state["query"]

        # 提取域名
        import re
        domain_pattern = r'\b([a-zA-Z0-9][-a-zA-Z0-9]{0,62}\.)+[a-zA-Z]{2,}\b'
        matches = re.findall(domain_pattern, query)
        domain = matches[0] if matches else "google.com"

        result = self.tools.search_by_domain.invoke({"domain": domain, "limit": 20})

        return {
            **state,
            "tool_calls": state.get("tool_calls", []) + [
                {"tool": "search_by_domain", "input": domain}
            ],
            "tool_results": state.get("tool_results", []) + [result],
            "step_count": state.get("step_count", 0) + 1
        }

    def aggregate_results(self, state: SNIGraphState) -> SNIGraphState:
        """节点: 汇总结果"""
        tool_results = state.get("tool_results", [])

        # 检查是否需要更多信息
        need_more = False
        if not tool_results or all(
            (isinstance(r, dict) and not r.get("found", True)) or
            (isinstance(r, list) and len(r) == 0)
            for r in tool_results
        ):
            need_more = True

        return {
            **state,
            "need_more_info": need_more,
            "step_count": state.get("step_count", 0) + 1
        }

    def should_continue(self, state: SNIGraphState) -> str:
        """条件判断: 是否需要继续查询"""
        if state.get("need_more_info") and state.get("step_count", 0) < 3:
            # 如果没找到结果，尝试其他方法
            return "vector_search"
        else:
            return "generate_answer"

    def generate_answer(self, state: SNIGraphState) -> SNIGraphState:
        """节点: 生成最终答案"""
        query = state["query"]
        tool_results = state.get("tool_results", [])

        # 构建上下文
        context = "查询结果：\n"
        for i, result in enumerate(tool_results, 1):
            if isinstance(result, dict) and result.get("found"):
                context += f"\n{i}. SNI: {result.get('sni')}\n"
                context += f"   域名: {result.get('domain')}\n"
                context += f"   协议: {', '.join(result.get('protocols', []))}\n"
            elif isinstance(result, list):
                context += f"\n找到 {len(result)} 个相关SNI：\n"
                for item in result[:5]:
                    context += f"  - {item.get('sni')} (域名: {item.get('domain')})\n"

        if not tool_results or all(
            (isinstance(r, dict) and not r.get("found", True)) or
            (isinstance(r, list) and len(r) == 0)
            for r in tool_results
        ):
            context = "未找到相关SNI信息"

        # 生成答案
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是SNI识别专家。基于查询结果，用简洁专业的语言回答用户问题。
要求：
1. 明确指出SNI对应的网站/服务
2. 说明主要用途
3. 保持简洁，不超过150字
"""),
            ("human", "用户问题: {query}\n\n{context}\n\n请回答：")
        ])

        response = self.llm.invoke(
            prompt.format_messages(query=query, context=context)
        )

        return {
            **state,
            "answer": response.content,
            "messages": state.get("messages", []) + [AIMessage(content=response.content)],
            "step_count": state.get("step_count", 0) + 1
        }
```

### 3.4 构建StateGraph

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

def create_sni_graph():
    """创建SNI识别StateGraph"""

    # 初始化
    llm = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        temperature=0
    )
    tools = SNITools(qdrant_url="http://localhost:6333")
    nodes = SNIGraphNodes(llm, tools)

    # 创建StateGraph
    workflow = StateGraph(SNIGraphState)

    # 添加节点
    workflow.add_node("understand", nodes.understand_query)
    workflow.add_node("exact_search", nodes.exact_search_node)
    workflow.add_node("vector_search", nodes.vector_search_node)
    workflow.add_node("domain_search", nodes.domain_search_node)
    workflow.add_node("aggregate", nodes.aggregate_results)
    workflow.add_node("generate", nodes.generate_answer)

    # 设置入口点
    workflow.set_entry_point("understand")

    # 添加边
    # understand -> 条件路由 -> 具体搜索节点
    workflow.add_conditional_edges(
        "understand",
        nodes.route_query,
        {
            "exact_search": "exact_search",
            "vector_search": "vector_search",
            "domain_search": "domain_search"
        }
    )

    # 所有搜索节点 -> aggregate
    workflow.add_edge("exact_search", "aggregate")
    workflow.add_edge("vector_search", "aggregate")
    workflow.add_edge("domain_search", "aggregate")

    # aggregate -> 条件判断
    workflow.add_conditional_edges(
        "aggregate",
        nodes.should_continue,
        {
            "vector_search": "vector_search",  # 如果需要更多信息，fallback到向量搜索
            "generate_answer": "generate"
        }
    )

    # generate -> END
    workflow.add_edge("generate", END)

    # 编译图（带检查点）
    memory = MemorySaver()
    app = workflow.compile(checkpointer=memory)

    return app

# 使用示例
if __name__ == "__main__":
    app = create_sni_graph()

    # 单次查询
    result = app.invoke({
        "query": "www.google.com是什么网站？",
        "step_count": 0,
        "tool_calls": [],
        "tool_results": [],
        "need_more_info": False,
        "messages": []
    })

    print(f"答案: {result['answer']}")
    print(f"执行步骤: {result['step_count']}")
    print(f"工具调用: {result['tool_calls']}")
```

---

## 4. 流式响应和可视化

### 4.1 流式执行

```python
async def stream_sni_query(query: str):
    """流式执行查询"""
    app = create_sni_graph()

    config = {"configurable": {"thread_id": "user-session-1"}}

    async for event in app.astream({
        "query": query,
        "step_count": 0,
        "tool_calls": [],
        "tool_results": [],
        "need_more_info": False,
        "messages": []
    }, config=config):
        # 输出每个节点的执行结果
        for node_name, node_output in event.items():
            print(f"\n--- {node_name} ---")
            if "answer" in node_output:
                print(f"答案: {node_output['answer']}")
            if "tool_calls" in node_output and node_output["tool_calls"]:
                print(f"工具调用: {node_output['tool_calls'][-1]}")

# 异步运行
import asyncio
asyncio.run(stream_sni_query("www.google.com是什么？"))
```

### 4.2 图可视化

```python
from IPython.display import Image, display

def visualize_graph():
    """可视化StateGraph"""
    app = create_sni_graph()

    # 生成Mermaid图
    mermaid_png = app.get_graph().draw_mermaid_png()

    # 保存为文件
    with open("sni_graph.png", "wb") as f:
        f.write(mermaid_png)

    print("图已保存到 sni_graph.png")

    # 如果在Jupyter中，可以直接显示
    # display(Image(mermaid_png))

visualize_graph()
```

---

## 5. FastAPI集成

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid

app_api = FastAPI(title="SNI识别服务 - LangGraph版")

# 全局StateGraph实例
sni_graph = create_sni_graph()

# 会话存储
sessions = {}

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    session_id: str
    steps: int
    tool_calls: list

@app_api.post("/api/query", response_model=QueryResponse)
async def query_sni(request: QueryRequest):
    """查询SNI"""
    session_id = request.session_id or str(uuid.uuid4())

    config = {"configurable": {"thread_id": session_id}}

    try:
        result = sni_graph.invoke({
            "query": request.query,
            "step_count": 0,
            "tool_calls": [],
            "tool_results": [],
            "need_more_info": False,
            "messages": []
        }, config=config)

        return QueryResponse(
            answer=result["answer"],
            session_id=session_id,
            steps=result["step_count"],
            tool_calls=result.get("tool_calls", [])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app_api.get("/api/graph/visualize")
async def get_graph_visualization():
    """获取图可视化"""
    mermaid_code = sni_graph.get_graph().draw_mermaid()
    return {"mermaid": mermaid_code}

# 运行: uvicorn api_server:app_api --reload --port 8000
```

---

## 6. 高级特性

### 6.1 人在环路（Human-in-the-Loop）

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode

def create_hitl_graph():
    """创建支持人工干预的图"""
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
    tools = SNITools()

    workflow = StateGraph(SNIGraphState)

    # ... 添加节点 ...

    # 添加人工审核节点
    def human_approval(state: SNIGraphState) -> SNIGraphState:
        """需要人工批准"""
        tool_results = state.get("tool_results", [])

        # 如果结果不确定，暂停等待人工确认
        if state.get("need_more_info"):
            # 这里会暂停执行，等待外部输入
            return {**state, "need_approval": True}

        return state

    workflow.add_node("human_review", human_approval)

    # aggregate -> human_review -> generate
    workflow.add_edge("aggregate", "human_review")
    workflow.add_edge("human_review", "generate")

    # 使用带检查点的编译
    memory = MemorySaver()
    app = workflow.compile(
        checkpointer=memory,
        interrupt_before=["human_review"]  # 在此节点前中断
    )

    return app

# 使用
app = create_hitl_graph()
config = {"configurable": {"thread_id": "session-1"}}

# 第一步：执行到人工审核点
result = app.invoke(initial_state, config=config)

# 人工审核后继续
result = app.invoke(None, config=config)  # 传入None继续执行
```

### 6.2 子图（Subgraph）

```python
def create_batch_search_subgraph():
    """批量搜索子图"""
    subgraph = StateGraph(SNIGraphState)

    def batch_search(state: SNIGraphState) -> SNIGraphState:
        """批量搜索逻辑"""
        # 提取多个SNI
        snis = state.get("extracted_entities", {}).get("sni_list", [])

        results = []
        tools = SNITools()
        for sni in snis:
            result = tools.search_sni_exact.invoke({"sni": sni})
            results.append(result)

        return {
            **state,
            "tool_results": results
        }

    subgraph.add_node("batch", batch_search)
    subgraph.set_entry_point("batch")
    subgraph.add_edge("batch", END)

    return subgraph.compile()

# 在主图中使用子图
def create_main_graph_with_subgraph():
    workflow = StateGraph(SNIGraphState)

    batch_graph = create_batch_search_subgraph()

    # 添加子图作为节点
    workflow.add_node("batch_search", batch_graph)

    # ... 其他节点 ...

    return workflow.compile()
```

### 6.3 并行执行

```python
from langgraph.graph import START

def create_parallel_graph():
    """创建并行执行的图"""
    workflow = StateGraph(SNIGraphState)

    # 添加多个并行节点
    workflow.add_node("search_exact", exact_search_node)
    workflow.add_node("search_vector", vector_search_node)
    workflow.add_node("search_domain", domain_search_node)

    # 从START并行启动多个搜索
    workflow.add_edge(START, "search_exact")
    workflow.add_edge(START, "search_vector")
    workflow.add_edge(START, "search_domain")

    # 所有搜索完成后汇总
    workflow.add_node("merge_results", merge_results_node)
    workflow.add_edge("search_exact", "merge_results")
    workflow.add_edge("search_vector", "merge_results")
    workflow.add_edge("search_domain", "merge_results")

    workflow.add_edge("merge_results", END)

    return workflow.compile()
```

---

## 7. 监控和调试

### 7.1 LangSmith集成

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "sni-recognition"
os.environ["LANGCHAIN_API_KEY"] = "your-api-key"

# 现在所有执行都会被追踪到LangSmith
app = create_sni_graph()
result = app.invoke(initial_state)
```

### 7.2 自定义回调

```python
from langchain_core.callbacks import BaseCallbackHandler

class SNICallbackHandler(BaseCallbackHandler):
    """自定义回调处理器"""

    def on_tool_start(self, serialized, input_str, **kwargs):
        """工具开始执行"""
        print(f"🔧 工具调用开始: {serialized.get('name')}")
        print(f"   输入: {input_str}")

    def on_tool_end(self, output, **kwargs):
        """工具执行结束"""
        print(f"✅ 工具调用完成")
        print(f"   输出: {output[:100]}...")

    def on_llm_start(self, serialized, prompts, **kwargs):
        """LLM开始执行"""
        print(f"🤖 LLM调用开始")

    def on_llm_end(self, response, **kwargs):
        """LLM执行结束"""
        print(f"✅ LLM调用完成")

# 使用回调
app = create_sni_graph()
result = app.invoke(
    initial_state,
    config={"callbacks": [SNICallbackHandler()]}
)
```

### 7.3 状态持久化

```python
from langgraph.checkpoint.sqlite import SqliteSaver

def create_persistent_graph():
    """创建带持久化的图"""
    # 使用SQLite持久化
    with SqliteSaver.from_conn_string("checkpoints.db") as saver:
        app = workflow.compile(checkpointer=saver)

        # 执行
        config = {"configurable": {"thread_id": "session-123"}}
        result = app.invoke(initial_state, config=config)

        # 稍后可以从同一个thread_id恢复状态
        result = app.invoke(None, config=config)

    return app
```

---

## 8. 测试

### 8.1 单元测试

```python
import pytest
from langgraph.graph import END

def test_understand_query_node():
    """测试查询理解节点"""
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
    tools = SNITools()
    nodes = SNIGraphNodes(llm, tools)

    state = {
        "query": "www.google.com是什么网站？",
        "step_count": 0,
        "tool_calls": [],
        "tool_results": [],
        "messages": []
    }

    result = nodes.understand_query(state)

    assert result["query_type"] in ["exact", "vector", "domain"]
    assert result["step_count"] == 1
    assert len(result["messages"]) > 0

def test_exact_search_node():
    """测试精确搜索节点"""
    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022")
    tools = SNITools()
    nodes = SNIGraphNodes(llm, tools)

    state = {
        "query": "www.google.com",
        "query_type": "exact",
        "step_count": 0,
        "tool_calls": [],
        "tool_results": []
    }

    result = nodes.exact_search_node(state)

    assert len(result["tool_results"]) > 0
    assert result["tool_results"][0].get("found") is not None

def test_full_graph():
    """测试完整流程"""
    app = create_sni_graph()

    result = app.invoke({
        "query": "google.com是什么？",
        "step_count": 0,
        "tool_calls": [],
        "tool_results": [],
        "need_more_info": False,
        "messages": []
    })

    assert "answer" in result
    assert result["answer"] is not None
    assert result["step_count"] > 0
```

### 8.2 集成测试

```python
@pytest.mark.asyncio
async def test_stream_execution():
    """测试流式执行"""
    app = create_sni_graph()

    events = []
    async for event in app.astream({
        "query": "www.google.com",
        "step_count": 0,
        "tool_calls": [],
        "tool_results": [],
        "need_more_info": False,
        "messages": []
    }):
        events.append(event)

    assert len(events) > 0
    # 最后一个事件应该包含答案
    assert "answer" in events[-1][list(events[-1].keys())[0]]
```

---

## 9. 部署

### 9.1 Docker部署

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "api_server:app_api", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_storage:/qdrant/storage

  sni-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - QDRANT_URL=http://qdrant:6333
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    depends_on:
      - qdrant
    volumes:
      - ./checkpoints.db:/app/checkpoints.db
```

### 9.2 启动命令

```bash
# 1. 启动服务
docker-compose up -d

# 2. 导入数据
python import_data.py

# 3. 测试
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "www.google.com是什么？"}'
```

---

## 10. 项目结构

```
sni_search/
├── data/
│   └── result/results/           # JSON数据源
├── src/
│   ├── __init__.py
│   ├── config.py                 # 配置
│   ├── state.py                  # State定义
│   ├── tools.py                  # SNITools工具类
│   ├── nodes.py                  # 节点实现
│   ├── graph.py                  # StateGraph构建
│   ├── api_server.py             # FastAPI服务
│   └── import_data.py            # 数据导入
├── tests/
│   ├── test_nodes.py
│   ├── test_tools.py
│   └── test_graph.py
├── checkpoints.db                # 状态持久化
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

### requirements.txt

```txt
langgraph>=0.2.0
langchain>=0.3.0
langchain-anthropic>=0.2.0
langchain-core>=0.3.0
qdrant-client>=1.7.0
sentence-transformers>=2.2.0
fastapi>=0.104.0
uvicorn>=0.24.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0
```

---

## 11. LangGraph优势总结

### vs 传统Tool Calling

| 特性 | LangGraph | 传统Tool Calling |
|------|-----------|-----------------|
| 流程控制 | 显式图结构，可视化 | 隐式在LLM中 |
| 状态管理 | 内置状态传递 | 手动管理 |
| 条件路由 | 声明式conditional_edges | 需要编写if/else |
| 人工干预 | 原生支持interrupt | 需要自己实现 |
| 可观测性 | 每个节点可追踪 | 只能追踪整体 |
| 错误恢复 | 检查点机制 | 需要自己实现 |
| 并行执行 | 原生支持 | 需要异步编程 |

### 适用场景

✅ **适合LangGraph**:
- 复杂的多步骤工作流
- 需要条件分支的流程
- 需要人工干预的场景
- 需要状态持久化
- 需要并行执行多个工具

❌ **不适合LangGraph**:
- 简单的单次查询
- 不需要状态管理
- 流程完全由LLM决定

---

## 12. 总结

本方案使用LangGraph框架实现SNI识别系统，核心优势：

1. **清晰的流程控制**: 通过图结构明确定义查询流程
2. **智能路由**: 根据查询类型自动选择最优工具
3. **状态管理**: 内置状态传递和持久化
4. **可扩展性**: 易于添加新节点和工具
5. **可观测性**: 完整的执行追踪和调试

**下一步**:
1. 实现数据导入脚本
2. 完善节点实现
3. 添加更多工具
4. 部署和测试

---

**文档版本**: v3.0 - LangGraph版
**最后更新**: 2025-12-18
**参考**: LangGraph官方文档
