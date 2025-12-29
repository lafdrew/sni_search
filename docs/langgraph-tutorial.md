# LangGraph 完全指南

## 目录
- [什么是 LangGraph](#什么是-langgraph)
- [核心概念](#核心概念)
- [快速开始](#快速开始)
- [状态管理](#状态管理)
- [节点和边](#节点和边)
- [条件分支](#条件分支)
- [循环和递归](#循环和递归)
- [子图](#子图)
- [持久化](#持久化)
- [流式输出](#流式输出)
- [人机交互](#人机交互)
- [最佳实践](#最佳实践)
- [常见模式](#常见模式)

---

## 什么是 LangGraph

**LangGraph** 是 LangChain 生态系统中的一个库，用于构建有状态、多步骤的 AI Agent 应用。它通过图结构来组织复杂的工作流，使 Agent 的行为更加可控和可预测。

### 核心特点

- **图结构**: 使用有向图组织工作流
- **状态管理**: 自动管理节点间的数据传递
- **条件路由**: 支持基于条件的分支逻辑
- **循环支持**: 支持循环和递归结构
- **持久化**: 可以保存和恢复执行状态
- **流式输出**: 支持实时输出中间结果
- **人机交互**: 可以在执行过程中请求人工输入

### 为什么需要 LangGraph

传统的 LangChain Agent 使用 LLM 来决定下一步做什么，这带来了不确定性：

```python
# 传统 Agent: LLM 决定下一步
while not done:
    action = llm.decide_next_action()  # 不可预测
    result = execute(action)
```

LangGraph 让你用代码控制流程：

```python
# LangGraph: 代码控制流程
graph.add_edge("step1", "step2")      # 确定的流程
graph.add_conditional_edges(          # 条件分支
    "step2",
    decide_next,                       # 你的 Python 函数
    {"option_a": "step3a", "option_b": "step3b"}
)
```

---

## 核心概念

### 1. State（状态）

状态是在节点之间传递的数据结构，通常使用 `TypedDict` 定义：

```python
from typing import TypedDict, Annotated
from operator import add

class State(TypedDict):
    # 简单字段：每次覆盖
    messages: list
    counter: int

    # 使用 Annotated 自定义更新逻辑
    # add: 将新值添加到列表（而不是替换）
    items: Annotated[list, add]
```

### 2. Nodes（节点）

节点是执行具体任务的函数，接收状态并返回更新：

```python
def my_node(state: State) -> dict:
    """节点函数"""
    # 读取状态
    messages = state["messages"]

    # 执行任务
    result = do_something(messages)

    # 返回状态更新（只返回变化的字段）
    return {"counter": state["counter"] + 1}
```

### 3. Edges（边）

边连接节点，定义执行顺序：

```python
# 普通边：A → B
graph.add_edge("node_a", "node_b")

# 条件边：基于函数返回值选择下一个节点
graph.add_conditional_edges(
    "node_a",
    route_function,
    {"path1": "node_b", "path2": "node_c"}
)
```

### 4. Graph（图）

图是整个工作流的容器：

```python
from langgraph.graph import StateGraph, END

# 创建图
workflow = StateGraph(State)

# 添加节点
workflow.add_node("process", process_node)

# 设置入口
workflow.set_entry_point("process")

# 添加边
workflow.add_edge("process", END)

# 编译
app = workflow.compile()
```

---

## 快速开始

### 安装

```bash
pip install langgraph
```

### 最简单的例子

```python
from typing import TypedDict
from langgraph.graph import StateGraph, END

# 1. 定义状态
class State(TypedDict):
    input: str
    output: str

# 2. 定义节点
def process_node(state: State) -> dict:
    """处理输入"""
    text = state["input"]
    processed = text.upper()  # 简单处理：转大写
    return {"output": processed}

# 3. 构建图
workflow = StateGraph(State)
workflow.add_node("process", process_node)
workflow.set_entry_point("process")
workflow.add_edge("process", END)

# 4. 编译
app = workflow.compile()

# 5. 执行
result = app.invoke({"input": "hello world"})
print(result["output"])  # HELLO WORLD
```

### 带 LLM 的例子

```python
from typing import TypedDict
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# 状态
class State(TypedDict):
    question: str
    answer: str

# LLM
llm = ChatOpenAI(model="gpt-4")

# 节点
def answer_question(state: State) -> dict:
    """使用 LLM 回答问题"""
    question = state["question"]
    response = llm.invoke(f"请回答: {question}")
    return {"answer": response.content}

# 构建图
workflow = StateGraph(State)
workflow.add_node("answer", answer_question)
workflow.set_entry_point("answer")
workflow.add_edge("answer", END)

# 编译并执行
app = workflow.compile()
result = app.invoke({"question": "什么是 Python?"})
print(result["answer"])
```

---

## 状态管理

### 基本状态更新

状态更新是**增量式**的，只需返回变化的字段：

```python
def node1(state: State) -> dict:
    return {"field1": "new_value"}  # 只更新 field1

def node2(state: State) -> dict:
    return {
        "field1": "updated",
        "field2": "also_updated"
    }
```

### 使用 Annotated 自定义更新逻辑

```python
from typing import Annotated
from operator import add

class State(TypedDict):
    # 默认行为：替换
    name: str

    # 自定义行为：追加到列表
    messages: Annotated[list, add]

    # 自定义行为：合并字典
    metadata: Annotated[dict, lambda x, y: {**x, **y}]
```

使用示例：

```python
# 初始状态
initial = {
    "name": "Alice",
    "messages": ["Hi"],
    "metadata": {"key1": "value1"}
}

# 节点返回
def node(state):
    return {
        "name": "Bob",              # 替换
        "messages": ["Hello"],      # 追加 -> ["Hi", "Hello"]
        "metadata": {"key2": "v2"}  # 合并 -> {"key1": "value1", "key2": "v2"}
    }
```

### Reducer 函数

自定义更新逻辑：

```python
def merge_lists(existing: list, new: list) -> list:
    """合并列表并去重"""
    return list(set(existing + new))

class State(TypedDict):
    items: Annotated[list, merge_lists]
```

---

## 节点和边

### 节点类型

#### 1. 普通函数节点

```python
def my_node(state: State) -> dict:
    """最常见的节点类型"""
    return {"result": "value"}
```

#### 2. 异步节点

```python
async def async_node(state: State) -> dict:
    """异步操作"""
    result = await some_async_operation()
    return {"result": result}
```

#### 3. 生成器节点（流式输出）

```python
def streaming_node(state: State):
    """逐步返回结果"""
    for i in range(10):
        yield {"progress": i}
    yield {"done": True}
```

#### 4. 类方法节点

```python
class MyWorkflow:
    def __init__(self, llm):
        self.llm = llm

    def process_node(self, state: State) -> dict:
        """使用实例变量"""
        result = self.llm.invoke(state["input"])
        return {"output": result}

# 使用
workflow = MyWorkflow(llm)
graph.add_node("process", workflow.process_node)
```

### 边类型

#### 1. 普通边

确定的执行顺序：

```python
graph.add_edge("node_a", "node_b")
graph.add_edge("node_b", "node_c")
graph.add_edge("node_c", END)
```

#### 2. 条件边

基于函数返回值路由：

```python
def decide_next(state: State) -> str:
    """返回下一个节点的名称"""
    if state["score"] > 0.8:
        return "high_quality"
    elif state["score"] > 0.5:
        return "medium_quality"
    else:
        return "low_quality"

graph.add_conditional_edges(
    "evaluate",
    decide_next,
    {
        "high_quality": "process_high",
        "medium_quality": "process_medium",
        "low_quality": "process_low"
    }
)
```

#### 3. 动态边

运行时决定目标节点：

```python
def dynamic_route(state: State) -> list[str]:
    """返回多个节点名称"""
    targets = []
    if state["needs_search"]:
        targets.append("search")
    if state["needs_analysis"]:
        targets.append("analyze")
    return targets

graph.add_conditional_edges(
    "decision",
    dynamic_route
)
```

---

## 条件分支

### 简单条件

```python
from langgraph.graph import StateGraph, END

class State(TypedDict):
    score: float

def check_score(state: State) -> str:
    """条件判断"""
    if state["score"] >= 0.7:
        return "pass"
    else:
        return "fail"

workflow = StateGraph(State)
workflow.add_node("evaluate", evaluate_node)
workflow.add_node("pass_handler", pass_node)
workflow.add_node("fail_handler", fail_node)

workflow.set_entry_point("evaluate")
workflow.add_conditional_edges(
    "evaluate",
    check_score,
    {
        "pass": "pass_handler",
        "fail": "fail_handler"
    }
)
workflow.add_edge("pass_handler", END)
workflow.add_edge("fail_handler", END)
```

### 多路分支

```python
def complex_router(state: State) -> str:
    """多个条件"""
    if state["type"] == "A":
        return "handler_a"
    elif state["type"] == "B":
        return "handler_b"
    elif state["type"] == "C":
        return "handler_c"
    else:
        return "default_handler"

graph.add_conditional_edges(
    "input",
    complex_router,
    {
        "handler_a": "process_a",
        "handler_b": "process_b",
        "handler_c": "process_c",
        "default_handler": "process_default"
    }
)
```

### 并行分支

```python
def parallel_router(state: State) -> list[str]:
    """返回多个节点，并行执行"""
    return ["task1", "task2", "task3"]

graph.add_conditional_edges(
    "split",
    parallel_router
)
```

---

## 循环和递归

### 简单循环

```python
class State(TypedDict):
    count: int
    max_count: int

def increment(state: State) -> dict:
    """递增计数器"""
    return {"count": state["count"] + 1}

def should_continue(state: State) -> str:
    """检查是否继续循环"""
    if state["count"] < state["max_count"]:
        return "continue"
    else:
        return "stop"

workflow = StateGraph(State)
workflow.add_node("increment", increment)
workflow.set_entry_point("increment")

# 循环：根据条件回到自身或结束
workflow.add_conditional_edges(
    "increment",
    should_continue,
    {
        "continue": "increment",  # 回到自身
        "stop": END
    }
)
```

### Agent 循环模式

```python
class AgentState(TypedDict):
    messages: list
    iterations: int
    max_iterations: int

def agent_node(state: AgentState) -> dict:
    """Agent 执行一步"""
    # LLM 决定是否使用工具
    response = llm.invoke(state["messages"])

    return {
        "messages": state["messages"] + [response],
        "iterations": state["iterations"] + 1
    }

def should_continue(state: AgentState) -> str:
    """检查是否继续"""
    last_message = state["messages"][-1]

    # 如果 LLM 决定结束
    if "FINAL_ANSWER" in last_message.content:
        return "end"

    # 如果达到最大迭代次数
    if state["iterations"] >= state["max_iterations"]:
        return "end"

    # 继续循环
    return "continue"

workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "agent",
        "end": END
    }
)
```

---

## 子图

子图允许你将复杂工作流模块化：

### 创建子图

```python
from langgraph.graph import StateGraph, END

# 子图状态
class SubState(TypedDict):
    input: str
    output: str

# 子图节点
def sub_node1(state: SubState) -> dict:
    return {"output": state["input"].upper()}

# 构建子图
subgraph = StateGraph(SubState)
subgraph.add_node("process", sub_node1)
subgraph.set_entry_point("process")
subgraph.add_edge("process", END)
sub_app = subgraph.compile()
```

### 在主图中使用子图

```python
# 主图状态
class MainState(TypedDict):
    data: str
    result: str

def use_subgraph(state: MainState) -> dict:
    """调用子图"""
    # 准备子图输入
    sub_input = {"input": state["data"]}

    # 执行子图
    sub_result = sub_app.invoke(sub_input)

    # 返回结果
    return {"result": sub_result["output"]}

# 主图
main_graph = StateGraph(MainState)
main_graph.add_node("sub", use_subgraph)
main_graph.set_entry_point("sub")
main_graph.add_edge("sub", END)
```

---

## 持久化

LangGraph 支持保存和恢复执行状态：

### 使用 Checkpointer

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# 创建持久化后端
memory = SqliteSaver.from_conn_string(":memory:")

# 编译时传入
app = workflow.compile(checkpointer=memory)

# 使用 thread_id 标识会话
config = {"configurable": {"thread_id": "user-123"}}

# 第一次执行
result1 = app.invoke({"input": "hello"}, config)

# 稍后恢复同一会话
result2 = app.invoke({"input": "world"}, config)
```

### 保存到文件

```python
from langgraph.checkpoint.sqlite import SqliteSaver

# 持久化到文件
memory = SqliteSaver.from_conn_string("checkpoints.db")
app = workflow.compile(checkpointer=memory)

# 执行后，状态保存在 checkpoints.db
result = app.invoke({"input": "data"}, config={"configurable": {"thread_id": "1"}})

# 程序重启后，可以恢复
app2 = workflow.compile(checkpointer=SqliteSaver.from_conn_string("checkpoints.db"))
result2 = app2.invoke({"input": "more"}, config={"configurable": {"thread_id": "1"}})
```

### 检查点历史

```python
# 获取所有检查点
for checkpoint in app.get_state_history(config):
    print(f"Checkpoint: {checkpoint}")

# 从特定检查点恢复
specific_config = {
    "configurable": {
        "thread_id": "1",
        "checkpoint_id": "abc123"
    }
}
result = app.invoke({"input": "data"}, config=specific_config)
```

---

## 流式输出

### 流式执行

```python
# 同步流式
for state in app.stream({"input": "hello"}):
    print(state)

# 异步流式
async for state in app.astream({"input": "hello"}):
    print(state)
```

### 流式输出中间结果

```python
for output in app.stream({"input": "hello"}):
    # output 是 {node_name: node_result} 的字典
    for node_name, node_output in output.items():
        print(f"{node_name}: {node_output}")
```

### 流式 Token 输出（LLM）

```python
from langchain_openai import ChatOpenAI

# 使用流式 LLM
llm = ChatOpenAI(model="gpt-4", streaming=True)

def streaming_node(state: State):
    """节点支持流式输出"""
    for chunk in llm.stream(state["input"]):
        # 逐个 token 输出
        print(chunk.content, end="", flush=True)
        yield {"partial": chunk.content}

workflow.add_node("stream", streaming_node)
```

---

## 人机交互

### 中断执行等待输入

```python
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import ToolNode

# 使用 interrupt 参数
app = workflow.compile(
    checkpointer=SqliteSaver.from_conn_string(":memory:"),
    interrupt_before=["human_review"]  # 在此节点前中断
)

# 执行到 human_review 前会停止
config = {"configurable": {"thread_id": "1"}}
result = app.invoke({"input": "data"}, config)

# 此时 result 包含中间状态
print(result)

# 用户审核后继续
user_feedback = input("请输入反馈: ")
result = app.invoke(
    {"feedback": user_feedback},
    config
)
```

### 动态工具审批

```python
class State(TypedDict):
    messages: list
    pending_action: str

def agent_node(state: State) -> dict:
    """Agent 提出行动"""
    action = "delete_file"  # 危险操作
    return {"pending_action": action}

def human_approval(state: State) -> dict:
    """等待人工批准"""
    # 在实际应用中，这里会等待用户输入
    approved = input(f"批准操作 {state['pending_action']}? (y/n): ")
    return {"approved": approved == "y"}

workflow = StateGraph(State)
workflow.add_node("agent", agent_node)
workflow.add_node("approval", human_approval)
workflow.add_node("execute", execute_action)

workflow.set_entry_point("agent")
workflow.add_edge("agent", "approval")
workflow.add_conditional_edges(
    "approval",
    lambda s: "execute" if s.get("approved") else END
)
```

---

## 最佳实践

### 1. 状态设计

```python
# ✅ 好的状态设计
class State(TypedDict):
    # 明确的字段名
    user_query: str
    search_results: list
    final_answer: str

    # 使用 Optional 表示可选字段
    error: Optional[str]

    # 使用 Annotated 自定义行为
    logs: Annotated[list, add]

# ❌ 避免的设计
class BadState(TypedDict):
    data: dict  # 太泛化
    x: str      # 名称不清晰
```

### 2. 节点设计

```python
# ✅ 单一职责
def search_node(state: State) -> dict:
    """只负责搜索"""
    results = search_api(state["query"])
    return {"search_results": results}

def process_node(state: State) -> dict:
    """只负责处理结果"""
    processed = process(state["search_results"])
    return {"processed_data": processed}

# ❌ 职责过多
def bad_node(state: State) -> dict:
    """做太多事情"""
    results = search_api(state["query"])
    processed = process(results)
    answer = generate_answer(processed)
    return {"everything": answer}
```

### 3. 错误处理

```python
def robust_node(state: State) -> dict:
    """健壮的节点"""
    try:
        result = risky_operation(state["input"])
        return {"result": result, "error": None}
    except Exception as e:
        # 记录错误但不中断流程
        logger.error(f"Node failed: {e}")
        return {"result": None, "error": str(e)}

# 在路由中处理错误
def error_aware_router(state: State) -> str:
    if state.get("error"):
        return "error_handler"
    else:
        return "next_step"
```

### 4. 日志记录

```python
import logging

logger = logging.getLogger(__name__)

def well_logged_node(state: State) -> dict:
    """带详细日志的节点"""
    logger.info(f"Processing query: {state['query']}")

    try:
        result = process(state["query"])
        logger.info(f"Success: {len(result)} items")
        return {"result": result}
    except Exception as e:
        logger.error(f"Failed: {e}", exc_info=True)
        raise
```

### 5. 测试

```python
import unittest

class TestWorkflow(unittest.TestCase):
    def test_node(self):
        """测试单个节点"""
        state = {"input": "test"}
        result = my_node(state)
        self.assertEqual(result["output"], "expected")

    def test_workflow(self):
        """测试完整工作流"""
        app = workflow.compile()
        result = app.invoke({"input": "test"})
        self.assertIn("output", result)
```

---

## 常见模式

### 1. 线性流程

```python
workflow = StateGraph(State)
workflow.add_node("step1", step1)
workflow.add_node("step2", step2)
workflow.add_node("step3", step3)

workflow.set_entry_point("step1")
workflow.add_edge("step1", "step2")
workflow.add_edge("step2", "step3")
workflow.add_edge("step3", END)
```

可视化：
```
step1 → step2 → step3 → END
```

### 2. 分支-汇合模式

```python
workflow = StateGraph(State)
workflow.add_node("decision", decision_node)
workflow.add_node("path_a", process_a)
workflow.add_node("path_b", process_b)
workflow.add_node("merge", merge_node)

workflow.set_entry_point("decision")
workflow.add_conditional_edges(
    "decision",
    router,
    {"a": "path_a", "b": "path_b"}
)
workflow.add_edge("path_a", "merge")
workflow.add_edge("path_b", "merge")
workflow.add_edge("merge", END)
```

可视化：
```
decision → path_a ↘
                    merge → END
decision → path_b ↗
```

### 3. 并行执行模式

```python
def parallel_router(state: State) -> list[str]:
    return ["task1", "task2", "task3"]

workflow = StateGraph(State)
workflow.add_node("split", split_node)
workflow.add_node("task1", task1_node)
workflow.add_node("task2", task2_node)
workflow.add_node("task3", task3_node)
workflow.add_node("combine", combine_node)

workflow.set_entry_point("split")
workflow.add_conditional_edges("split", parallel_router)
workflow.add_edge("task1", "combine")
workflow.add_edge("task2", "combine")
workflow.add_edge("task3", "combine")
workflow.add_edge("combine", END)
```

可视化：
```
split → task1 ↘
split → task2 → combine → END
split → task3 ↗
```

### 4. 循环模式

```python
workflow = StateGraph(State)
workflow.add_node("process", process_node)
workflow.add_node("check", check_node)

workflow.set_entry_point("process")
workflow.add_edge("process", "check")
workflow.add_conditional_edges(
    "check",
    should_continue,
    {
        "continue": "process",  # 循环
        "done": END
    }
)
```

可视化：
```
process → check → [done] → END
    ↑        ↓
    └─[continue]
```

### 5. Agent + Tools 模式

```python
from langgraph.prebuilt import ToolNode, tools_condition

class AgentState(TypedDict):
    messages: list

# 工具节点（内置）
tools = [search_tool, calculator_tool]
tool_node = ToolNode(tools)

# Agent 节点
def agent(state: AgentState) -> dict:
    response = llm.invoke(state["messages"])
    return {"messages": [response]}

# 构建图
workflow = StateGraph(AgentState)
workflow.add_node("agent", agent)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent")
workflow.add_conditional_edges(
    "agent",
    tools_condition,  # 内置条件：检查是否需要工具
)
workflow.add_edge("tools", "agent")  # 工具执行后回到 agent
```

可视化：
```
agent → [需要工具] → tools → agent
  ↓
[完成] → END
```

### 6. Map-Reduce 模式

```python
class State(TypedDict):
    items: list
    results: Annotated[list, add]

def map_node(state: State) -> dict:
    """并行处理每个项目"""
    # 实际中这里会分发到多个节点
    results = [process_item(item) for item in state["items"]]
    return {"results": results}

def reduce_node(state: State) -> dict:
    """汇总结果"""
    final = aggregate(state["results"])
    return {"final": final}

workflow = StateGraph(State)
workflow.add_node("map", map_node)
workflow.add_node("reduce", reduce_node)
workflow.set_entry_point("map")
workflow.add_edge("map", "reduce")
workflow.add_edge("reduce", END)
```

### 7. 多阶段管道模式

```python
workflow = StateGraph(State)

# 阶段1: 数据收集
workflow.add_node("fetch_data", fetch_node)
workflow.add_node("validate_data", validate_node)

# 阶段2: 数据处理
workflow.add_node("clean_data", clean_node)
workflow.add_node("transform_data", transform_node)

# 阶段3: 数据分析
workflow.add_node("analyze", analyze_node)
workflow.add_node("summarize", summarize_node)

# 连接
workflow.set_entry_point("fetch_data")
workflow.add_edge("fetch_data", "validate_data")
workflow.add_edge("validate_data", "clean_data")
workflow.add_edge("clean_data", "transform_data")
workflow.add_edge("transform_data", "analyze")
workflow.add_edge("analyze", "summarize")
workflow.add_edge("summarize", END)
```

---

## 调试和可视化

### 可视化图结构

```python
from IPython.display import Image, display

# 生成图的可视化
try:
    display(Image(app.get_graph().draw_mermaid_png()))
except Exception:
    # 如果没有 graphviz，使用 mermaid
    print(app.get_graph().draw_mermaid())
```

### 打印图结构

```python
# 打印所有节点
print("Nodes:", app.get_graph().nodes)

# 打印所有边
print("Edges:", app.get_graph().edges)
```

### 调试执行

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 逐步查看状态
for i, state in enumerate(app.stream({"input": "test"})):
    print(f"\n=== Step {i} ===")
    print(state)
```

### 使用 LangSmith

```python
import os

# 设置 LangSmith
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "my-project"
os.environ["LANGCHAIN_API_KEY"] = "your-key"

# 执行后会自动上传到 LangSmith
result = app.invoke({"input": "test"})
```

---

## 高级主题

### 动态图构建

```python
def build_dynamic_graph(num_steps: int):
    """根据参数动态构建图"""
    workflow = StateGraph(State)

    for i in range(num_steps):
        workflow.add_node(f"step_{i}", lambda s: process(s, i))

    workflow.set_entry_point("step_0")
    for i in range(num_steps - 1):
        workflow.add_edge(f"step_{i}", f"step_{i+1}")
    workflow.add_edge(f"step_{num_steps-1}", END)

    return workflow.compile()
```

### 嵌套子图

```python
# 子图
sub1 = StateGraph(SubState)
sub1.add_node("process", sub_process)
sub1.set_entry_point("process")
sub1.add_edge("process", END)
sub1_app = sub1.compile()

# 主图调用子图
def use_subgraph(state: MainState) -> dict:
    result = sub1_app.invoke({"input": state["data"]})
    return {"sub_result": result}

main = StateGraph(MainState)
main.add_node("sub", use_subgraph)
```

### 自定义执行器

```python
from langgraph.pregel import Pregel

# 自定义执行逻辑
class CustomExecutor(Pregel):
    def invoke(self, input, config=None):
        # 自定义前置处理
        preprocessed = self.preprocess(input)

        # 执行
        result = super().invoke(preprocessed, config)

        # 自定义后置处理
        return self.postprocess(result)
```

---

## 性能优化

### 1. 并行执行

```python
import asyncio

# 使用异步节点
async def fast_node(state: State) -> dict:
    results = await asyncio.gather(
        async_task1(),
        async_task2(),
        async_task3()
    )
    return {"results": results}
```

### 2. 缓存

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_operation(input_data: str) -> str:
    """缓存昂贵操作的结果"""
    return complex_computation(input_data)

def node_with_cache(state: State) -> dict:
    result = expensive_operation(state["input"])
    return {"result": result}
```

### 3. 批处理

```python
def batch_node(state: State) -> dict:
    """批量处理多个项目"""
    items = state["items"]

    # 批量处理而不是逐个处理
    batch_size = 10
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        batch_results = process_batch(batch)
        results.extend(batch_results)

    return {"results": results}
```

---

## 参考资源

### 官方文档
- [LangGraph 官方文档](https://python.langchain.com/docs/langgraph)
- [LangChain 文档](https://python.langchain.com/)
- [API 参考](https://python.langchain.com/api_reference/langgraph/index.html)

### 示例和教程
- [LangGraph Examples](https://github.com/langchain-ai/langgraph/tree/main/examples)
- [LangChain Blog](https://blog.langchain.dev/)

### 社区
- [Discord](https://discord.gg/langchain)
- [GitHub Discussions](https://github.com/langchain-ai/langgraph/discussions)
- [Twitter](https://twitter.com/langchainai)

---

## 总结

LangGraph 的核心优势：

1. **可控性**: 用代码而不是 LLM 控制流程
2. **可维护性**: 图结构清晰易懂
3. **灵活性**: 支持各种复杂的流程模式
4. **可观测性**: 内置调试和追踪功能
5. **持久化**: 可以保存和恢复状态

适用场景：
- 多步骤的 Agent 工作流
- 需要条件分支的复杂流程
- 需要人机交互的应用
- 长时间运行的任务
- 需要可靠性的生产环境

开始使用 LangGraph，构建更可控、更可靠的 AI Agent 吧！
