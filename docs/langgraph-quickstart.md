# LangGraph 快速入门指南

## 5 分钟快速理解 LangGraph

### 1. 核心概念

```python
from langgraph.graph import StateGraph, END

# 状态：节点间共享的数据
class MyState(TypedDict):
    input: str
    output: str

# 节点：执行具体任务的函数
def process_node(state: MyState) -> Dict:
    result = do_something(state["input"])
    return {"output": result}

# 图：组织节点的流程
workflow = StateGraph(MyState)
workflow.add_node("process", process_node)
workflow.set_entry_point("process")
workflow.add_edge("process", END)

# 编译并执行
graph = workflow.compile()
result = graph.invoke({"input": "test"})
```

### 2. 本项目的 LangGraph 应用

#### 状态定义 (src/graph/state.py)
```python
class SNIAgentState(TypedDict):
    query: str                  # 输入
    sni_exact_results: Optional[List]
    sni_vector_results: Optional[List]
    final_answer: Optional[str] # 输出
    # ... 更多中间状态
```

#### 节点实现 (src/graph/nodes.py)
```python
class SNIWorkflowNodes:
    def sni_exact_query_node(self, state):
        """查询数据库"""
        results = self.tools.search(state["query"])
        return {"sni_exact_results": results}

    def synthesize_node(self, state):
        """综合结果"""
        answer = self.llm.invoke(state["query"])
        return {"final_answer": answer}
```

#### 构建工作流 (src/graph/builder.py)
```python
def create_sni_graph():
    workflow = StateGraph(SNIAgentState)

    # 添加节点
    workflow.add_node("exact_query", nodes.sni_exact_query_node)
    workflow.add_node("vector_search", nodes.sni_vector_query_node)
    workflow.add_node("synthesize", nodes.synthesize_node)

    # 定义流程
    workflow.set_entry_point("exact_query")
    workflow.add_edge("exact_query", "vector_search")
    workflow.add_edge("vector_search", "synthesize")
    workflow.add_edge("synthesize", END)

    return workflow.compile()
```

### 3. 关键特性

#### ✅ 条件分支
```python
def should_web_search(state):
    if state["exact_results"]:
        return "synthesize"  # 跳过搜索
    return "web_search"      # 执行搜索

workflow.add_conditional_edges(
    "exact_query",
    should_web_search,
    {
        "web_search": "web_search",
        "synthesize": "synthesize"
    }
)
```

#### ✅ 并行执行
```python
async def parallel_search_node(state):
    queries = state["round1_queries"]  # 4个查询

    # 并行执行
    results = await asyncio.gather(*[
        search(q) for q in queries
    ])

    return {"round1_results": results}
```

#### ✅ LLM 集成
```python
def llm_node(state):
    prompt = f"Analyze: {state['query']}"
    response = self.llm.invoke([
        {"role": "user", "content": prompt}
    ])
    return {"analysis": response.content}
```

### 4. 完整工作流示例

```python
import asyncio
from src.graph.builder import create_sni_graph

async def main():
    # 创建图
    graph = create_sni_graph()

    # 准备输入
    initial_state = {
        "query": "example.com",
        "locale": "en-US"
        # 其他字段自动初始化
    }

    # 执行
    result = await graph.ainvoke(initial_state)

    # 输出
    print(result["final_answer"])

asyncio.run(main())
```

### 5. 调试技巧

#### 查看执行流程
```python
async for state in graph.astream(initial_state):
    print(f"Current node: {state}")
```

#### 可视化图结构
```python
from src.graph.builder import visualize_graph

mermaid = visualize_graph(graph)
print(mermaid)  # 生成流程图
```

#### 启用 LangSmith 追踪
```bash
# .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=my-project
LANGCHAIN_API_KEY=your-key
```

### 6. 常见模式

#### 模式 1: 数据查询 → LLM 处理 → 输出
```
查询节点 → 提取节点 → 综合节点
```

#### 模式 2: 多轮迭代
```
初始查询 → Round1 → Round2 → 最终查询 → 综合
```

#### 模式 3: 条件分支
```
查询 → [有结果？] → 是：直接输出
              ↓
              否：深度搜索 → 输出
```

### 7. 最佳实践

1. **状态最小化**: 只在状态中存储必要数据
2. **节点单一职责**: 每个节点只做一件事
3. **错误处理**: 每个节点都要有 try-except
4. **日志记录**: 记录关键步骤便于调试
5. **纯函数决策**: 条件分支用纯 Python 函数

### 8. 扩展示例

#### 添加新节点
```python
def my_new_node(self, state: SNIAgentState):
    """新功能节点"""
    # 处理逻辑
    result = process_data(state["query"])

    # 返回状态更新
    return {"my_new_field": result}
```

#### 集成到工作流
```python
# 在 builder.py 中
workflow.add_node("my_node", nodes.my_new_node)
workflow.add_edge("previous_node", "my_node")
workflow.add_edge("my_node", "next_node")
```

### 9. 性能优化

```python
# 并发控制
semaphore = asyncio.Semaphore(4)

async def rate_limited_search(query):
    async with semaphore:
        return await search_api(query)

# 结果缓存
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query):
    return expensive_search(query)
```

### 10. 故障排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 状态未更新 | 节点未返回字典 | 检查返回值格式 |
| 流程卡住 | 缺少边或END | 检查边的连接 |
| 类型错误 | 状态类型不匹配 | 检查 TypedDict 定义 |
| LLM 超时 | 请求过大 | 增加 timeout 参数 |

---

## 下一步

- 阅读完整文档: [langgraph-architecture.md](./langgraph-architecture.md)
- 查看示例代码: `demo/test_multi_round_search.py`
- 尝试修改工作流: `src/graph/builder.py`
- LangGraph 官方教程: https://python.langchain.com/docs/langgraph
