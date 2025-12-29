# SNI Search 项目架构借鉴与改进方向

## 项目概述

**当前项目**：SNI Search - 基于 LangGraph 的多轮 SNI 识别系统
**参考项目**：
1. **Deer-Flow** - Bytedance 的 LangGraph 研究工作流框架
2. **GPT-Researcher** - 自主研究代理，生成综合报告

## 一、从 Deer-Flow 借鉴的核心设计

### 1.1 LangGraph 状态管理架构 ✓

**Deer-Flow 实现**：
```python
# deer-flow/src/graph/types.py
class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    current_plan: Optional[Plan]
    research_result: Optional[str]
    ...
```

**当前项目采用**：
```python
# src/graph/state.py
class SNIAgentState(TypedDict):
    messages: List[BaseMessage]
    query: str
    sni_exact_results: Optional[...]
    round1_queries: Optional[List[str]]
    round2_keywords: Optional[List[str]]
    ...
```

**借鉴点**：
- TypedDict 定义清晰的状态结构
- 消息历史管理
- 可选字段灵活支持不同阶段

### 1.2 多节点工作流编排 ✓

**Deer-Flow 实现**：
```python
# deer-flow/src/graph/builder.py
builder = StateGraph(State)
builder.add_node("coordinator", coordinator_node)
builder.add_node("planner", planner_node)
builder.add_node("researcher", researcher_node)
builder.add_conditional_edges("research_team", continue_to_running_research_team, [...])
```

**当前项目采用**：
```python
# src/graph/builder.py
workflow = StateGraph(SNIAgentState)
workflow.add_node("sni_exact_query", nodes.sni_exact_query_node)
workflow.add_node("vector_search", nodes.vector_search_node)
workflow.add_node("round1_planning", nodes.round1_planning_node)
workflow.add_conditional_edges("sni_exact_query", should_try_vector_search, [...])
```

**借鉴点**：
- 清晰的节点职责划分
- 条件边实现流程控制
- 节点间状态传递

### 1.3 Agent + Tool 组合模式 ✓

**Deer-Flow 实现**：
```python
# deer-flow/src/agents/agents.py
def create_agent(llm, tools, system_message):
    return llm.bind_tools(tools) | ToolNode(tools)
```

**当前项目采用**：
```python
# src/tools/sni_tools.py
class SNITools:
    def exact_search(self, sni: str) -> List[Dict]:
        ...
    def vector_search(self, query: str, top_k: int = 5):
        ...
```

**借鉴点**：
- 工具封装独立可测试
- LLM + Tool 绑定模式
- 工具调用结果标准化

### 1.4 Prompt 模板管理 ✓

**Deer-Flow 实现**：
```python
# deer-flow/src/prompts/template.py
def apply_prompt_template(prompt_name, variables, locale="en-US"):
    template = load_template(prompt_name, locale)
    return template.format(**variables)
```

**当前项目采用**：
```python
# src/prompts/loader.py
def apply_prompt_variables(prompt_name, variables, locale="en-US"):
    prompt_template = load_prompt(prompt_name, locale)
    for key, value in variables.items():
        prompt_template = prompt_template.replace(f"{{{{ {key} }}}}", str(value))
    return prompt_template
```

**借鉴点**：
- 多语言 Prompt 支持 (en-US / zh-CN)
- 变量替换机制
- Markdown 格式 Prompt 文件

### 1.5 流程可视化日志 ✓

**Deer-Flow 特色**：
```python
logger.info(f"[coordinator] Detected locale: {locale}")
logger.info(f"[planner] Generated {len(plan.steps)} steps")
```

**当前项目采用**：
```python
logger.info(f"[round1_planning_node] Generating round 1 queries for: {query}")
logger.info(f"[round2_planning_node] Discovered organization: {organization}")
```

**借鉴点**：
- 节点名称作为日志前缀
- 关键状态变更记录
- 便于调试和流程追踪

---

## 二、从 GPT-Researcher 借鉴的核心设计

### 2.1 多轮迭代搜索策略 ✓

**GPT-Researcher 实现**：
```python
# gpt_researcher/agent.py
class GPTResearcher:
    async def conduct_research(self):
        # 1. Plan research questions
        # 2. Search for each question
        # 3. Scrape and process sources
        # 4. Synthesize findings
        ...
```

**当前项目采用**：
```
Round1 (后缀定范围) → Round2 (前缀定具体) → Final (验证)
```

**借鉴点**：
- **递进式搜索**：从广度到深度
- **迭代优化**：每轮基于上一轮结果调整查询
- **多角度覆盖**：Round1 生成 4 个不同维度查询

### 2.2 Web 搜索集成 ✓

**GPT-Researcher 实现**：
```python
# gpt_researcher/retrievers/tavily/tavily_search.py
async def search(self, query, max_results=7):
    response = tavily_client.search(query)
    return response.get("results", [])
```

**当前项目采用**：
```python
# src/tools/web_search.py
async def web_search_tool(query: str):
    retriever = TavilySearchAPIRetriever(k=3)
    docs = await retriever.ainvoke(query)
    return "\n\n".join([doc.page_content for doc in docs])
```

**借鉴点**：
- Tavily API 作为默认搜索引擎
- 异步搜索提升性能
- 结果标准化处理

### 2.3 并行搜索优化 ✓

**GPT-Researcher 实现**：
```python
# 并行执行多个搜索任务
tasks = [search_task(q) for q in queries]
results = await asyncio.gather(*tasks)
```

**当前项目采用**：
```python
# src/graph/nodes.py (round1_parallel_search_node)
async def round1_parallel_search_node(self, state):
    semaphore = asyncio.Semaphore(4)
    async def search_with_limit(query: str):
        async with semaphore:
            result = await web_search_tool.ainvoke(query)
    results = await asyncio.gather(*[search_with_limit(q) for q in queries])
```

**借鉴点**：
- **asyncio.gather** 并行执行
- **Semaphore** 控制并发数
- 提升搜索效率（4 个查询并行）

### 2.4 内容合成框架 ✓

**GPT-Researcher 实现**：
```python
# gpt_researcher/skills/writer.py
class ReportGenerator:
    async def write_report(self, query, context, report_type):
        prompt = get_report_prompt(report_type)
        return await llm.ainvoke(prompt.format(query=query, context=context))
```

**当前项目采用**：
```python
# src/graph/nodes.py (synthesize_node)
def synthesize_node(self, state):
    context = build_context_from_all_sources(state)
    synthesis_prompt = apply_prompt_variables("synthesis", {"query": query, "context": context})
    response = self.llm.invoke([{"role": "user", "content": synthesis_prompt}])
    return {"final_answer": response.content}
```

**借鉴点**：
- 聚合所有搜索结果
- LLM 驱动的内容合成
- 结构化输出（JSON）

### 2.5 流式输出支持 ✓

**GPT-Researcher 实现**：
```python
# backend/server/app.py (WebSocket)
async for chunk in researcher.stream_output():
    await websocket.send_json({"type": "report", "content": chunk})
```

**当前项目采用**：
```python
# src/api_server.py
@app.websocket("/ws/search")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    async for event in graph.astream_events(initial_state, version="v1"):
        await websocket.send_json({"type": "log", "data": event})
```

**借鉴点**：
- WebSocket 实时推送
- 流式事件发送
- 用户体验优化

---

## 三、当前项目的创新点

### 3.1 SNI 结构感知搜索策略 ⭐

**独创设计**：
```
Round1: 后缀（ksord.com） + 关键词 → 识别组织（Kingsoft）
Round2: 前缀（shuc-pc-hunt） + 组织 → 定位具体服务
Final: 完整 SNI + Round2 关键词 → 验证发现
```

**优势**：
- 针对域名结构的专门优化
- 递进式缩小搜索范围
- 提高识别准确度

### 3.2 向量搜索 + Web 搜索混合 ⭐

**独创设计**：
```python
1. Vector Search (Qdrant) - 从 SNI 数据库找相似域名
2. Initial Web Search - 直接爬取 SNI 网页
3. Keyword Extraction - 从两个来源提取关键词
```

**优势**：
- 结合结构化数据（数据库）和非结构化数据（Web）
- 多源信息融合
- 降低对单一信息源的依赖

### 3.3 纯关键词查询策略 ⭐

**独创设计**：
```python
# 严格禁止描述性扩展词
❌ "ksord.com 公司"
❌ "shuc-pc kingsoft 服务"
✅ "ksord.com wps"
✅ "shuc-pc kingsoft wps"
```

**优势**：
- 让搜索引擎自然排序
- 避免人为偏见
- 提高搜索结果相关性

### 3.4 关键词相关性验证 ⭐

**独创设计**：
```python
# keyword_extraction.md
- 必须判断关键词与目标 SNI 的相关性
- 如果向量搜索结果不相关，返回空列表 []
- 宁可没有关键词，也不要误导性的
```

**优势**：
- 防止错误信息传播
- 提高后续搜索质量
- 智能容错机制

---

## 四、可以继续改进的方向

### 4.1 借鉴 Deer-Flow：多 Agent 协作 🔄

**Deer-Flow 优势**：
```python
# 多个专门 Agent 协作
coordinator → planner → researcher/analyst/coder → reporter
```

**改进方案**：
```python
# 当前：单一 SNI Agent
# 改进：引入专门 Agent
- IdentifierAgent: 识别 SNI 类型（CDN、API、Web）
- OrgDiscoveryAgent: 专注组织识别
- ServiceDetectorAgent: 专注服务定位
- VerificationAgent: 验证和评分
```

**预期收益**：
- 专业化分工，每个 Agent 更精准
- 易于扩展新的识别策略
- 便于 A/B 测试不同方法

### 4.2 借鉴 GPT-Researcher：自适应规划 🔄

**GPT-Researcher 优势**：
```python
# 根据 Query 类型动态调整策略
if report_type == "detailed_report":
    conduct_deep_research()  # 多 Agent 深度研究
elif report_type == "quick_summary":
    conduct_quick_search()   # 快速概览
```

**改进方案**：
```python
# 当前：固定 3 轮搜索
# 改进：根据 SNI 特征自适应
if is_well_known_domain(sni):  # 如 google.com
    skip_to_synthesis()
elif has_exact_match(sni):
    skip_web_search()
elif is_obscure_domain(sni):
    extend_to_round3()  # 额外搜索轮次
```

**预期收益**：
- 节省已知域名的搜索成本
- 对复杂域名加大投入
- 动态资源分配

### 4.3 借鉴 Deer-Flow：人机交互澄清 🔄

**Deer-Flow 优势**：
```python
# 支持多轮澄清
def needs_clarification(state):
    if ambiguous_query(state):
        return interrupt("Need user input")
```

**改进方案**：
```python
# 当前：直接搜索
# 改进：支持交互澄清
if ambiguous_sni(query):  # 如 "api" 不完整
    clarify_prompt = "Is this api.example.com or api.company.com?"
    user_response = await interrupt(clarify_prompt)
    query = user_response
```

**预期收益**：
- 减少无效搜索
- 提高用户满意度
- 更准确的结果

### 4.4 借鉴 GPT-Researcher：多数据源融合 🔄

**GPT-Researcher 优势**：
```python
# 支持多种数据源
report_source = "hybrid"  # web + local + mcp
```

**改进方案**：
```python
# 当前：Web + Qdrant
# 改进：添加更多数据源
- WHOIS 数据库（域名注册信息）
- Certificate Transparency Logs（SSL 证书）
- DNS 记录（子域名枚举）
- Shodan/Censys（网络扫描数据）
- GitHub（开源项目）
```

**预期收益**：
- 更全面的信息覆盖
- 多角度交叉验证
- 提高识别准确率

### 4.5 借鉴 Deer-Flow：记忆和上下文管理 🔄

**Deer-Flow 优势**：
```python
# 使用 MemorySaver 持久化历史
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
```

**改进方案**：
```python
# 当前：每次搜索独立
# 改进：跨查询记忆
- 相同域名的历史搜索结果缓存
- 相似 SNI 的识别模式复用
- 用户反馈学习（标注正确/错误）
```

**预期收益**：
- 避免重复搜索
- 加速相似查询
- 持续优化识别准确度

### 4.6 借鉴 GPT-Researcher：深度爬取 🔄

**GPT-Researcher 优势**：
```python
# gpt_researcher/actions/web_scraping.py
async def scrape_urls(urls, config):
    # 支持多种爬取方法：
    - BeautifulSoup
    - Playwright（JavaScript 渲染）
    - Jina Reader API
```

**改进方案**：
```python
# 当前：简单 HTTP 请求
# 改进：智能爬取策略
- 检测反爬虫机制
- JavaScript 渲染支持
- 自动绕过 Cloudflare
- 提取结构化数据（JSON-LD）
```

**预期收益**：
- 提高爬取成功率
- 获取更丰富的信息
- 支持现代 Web 应用

### 4.7 增强错误处理和重试机制 🔄

**参考两个项目的实践**：
```python
# GPT-Researcher: 优雅降级
try:
    result = await primary_source()
except Exception:
    result = await fallback_source()

# Deer-Flow: 工具调用容错
sanitized_response = sanitize_tool_response(tool_output)
```

**改进方案**：
```python
# 当前：简单 try-except
# 改进：分级重试策略
- 网络超时：重试 3 次（指数退避）
- API 限流：等待 + 降级到备用 API
- 解析错误：多种解析器尝试
- LLM 错误：切换到备用模型
```

**预期收益**：
- 提高系统稳定性
- 减少用户体验中断
- 自动故障恢复

### 4.8 性能监控和评估 🔄

**GPT-Researcher 特色**：
```python
# evals/ 目录包含完整的评估框架
- hallucination_eval: 检测幻觉
- simple_evals: 答案质量评估
```

**改进方案**：
```python
# 当前：无系统化评估
# 改进：建立评估体系
- 识别准确率（Precision/Recall）
- 搜索效率（平均查询次数）
- 响应时间（P50/P99）
- 成本分析（API 调用次数）
- A/B 测试框架
```

**预期收益**：
- 量化改进效果
- 发现性能瓶颈
- 指导优化方向

---

## 五、架构对比总结

| 维度 | Deer-Flow | GPT-Researcher | SNI Search (当前) |
|------|-----------|----------------|------------------|
| **核心框架** | LangGraph | 自定义 + LangChain | LangGraph |
| **多 Agent** | ✅ 多角色协作 | ✅ 多技能协作 | ❌ 单 Agent |
| **状态管理** | TypedDict + Memory | 自定义 Memory | TypedDict |
| **搜索策略** | 动态规划 | 多轮迭代 | ✅ **SNI 结构感知** |
| **数据来源** | Web + MCP | Web + Local + MCP | ✅ **Vector + Web** |
| **并行搜索** | 部分支持 | ✅ 全面并行 | ✅ Round1/2 并行 |
| **人机交互** | ✅ 澄清机制 | 有限 | ❌ 无 |
| **流式输出** | 部分支持 | ✅ WebSocket | ✅ WebSocket |
| **Prompt 管理** | ✅ 模板化 | ✅ 家族化 | ✅ 多语言模板 |
| **评估体系** | 基础 | ✅ 完善 | ❌ 缺失 |

---

## 六、优先改进建议（按重要性排序）

### 高优先级 🔴

1. **建立评估体系**（参考 GPT-Researcher）
   - 量化当前性能基线
   - 设立改进目标

2. **增强错误处理**（参考两个项目）
   - 提高系统鲁棒性
   - 用户体验关键

3. **多数据源融合**（参考 GPT-Researcher）
   - WHOIS、CT Logs、DNS
   - 显著提升识别能力

### 中优先级 🟡

4. **自适应搜索策略**（参考 GPT-Researcher）
   - 节省已知域名成本
   - 对复杂域名加大投入

5. **记忆和缓存机制**（参考 Deer-Flow）
   - 避免重复搜索
   - 提升响应速度

6. **深度爬取支持**（参考 GPT-Researcher）
   - JavaScript 渲染
   - 结构化数据提取

### 低优先级 🟢

7. **多 Agent 架构**（参考 Deer-Flow）
   - 需要大规模重构
   - 先验证收益

8. **人机交互澄清**（参考 Deer-Flow）
   - 改善用户体验
   - 复杂度较高

---

## 七、结论

**当前项目的优势**：
- ✅ 针对 SNI 的专门优化（结构感知搜索）
- ✅ 混合向量搜索和 Web 搜索
- ✅ 纯关键词查询策略
- ✅ 智能关键词过滤

**需要改进的方面**：
- 🔄 缺乏系统化评估
- 🔄 错误处理不够完善
- 🔄 数据源单一（只有 Web + Qdrant）
- 🔄 无人机交互澄清
- 🔄 无跨查询记忆

**借鉴策略**：
1. **从 Deer-Flow 学习**：多 Agent 协作、人机交互、记忆管理
2. **从 GPT-Researcher 学习**：多数据源、深度爬取、评估体系
3. **保持创新点**：SNI 结构感知、混合搜索、纯关键词策略

通过有选择性地吸收两个参考项目的优点，并保持当前项目的创新特色，SNI Search 可以发展成为更强大、更可靠的 SNI 识别系统。
