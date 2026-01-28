# AI 搜索界面技术规格

## 组件清单

### shadcn/ui 组件
- Button - 发送按钮、附件按钮
- Switch - Pro 模式切换
- Card - 搜索结果卡片
- Collapsible - Agent Trace 展开/收起
- ScrollArea - 搜索结果滚动区域
- Textarea - 输入框

### 自定义组件

| 组件名 | 用途 | 文件路径 |
|--------|------|----------|
| GradientTitle | 渐变文字标题 | src/components/GradientTitle.tsx |
| DecoratedSubtitle | 带装饰线的副标题 | src/components/DecoratedSubtitle.tsx |
| SmartInput | 智能输入框（含工具栏） | src/components/SmartInput.tsx |
| SearchResults | 搜索结果列表 | src/components/SearchResults.tsx |
| SearchResultItem | 单个搜索结果项 | src/components/SearchResultItem.tsx |
| AgentTrace | Agent 思考过程面板 | src/components/AgentTrace.tsx |
| SourceIcon | 来源网站图标 | src/components/SourceIcon.tsx |

### 自定义 Hooks

| Hook 名 | 用途 | 文件路径 |
|---------|------|----------|
| useSearch | 搜索逻辑 | src/hooks/useSearch.ts |

### Zustand Stores

| Store 名 | 用途 | 文件路径 |
|----------|------|----------|
| searchStore | 搜索状态管理 | src/stores/searchStore.ts |
| agentTraceStore | Agent Trace 状态 | src/stores/agentTraceStore.ts |

---

## 动画实现方案

| 动画 | 库 | 实现方式 | 复杂度 |
|------|-----|----------|--------|
| 标题入场 fadeIn + slideUp | Framer Motion | motion.h1 with initial/animate | 低 |
| 副标题入场 fadeIn | Framer Motion | motion.p with delay | 低 |
| 输入框入场 fadeIn + scale | Framer Motion | motion.div with spring | 低 |
| 输入框聚焦边框动画 | CSS Transition | transition-all duration-200 | 低 |
| 发送按钮悬停/点击 | CSS Transition + Framer Motion | whileHover/whileTap | 低 |
| Pro 切换开关 | CSS Transition | transition-colors duration-200 | 低 |
| 搜索结果 staggered 入场 | Framer Motion | staggerChildren + motion.div | 中 |
| 结果项悬停高亮 | CSS Transition | transition-all duration-150 | 低 |
| Agent Trace 展开/收起 | Framer Motion | AnimatePresence + motion | 中 |

---

## 项目文件结构

```
src/
├── components/
│   ├── GradientTitle.tsx
│   ├── DecoratedSubtitle.tsx
│   ├── SmartInput.tsx
│   ├── SearchResults.tsx
│   ├── SearchResultItem.tsx
│   ├── AgentTrace.tsx
│   ├── SourceIcon.tsx
│   └── ui/           # shadcn/ui 组件
├── stores/
│   ├── searchStore.ts
│   └── agentTraceStore.ts
├── hooks/
│   └── useSearch.ts
├── types/
│   └── index.ts
├── sections/
│   ├── HeroSection.tsx
│   └── ResultsSection.tsx
├── lib/
│   └── utils.ts
├── App.tsx
├── main.tsx
└── index.css
```

---

## 依赖清单

### 核心依赖（技能已包含）
- React 19.2.0
- TypeScript 5.9.3
- Vite 7.2.4
- Tailwind CSS 4.1.18
- Lucide React 0.562.0

### 需要安装的依赖
```bash
npm install zustand framer-motion
```

---

## 类型定义

```typescript
// src/types/index.ts

export interface SearchResult {
  id: string;
  source: string;
  sourceIcon: string;
  title: string;
  description: string;
  url: string;
}

export interface AgentTraceStep {
  id: string;
  type: 'thinking' | 'search' | 'analyze' | 'conclude';
  content: string;
  timestamp: number;
}

export interface SearchState {
  query: string;
  isSearching: boolean;
  results: SearchResult[];
  totalCount: number;
  proMode: boolean;
}

export interface AgentTraceState {
  steps: AgentTraceStep[];
  isExpanded: boolean;
  isVisible: boolean;
}
```

---

## Store 接口设计

### searchStore

```typescript
interface SearchStore {
  // State
  query: string;
  isSearching: boolean;
  results: SearchResult[];
  totalCount: number;
  proMode: boolean;
  
  // Actions
  setQuery: (query: string) => void;
  setProMode: (enabled: boolean) => void;
  search: () => Promise<void>;
  clearResults: () => void;
}
```

### agentTraceStore

```typescript
interface AgentTraceStore {
  // State
  steps: AgentTraceStep[];
  isExpanded: boolean;
  isVisible: boolean;
  
  // Actions
  addStep: (step: Omit<AgentTraceStep, 'id' | 'timestamp'>) => void;
  toggleExpanded: () => void;
  show: () => void;
  hide: () => void;
  clear: () => void;
}
```

---

## 关键实现细节

### 1. 渐变文字标题

使用 CSS background-clip: text 实现：

```tsx
<h1 className="text-5xl font-bold bg-gradient-to-r from-emerald-500 via-emerald-400 to-emerald-600 bg-clip-text text-transparent">
  Engineered for Deep Understanding, Not Small Talk
</h1>
```

### 2. 装饰副标题

使用 flex 布局实现两侧装饰线：

```tsx
<div className="flex items-center gap-4">
  <div className="w-12 h-px bg-gray-200" />
  <p className="text-gray-500">Don't just chat...</p>
  <div className="w-12 h-px bg-gray-200" />
</div>
```

### 3. 智能输入框

使用 textarea + 底部工具栏布局：

```tsx
<div className="relative bg-white border border-gray-200 rounded-2xl shadow-sm">
  <textarea className="w-full p-5 resize-none outline-none" />
  <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100">
    {/* Pro 切换 */}
    {/* 附件按钮 */}
    {/* 发送按钮 */}
  </div>
</div>
```

### 4. 搜索结果 staggered 动画

使用 Framer Motion 的 staggerChildren：

```tsx
<motion.div
  initial="hidden"
  animate="visible"
  variants={{
    visible: { transition: { staggerChildren: 0.05 } }
  }}
>
  {results.map(result => (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 20 },
        visible: { opacity: 1, y: 0 }
      }}
    />
  ))}
</motion.div>
```

### 5. 来源图标映射

```typescript
const sourceIconMap: Record<string, string> = {
  '搜狗百科': 'sogou',
  '爱奇艺': 'iqiyi',
  '新浪微博': 'weibo',
  '漫漫看': 'manman',
  '电视猫': 'tvmao',
  '天眼查': 'tianyancha',
  '百度百科': 'baidu',
  '抖音': 'douyin',
};
```
