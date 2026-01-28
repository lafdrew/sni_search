# HeroSection 欢迎页 - 使用指南

## 🎉 已创建组件

### 新增文件
1. **`frontend/src/sections/HeroSection.tsx`** - 主欢迎页组件
2. **`frontend/src/components/ExampleQueries.tsx`** - 示例查询卡片

### 修改文件
1. **`frontend/src/App.tsx`** - 添加路由系统
2. **`frontend/src/main.tsx`** - 添加 BrowserRouter
3. **`frontend/src/components/agent-trace/ChatContainer.tsx`** - 支持 URL 查询参数

## 📍 路由结构

```
/ (根路径)
├─ HeroSection (欢迎页)
│  ├─ 大标题: "Intelligent SNI Domain Recognition"
│  ├─ 副标题: "Multi-round search • Vector database • LangGraph powered"
│  ├─ 3 个功能高亮卡片
│  ├─ 大输入框
│  └─ 4 个示例查询

/chat (聊天界面)
├─ ChatContainer (Agent 追踪界面)
│  ├─ Header (状态栏 + Home 按钮)
│  ├─ EventStream (事件流)
│  └─ InputComposer (输入框)
│
└─ 支持 URL 参数: /chat?q=your-query
   自动开始搜索
```

## 🚀 使用方法

### 1. 启动开发服务器

```bash
cd frontend
npm run dev
```

### 2. 访问欢迎页

打开浏览器访问: **http://localhost:5173/**

你会看到：
- ✨ 精美的渐变标题
- 🎯 3 个功能亮点卡片
- ✍️ 大输入框（120px 高度）
- 📋 4 个可点击的示例查询

### 3. 交互流程

**方式 1: 使用输入框**
1. 在大输入框中输入 SNI 域名
2. 按 Enter 或点击 "Search" 按钮
3. 自动跳转到 `/chat?q=your-query`
4. ChatContainer 自动开始搜索

**方式 2: 点击示例查询**
1. 点击任意示例查询卡片
2. 自动跳转到 `/chat?q=example-query`
3. ChatContainer 自动开始搜索

**方式 3: 直接访问聊天页**
- 访问 `/chat` 进入空白聊天界面
- 手动输入查询

### 4. 导航

- 欢迎页 → 聊天页: 点击示例或提交查询
- 欢迎页 → 聊天页 (空白): 点击 "Go to Chat" 按钮
- 聊天页 → 欢迎页: 点击 "Home" 按钮

## 🎨 HeroSection 设计特点

### 布局
- **垂直居中**: 内容在视口中央
- **渐变背景**: 翡翠色渐变 (emerald-50 → teal-50 → cyan-50)
- **响应式**: 手机/平板/桌面自适应

### 顶部导航栏
```tsx
<Logo /> + "SNI Agent v2.0"  |  [Go to Chat]
```

### 功能卡片
```
┌─────────┐ ┌─────────┐ ┌─────────┐
│ 🎯      │ │ 🔍      │ │ 🤖      │
│ Exact   │ │ 4-2-1   │ │ Lang-   │
│ Match   │ │ Search  │ │ Graph   │
└─────────┘ └─────────┘ └─────────┘
```

### 大输入框
- 高度: 120px
- 圆角: 2xl
- 边框: 悬停时变为翡翠色
- 底部工具栏: "Powered by Claude & LangGraph"

### 示例查询（4个）
1. **SNI Domain Lookup** - `api.bilibili.com`
2. **Vector Search** - `video streaming service`
3. **Web Research** - `what is bilibili.com`
4. **Entity Recognition** - `tencent cloud services`

## 🔧 自定义示例查询

编辑 `frontend/src/components/ExampleQueries.tsx`:

```typescript
const examples: ExampleQuery[] = [
  {
    icon: Globe,
    text: '你的标题',
    description: '你的描述',
    query: '你的查询内容'
  },
  // 添加更多...
];
```

支持的图标：`Search`, `Globe`, `Database`, `FileSearch`, `Zap`, `Target` 等

## 🎯 与 Kimi Agent 的对比

| 特性 | Kimi Agent | SNI Agent (本项目) |
|------|-----------|-------------------|
| **布局** | 垂直居中 ✅ | 垂直居中 ✅ |
| **大标题** | 硬编码英文 | 自定义标题 ✅ |
| **Pro 模式** | ✅ (未实现) | ❌ (已移除) |
| **示例查询** | ❌ | ✅ 4 个可点击 |
| **功能卡片** | ❌ | ✅ 3 个卡片 |
| **路由系统** | ❌ 单页 | ✅ / 和 /chat |
| **URL 参数** | ❌ | ✅ 自动搜索 |
| **Home 按钮** | ❌ | ✅ 返回首页 |
| **暗黑模式** | ❌ | ✅ 全支持 |
| **国际化** | ❌ | ✅ i18n |

## 📱 响应式设计

### 桌面 (≥1024px)
- 导航栏: Logo + 标题 + 按钮
- 示例查询: 2 列网格
- 输入框: 全宽

### 平板 (768px - 1023px)
- 导航栏: 正常显示
- 示例查询: 2 列网格
- 按钮文字: 显示

### 手机 (<768px)
- 导航栏: Logo + 按钮（无文字）
- 示例查询: 1 列堆叠
- 按钮文字: 隐藏（仅图标）

## 🌈 动画效果

### 入场动画（Framer Motion）
1. **Logo + 标题**: 从左滑入 (x: -20 → 0)
2. **按钮**: 从右滑入 (x: 20 → 0)
3. **大标题**: 从下向上 (y: 30 → 0)
4. **副标题**: 淡入 (delay: 0.2s)
5. **功能卡片**: 缩放 (scale: 0.9 → 1, 递增延迟)
6. **输入框**: 缩放 + 弹跳效果
7. **示例查询**: 从下向上 (递增延迟)

### 交互动画
- **按钮悬停**: scale(1.05)
- **按钮点击**: scale(0.98)
- **卡片悬停**: scale(1.02) + translateY(-2px)
- **输入框聚焦**: 边框变为翡翠色

## 🔍 技术细节

### 依赖包
- `react-router-dom` (新增) - 路由管理
- `framer-motion` - 动画
- `lucide-react` - 图标

### 关键代码片段

**URL 参数自动搜索 (ChatContainer.tsx):**
```typescript
useEffect(() => {
  const query = searchParams.get('q');
  if (query) {
    handleSubmit(query);
  }
}, [searchParams]);
```

**导航跳转 (ExampleQueries.tsx):**
```typescript
const handleQueryClick = (query: string) => {
  navigate(`/chat?q=${encodeURIComponent(query)}`);
};
```

## 🐛 故障排除

### 问题 1: 路由不工作
**症状:** 刷新页面 404
**解决:** Vite 开发服务器默认支持，生产环境需配置服务器重定向

### 问题 2: URL 参数不触发搜索
**检查:**
1. ChatContainer 是否导入 `useSearchParams`
2. useEffect 依赖是否包含 `searchParams`
3. handleSubmit 函数是否正确调用

### 问题 3: 示例查询点击无反应
**检查:**
1. ExampleQueries 是否导入 `useNavigate`
2. handleQueryClick 函数是否正确实现
3. encodeURIComponent 是否正确编码

## 📈 未来改进建议

1. **SEO 优化**
   - 添加 React Helmet
   - 设置 meta 标签

2. **加载状态**
   - 示例查询 loading skeleton
   - 路由切换过渡动画

3. **更多示例**
   - 分类示例（基础/高级/企业）
   - 随机推荐

4. **用户引导**
   - 首次访问 tour
   - 功能介绍弹窗

5. **分析追踪**
   - 示例点击统计
   - 用户行为分析

## 🎊 完成！

现在你已经有了一个专业的欢迎页，结合了：
- ✅ Kimi Agent 的营销设计
- ✅ SNI Agent 的强大功能
- ✅ 最佳用户体验

**立即体验: http://localhost:5173/**
