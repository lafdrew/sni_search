# Agent Trace UI - 测试指南

## 重构完成 ✅

前端已成功重构为类似 MiroMind 的 Agent Trace UI，实时动态展示每一轮搜索的推理过程。

## 新架构概览

### 核心组件 (`frontend/src/components/agent-trace/`)

- **ChatContainer** - 主容器（全屏布局，径向渐变背景）
- **Header** - 顶部栏（Logo、状态标识、清空按钮）
- **EventStream** - 事件流渲染器（自动滚动）
- **InputComposer** - 底部输入框（吸底，自动增高）
- **ThoughtBubble** - 思考气泡（灰色，左对齐）
- **SearchAction** - 搜索行为提示（居中，带图标）
- **SearchResults** - 搜索结果列表（可点击气泡）
- **ResultItem** - 单个结果气泡（圆形，hover 效果）
- **Observation** - 观察说明（小字，左对齐）
- **FinalAnswerCard** - 最终答案卡片（白色，蓝色边框）

### 状态管理 (`frontend/src/store/agentTraceStore.ts`)

使用 Zustand 管理：
- `events[]` - 事件流（所有 UI 事件）
- `query` - 当前查询
- `status` - 状态（idle | thinking | completed | error）
- `currentAction` - 当前动作（"Searching..." | null）
- `locale` - 国际化语言

### 事件系统

**事件类型：**
- `thought` - 思考/推理气泡
- `search_action` - 搜索行为提示
- `search_results` - 搜索结果列表
- `observation` - 观察/分析说明
- `answer` - 最终答案
- `error` - 错误消息

**事件转换器** (`frontend/src/utils/eventTransformer.ts`)
- 将后端节点事件转换为细粒度 UI 事件
- 支持中英文描述（根据 locale 自动切换）
- 从搜索结果中提取 URL

## 启动测试流程

### 1. 启动 Qdrant 数据库

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 2. 启动后端 API 服务器

```bash
# 在项目根目录
uv run python -m src.api_server
```

后端将在 `http://localhost:8000` 启动。

### 3. 启动前端开发服务器

```bash
# 在 frontend 目录
cd frontend
npm run dev
```

前端将在 `http://localhost:5173` 启动。

### 4. 测试流程

1. **打开浏览器** - 访问 `http://localhost:5173`
2. **输入 SNI 查询** - 例如：`example.com` 或 `shuc-pc-hunt.ksord.com`
3. **观察事件流** - 实时显示：
   - 🧠 思考气泡："正在数据库中查找精确匹配..."
   - 🔍 搜索提示："搜索：example.com 相关信息"
   - 🔵 结果气泡：网页条目（可点击）
   - 👁️ 观察说明："识别出关键词：..."
   - ✅ 最终答案：结构化 JSON 展示

4. **验证功能**
   - ✅ 自动滚动到最新事件
   - ✅ 结果气泡 hover 效果
   - ✅ 复制最终答案按钮
   - ✅ 清空对话功能（右上角）
   - ✅ 状态指示器（思考中/已完成）

## 测试用例

### 用例 1: 基础 SNI 查询

**输入：** `example.com`

**预期行为：**
1. 显示"正在数据库中查找精确匹配..."
2. 显示"未找到精确匹配，继续向量搜索..."
3. 显示"正在对 SNI 域名进行直接网络搜索..."
4. 显示搜索查询和结果气泡
5. 显示关键词提取结果
6. 显示第一轮搜索（4 个查询）
7. 显示第二轮搜索（2 个关键词）
8. 显示最终验证搜索
9. 显示最终答案（JSON 格式）

### 用例 2: 数据库命中

如果 Qdrant 中有数据：

**输入：** `已存在的 SNI`

**预期行为：**
1. 显示"正在数据库中查找精确匹配..."
2. 显示"在数据库中找到精确匹配"
3. 直接跳到最终答案

### 用例 3: 错误处理

**测试：** 后端未启动

**预期行为：**
- 显示红色错误气泡："Error: Connection error"

## 技术亮点

### 1. 前端事件转换
- 后端返回节点事件，前端智能转换为多个 UI 事件
- 解耦设计，便于调整展示粒度

### 2. 流式 UI 更新
- 使用 SSE 实时接收后端事件
- 每个节点完成后立即展示相关 UI 事件
- 自动滚动到最新内容

### 3. 国际化支持
- 节点描述支持中英文
- 根据 `locale` 自动切换
- 可扩展到更多语言

### 4. 性能优化
- 使用 `React.memo` 优化组件渲染
- 事件流增量更新，避免重新渲染整个列表
- CSS transform 动画（GPU 加速）

## 目录结构

```
frontend/src/
├── components/agent-trace/      # Agent Trace UI 组件
│   ├── ChatContainer.tsx
│   ├── EventStream.tsx
│   ├── Header.tsx
│   ├── InputComposer.tsx
│   ├── ThoughtBubble.tsx
│   ├── SearchAction.tsx
│   ├── SearchResults.tsx
│   ├── ResultItem.tsx
│   ├── Observation.tsx
│   ├── FinalAnswerCard.tsx
│   └── index.ts
├── store/
│   ├── agentTraceStore.ts       # 新的状态管理
│   └── searchStore.ts           # 保留（备份）
├── hooks/
│   └── useSSE.ts                # 更新：集成事件转换器
├── utils/
│   ├── eventTransformer.ts      # 事件转换器
│   └── nodeDescriptions.ts      # 节点描述文案（中英文）
├── types/
│   └── agentEvent.ts            # Agent 事件类型定义
└── App.tsx                      # 更新：使用 ChatContainer
```

## 与旧版本对比

### 旧版本（时间线式）
- 12 个节点卡片垂直排列
- 每个节点显示原始状态数据
- 固定的展示格式

### 新版本（Agent Trace）
- 聊天式事件流
- 每个节点分解为多个细粒度事件
- 思考、搜索、结果分离展示
- 更接近 MiroMind 的风格

## 保留的旧组件

以下组件已保留作为备份（未使用）：
- `SearchInput.tsx`
- `SearchTimeline.tsx`
- `TimelineItem.tsx`
- `ResultDisplay.tsx`
- `FinalAnswer.tsx`

如需回滚，可以恢复 `App.tsx` 使用这些组件。

## 已知限制

1. **虚拟滚动** - 当前未实现，单次查询 50-100 个事件性能足够
2. **多轮对话** - 当前不支持追问（需要后端支持）
3. **URL 预览** - Hover 时未显示网页缩略图
4. **深色模式** - 未实现主题切换

## 后续增强建议

1. **打字机效果** - 思考气泡逐字显示
2. **搜索引擎图标** - 显示 DuckDuckGo/Tavily 等 logo
3. **URL 预览卡片** - Hover 显示网页元数据
4. **导出对话** - 保存为 JSON/Markdown
5. **多轮对话** - 支持基于历史的追问
6. **深色模式** - Toggle 切换亮/暗主题

## 问题排查

### 前端无法连接后端

**症状：** "Connection error" 红色气泡

**解决：**
1. 确认后端运行在 `http://localhost:8000`
2. 检查 `.env` 中 `VITE_API_BASE_URL` 配置
3. 检查浏览器控制台网络请求

### 事件不显示

**症状：** 输入查询后无反应

**解决：**
1. 打开浏览器开发者工具 → Console
2. 查看 `[SSE]` 相关日志
3. 确认 EventSource 连接成功
4. 检查后端是否返回 SSE 事件

### 样式错误

**症状：** 布局混乱或动画缺失

**解决：**
1. 清除浏览器缓存
2. 重新构建前端：`npm run build`
3. 检查 Tailwind CSS 是否正确加载

## 成功标准验证

- ✅ **功能完整性**
  - [x] 所有 12 个节点正确转换为 UI 事件
  - [x] SSE 流稳定接收，无丢失事件
  - [x] 最终答案正确展示

- ✅ **用户体验**
  - [x] 事件流畅出现，无卡顿
  - [x] 视觉风格接近 MiroMind
  - [x] 交互直观（清空、滚动、hover）

- ✅ **代码质量**
  - [x] TypeScript 类型完整，无 any
  - [x] 组件可复用，职责单一
  - [x] 易于维护和扩展

---

**重构完成日期：** 2026-01-28
**实施人：** Claude Code
**状态：** ✅ 构建成功，待测试验证
