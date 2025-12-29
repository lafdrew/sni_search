# SNI Search 文档中心

欢迎来到 SNI Search 文档中心。本项目使用 LangGraph 构建了一个智能化的 SNI 域名识别系统。

## 📚 文档导航

### 🚀 快速开始
如果你是第一次接触 LangGraph 或本项目，建议按以下顺序阅读：

1. **[README](../README.md)** - 项目概览和基本使用
2. **[LangGraph 快速入门](./langgraph-quickstart.md)** - 5分钟了解 LangGraph
3. **[工作流可视化](./workflow-visualization.md)** - 通过图表理解系统流程

### 📖 深入理解
当你需要深入了解系统架构和实现细节时：

4. **[LangGraph 架构指南](./langgraph-architecture.md)** - 完整的架构文档
   - LangGraph 核心概念
   - 项目架构设计
   - 状态管理详解
   - 节点实现细节
   - 最佳实践

---

## 🎯 按主题查找

### LangGraph 相关

#### 基础概念
- **什么是 LangGraph?** → [快速入门](./langgraph-quickstart.md#核心概念)
- **状态图是什么?** → [架构指南 - LangGraph 介绍](./langgraph-architecture.md#什么是-langgraph)
- **节点和边的作用?** → [快速入门 - 核心概念](./langgraph-quickstart.md#核心概念)

#### 实现细节
- **如何定义状态?** → [架构指南 - 状态管理](./langgraph-architecture.md#状态管理)
- **如何创建节点?** → [架构指南 - 节点实现](./langgraph-architecture.md#节点实现)
- **如何添加条件分支?** → [架构指南 - 流程控制](./langgraph-architecture.md#流程控制)
- **如何并行执行?** → [快速入门 - 并行执行](./langgraph-quickstart.md#并行执行)

### 工作流相关

#### 流程理解
- **完整工作流图** → [工作流可视化 - 完整工作流图](./workflow-visualization.md#完整工作流图)
- **多轮搜索策略** → [工作流可视化 - 搜索策略](./workflow-visualization.md#搜索策略分析)
- **节点执行顺序** → [工作流可视化 - 节点详细说明](./workflow-visualization.md#节点详细说明)
- **数据流动** → [工作流可视化 - 数据流图](./workflow-visualization.md#数据流图)

#### 性能优化
- **并发控制** → [架构指南 - 并发控制](./langgraph-architecture.md#2-并发控制)
- **执行时间分析** → [工作流可视化 - 性能指标](./workflow-visualization.md#性能指标)
- **优化建议** → [工作流可视化 - 优化点](./workflow-visualization.md#优化点)

### 开发指南

#### 使用示例
- **基本用法** → [快速入门 - 完整示例](./langgraph-quickstart.md#完整工作流示例)
- **API 集成** → [架构指南 - API 服务器集成](./langgraph-architecture.md#api-服务器集成)
- **测试示例** → [快速入门 - 调试技巧](./langgraph-quickstart.md#调试技巧)

#### 扩展开发
- **添加新节点** → [快速入门 - 扩展示例](./langgraph-quickstart.md#添加新节点)
- **错误处理** → [架构指南 - 错误处理](./langgraph-architecture.md#5-错误处理)
- **最佳实践** → [快速入门 - 最佳实践](./langgraph-quickstart.md#最佳实践)

---

## 📊 文档对比

| 文档 | 适合人群 | 阅读时间 | 内容深度 |
|------|---------|---------|---------|
| [README](../README.md) | 所有用户 | 3 分钟 | ⭐ 入门 |
| [快速入门](./langgraph-quickstart.md) | 初学者 | 5-10 分钟 | ⭐⭐ 基础 |
| [工作流可视化](./workflow-visualization.md) | 视觉学习者 | 10-15 分钟 | ⭐⭐ 基础 |
| [架构指南](./langgraph-architecture.md) | 开发者 | 30-45 分钟 | ⭐⭐⭐⭐⭐ 深入 |

---

## 🔍 常见问题索引

### 概念理解
- **Q: LangGraph 和 LangChain 有什么区别?**
  - A: 见 [架构指南 - 为什么选择 LangGraph](./langgraph-architecture.md#为什么选择-langgraph)

- **Q: 为什么需要多轮搜索?**
  - A: 见 [工作流可视化 - 搜索策略分析](./workflow-visualization.md#搜索策略分析)

- **Q: 状态是如何在节点间传递的?**
  - A: 见 [架构指南 - 状态传递机制](./langgraph-architecture.md#状态传递机制)

### 实现细节
- **Q: 如何实现并行搜索?**
  - A: 见 [架构指南 - 异步搜索节点](./langgraph-architecture.md#3-异步搜索节点)

- **Q: LLM 如何集成到节点中?**
  - A: 见 [架构指南 - LLM 推理节点](./langgraph-architecture.md#2-llm-推理节点)

- **Q: 如何处理节点执行失败?**
  - A: 见 [工作流可视化 - 错误处理流程](./workflow-visualization.md#错误处理流程)

### 使用问题
- **Q: 如何切换 LLM 提供商?**
  - A: 见 [README - Configuration](../README.md#configuration)

- **Q: 如何调试工作流?**
  - A: 见 [快速入门 - 调试技巧](./langgraph-quickstart.md#调试技巧)

- **Q: 如何添加新的搜索引擎?**
  - A: 见 [架构指南 - 扩展方向](./langgraph-architecture.md#扩展方向)

---

## 💡 学习路径

### 路径 1: 快速上手（新手）
```
README → 快速入门 → 运行示例 → 查看日志
```
**目标**: 能够运行和使用系统

### 路径 2: 理解原理（开发者）
```
README → 工作流可视化 → 架构指南 → 阅读源码
```
**目标**: 理解系统设计和实现

### 路径 3: 深度定制（高级开发者）
```
架构指南 → 源码分析 → 添加功能 → 性能优化
```
**目标**: 能够扩展和优化系统

---

## 🎓 相关资源

### 官方文档
- [LangGraph 官方文档](https://python.langchain.com/docs/langgraph)
- [LangChain 官方文档](https://python.langchain.com/)
- [Qdrant 文档](https://qdrant.tech/documentation/)

### 示例代码
- [demo/test_multi_round_search.py](../demo/test_multi_round_search.py) - 完整测试示例
- [src/graph/builder.py](../src/graph/builder.py) - 工作流构建
- [src/graph/nodes.py](../src/graph/nodes.py) - 节点实现

### 社区资源
- LangChain Discord
- LangGraph GitHub Issues
- LangChain Blog

---

## 📝 贡献文档

欢迎贡献文档改进！

### 文档规范
- 使用 Markdown 格式
- 包含代码示例
- 添加图表说明
- 保持中英文对照

### 提交流程
1. Fork 项目
2. 创建文档分支
3. 编写/修改文档
4. 提交 Pull Request

---

## 📧 反馈和支持

如果你在使用文档时遇到问题：
- 提交 Issue
- 发送邮件
- 加入讨论组

---

**最后更新**: 2025-12-26
