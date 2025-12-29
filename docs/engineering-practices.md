# SNI Search 工程化实践参考

本文档总结 **Deer-Flow** 和 **GPT-Researcher** 两个项目的工程化实践，为 SNI Search 项目的未来改进提供参考。

---

## 目录

1. [上下文管理（Context Management）](#1-上下文管理context-management)
2. [配置管理（Configuration Management）](#2-配置管理configuration-management)
3. [日志系统（Logging System）](#3-日志系统logging-system)
4. [工具抽象（Tool Abstraction）](#4-工具抽象tool-abstraction)
5. [状态管理（State Management）](#5-状态管理state-management)
6. [错误处理（Error Handling）](#6-错误处理error-handling)
7. [实施建议（Implementation Recommendations）](#7-实施建议implementation-recommendations)

---

## 1. 上下文管理（Context Management）

### 1.1 Deer-Flow 的实现：字符级 Token 计数

**核心思想**：基于字符数估算 Token，区分英文和非英文字符，针对不同消息类型应用不同系数。

**实现代码**：`deer-flow/src/utils/context_manager.py`

```python
class ContextManager:
    """管理 LLM 上下文，包括 Token 计数和压缩"""

    def __init__(self, max_tokens: int = 100000):
        self.max_tokens = max_tokens

    def count_tokens(self, text: str) -> int:
        """估算 Token 数量

        估算规则：
        - 英文字符：4 个字符 ≈ 1 token
        - 非英文字符：1 个字符 ≈ 1 token
        """
        if not text:
            return 0

        # 统计英文和非英文字符
        english_chars = sum(1 for c in text if ord(c) < 128)
        non_english_chars = len(text) - english_chars

        # 估算 Token
        tokens = (english_chars / 4) + non_english_chars
        return int(tokens)

    def count_message_tokens(self, message: BaseMessage) -> int:
        """根据消息类型计算 Token

        消息类型系数：
        - SystemMessage: 1.1x （系统提示通常更复杂）
        - AIMessage: 1.2x （AI 回复可能包含结构化数据）
        - ToolMessage: 1.3x （工具输出可能包含 JSON/代码）
        - HumanMessage: 1.0x （用户输入基准）
        """
        base_tokens = self.count_tokens(message.content)

        if isinstance(message, SystemMessage):
            return int(base_tokens * 1.1)
        elif isinstance(message, AIMessage):
            return int(base_tokens * 1.2)
        elif isinstance(message, ToolMessage):
            return int(base_tokens * 1.3)
        else:
            return base_tokens

    def compress_messages(
        self,
        messages: List[BaseMessage],
        preserve_prefix: int = 3
    ) -> List[BaseMessage]:
        """压缩消息列表，保留前缀和尾部

        策略：
        1. 保留前 N 条消息（系统提示 + 初始上下文）
        2. 保留最后一轮对话（最新交互）
        3. 中间消息按需删除

        Args:
            messages: 消息列表
            preserve_prefix: 保留前缀消息数量（默认 3）
        """
        total_tokens = sum(self.count_message_tokens(m) for m in messages)

        if total_tokens <= self.max_tokens:
            return messages

        # 保留前缀（系统提示 + 早期上下文）
        prefix = messages[:preserve_prefix]

        # 保留尾部（最新一轮对话，通常是最后 2-3 条）
        tail_start = len(messages) - 3
        tail = messages[tail_start:]

        # 计算剩余预算
        prefix_tokens = sum(self.count_message_tokens(m) for m in prefix)
        tail_tokens = sum(self.count_message_tokens(m) for m in tail)
        remaining_budget = self.max_tokens - prefix_tokens - tail_tokens

        # 从中间消息中选择（优先保留 AI 和 Tool 消息）
        middle = messages[preserve_prefix:tail_start]
        selected_middle = []
        middle_tokens = 0

        for msg in reversed(middle):  # 从后往前选择（更新的优先）
            msg_tokens = self.count_message_tokens(msg)
            if middle_tokens + msg_tokens <= remaining_budget:
                selected_middle.insert(0, msg)
                middle_tokens += msg_tokens

        return prefix + selected_middle + tail

    def validate_message_content(self, content: str) -> str:
        """验证和清理消息内容

        清理规则：
        - 移除过长的重复字符
        - 截断超长行
        - 验证 JSON 格式（如果是 JSON）
        """
        if not content:
            return ""

        # 移除连续重复超过 10 次的字符
        import re
        content = re.sub(r'(.)\1{10,}', r'\1' * 10, content)

        # 截断超长行（每行最多 2000 字符）
        lines = content.split('\n')
        lines = [line[:2000] + '...' if len(line) > 2000 else line
                 for line in lines]

        return '\n'.join(lines)
```

**优势**：
- ✅ 快速估算，无需调用 tiktoken
- ✅ 区分语言特征（中英文）
- ✅ 消息类型感知（System/AI/Tool）
- ✅ 前缀 + 尾部保留策略

**适用场景**：
- 多语言混合内容
- 需要快速预估 Token
- 消息列表动态增长

---

### 1.2 GPT-Researcher 的实现：嵌入式语义压缩

**核心思想**：使用 Embeddings 进行语义相似度过滤，保留与查询最相关的内容。

**实现代码**：`gpt-researcher/gpt_researcher/context/compression.py`

```python
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain_text_splitters import RecursiveCharacterTextSplitter

class ContextCompressor:
    """基于语义相似度的上下文压缩器"""

    def __init__(
        self,
        embeddings_provider,
        similarity_threshold: float = 0.75,
        chunk_size: int = 1000,
        chunk_overlap: int = 100
    ):
        self.embeddings_provider = embeddings_provider
        self.similarity_threshold = similarity_threshold

        # 文本分割器
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

        # 嵌入过滤器
        self.embeddings_filter = EmbeddingsFilter(
            embeddings=embeddings_provider,
            similarity_threshold=similarity_threshold
        )

    def compress(self, documents: List[str], query: str) -> List[str]:
        """压缩文档列表，保留与查询相关的部分

        流程：
        1. 分割文档为 chunks
        2. 为每个 chunk 生成 embedding
        3. 计算 chunk 与 query 的相似度
        4. 过滤掉相似度低于阈值的 chunks
        5. 拼接保留的 chunks

        Args:
            documents: 文档列表
            query: 查询字符串（用于相似度计算）

        Returns:
            压缩后的文档列表
        """
        if not documents:
            return []

        # 步骤 1: 分割文档
        all_chunks = []
        for doc in documents:
            chunks = self.splitter.split_text(doc)
            all_chunks.extend(chunks)

        # 步骤 2-4: 使用 EmbeddingsFilter 过滤
        from langchain.schema import Document
        chunk_docs = [Document(page_content=chunk) for chunk in all_chunks]
        filtered_docs = self.embeddings_filter.compress_documents(
            documents=chunk_docs,
            query=query
        )

        # 步骤 5: 拼接保留的内容
        compressed = [doc.page_content for doc in filtered_docs]

        return compressed

    def compress_to_max_tokens(
        self,
        documents: List[str],
        query: str,
        max_tokens: int
    ) -> str:
        """压缩文档直到满足 Token 限制

        策略：
        1. 先做语义压缩
        2. 如果仍超限，降低相似度阈值再压缩
        3. 如果还超限，截断内容
        """
        compressed_docs = self.compress(documents, query)
        compressed_text = "\n\n".join(compressed_docs)

        # 简单 Token 估算（1 token ≈ 4 chars）
        estimated_tokens = len(compressed_text) / 4

        if estimated_tokens <= max_tokens:
            return compressed_text

        # 降低阈值重试
        original_threshold = self.similarity_threshold
        self.similarity_threshold = 0.85  # 更严格
        compressed_docs = self.compress(documents, query)
        compressed_text = "\n\n".join(compressed_docs)
        self.similarity_threshold = original_threshold

        # 如果仍超限，截断
        max_chars = int(max_tokens * 4)
        if len(compressed_text) > max_chars:
            compressed_text = compressed_text[:max_chars] + "\n\n[Content truncated]"

        return compressed_text
```

**优势**：
- ✅ 语义感知（保留相关内容）
- ✅ 自动过滤噪音信息
- ✅ 可调节相似度阈值
- ✅ 递归分割策略

**适用场景**：
- 长文档压缩
- 需要保留语义相关性
- 查询导向的内容提取

---

### 1.3 当前 SNI Search 项目的实践

**当前实现**：`src/graph/nodes.py` - `synthesize_node` 函数

```python
# 当前简单截断策略
MAX_CONTEXT_CHARS = 15000

context_parts = []
# ... 收集各种来源的内容 ...

context = "\n\n".join(context_parts)

if len(context) > MAX_CONTEXT_CHARS:
    logger.warning(f"Context too large ({len(context)} chars), truncating")
    context = context[:MAX_CONTEXT_CHARS] + "\n\n[Context truncated]"
```

**问题**：
- ❌ 粗暴截断可能丢失关键信息
- ❌ 未考虑语义相关性
- ❌ 固定字符数限制不够灵活

**改进方向**：
1. 引入 Token 计数器（参考 Deer-Flow）
2. 实现优先级保留策略（Final > Round2 > Round1 > Initial）
3. 可选的语义压缩（参考 GPT-Researcher）

---

## 2. 配置管理（Configuration Management）

### 2.1 Deer-Flow 的实现：Dataclass + 环境变量

**核心思想**：使用 Python Dataclass 定义配置，支持环境变量覆盖，类型安全。

**实现代码**：`deer-flow/src/config/configuration.py`

```python
from dataclasses import dataclass, field
from typing import Optional
import os

@dataclass
class Configuration:
    """Deer-Flow 配置类"""

    # LLM 配置
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.1
    max_tokens: int = 4000

    # 工作流配置
    max_plan_iterations: int = 3
    max_search_results: int = 10
    enable_clarification: bool = False
    max_clarification_rounds: int = 3

    # 系统配置
    max_context_tokens: int = 100000
    locale: str = "en-US"
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Configuration":
        """从环境变量加载配置

        环境变量命名规则：
        - DEER_FLOW_LLM_MODEL
        - DEER_FLOW_MAX_TOKENS
        - DEER_FLOW_ENABLE_CLARIFICATION
        """
        config = cls()

        # 字符串类型
        if model := os.getenv("DEER_FLOW_LLM_MODEL"):
            config.llm_model = model

        # 数值类型（需要类型转换）
        if temp := os.getenv("DEER_FLOW_LLM_TEMPERATURE"):
            config.llm_temperature = float(temp)

        if max_tokens := os.getenv("DEER_FLOW_MAX_TOKENS"):
            config.max_tokens = int(max_tokens)

        # 布尔类型（字符串转布尔）
        if clarification := os.getenv("DEER_FLOW_ENABLE_CLARIFICATION"):
            config.enable_clarification = clarification.lower() in ("true", "1", "yes")

        return config

    @classmethod
    def from_runnable_config(cls, runnable_config: dict) -> "Configuration":
        """从 LangGraph RunnableConfig 加载

        支持从 LangGraph 的配置对象中提取参数
        """
        config = cls()
        configurable = runnable_config.get("configurable", {})

        # 从 configurable 字段提取
        config.llm_model = configurable.get("llm_model", config.llm_model)
        config.max_tokens = configurable.get("max_tokens", config.max_tokens)
        config.locale = configurable.get("locale", config.locale)

        return config

    def validate(self) -> None:
        """验证配置有效性"""
        if self.max_plan_iterations < 1:
            raise ValueError("max_plan_iterations must be >= 1")

        if self.llm_temperature < 0 or self.llm_temperature > 2:
            raise ValueError("llm_temperature must be in [0, 2]")

        if self.max_context_tokens < 1000:
            raise ValueError("max_context_tokens must be >= 1000")
```

**优势**：
- ✅ 类型安全（IDE 自动补全）
- ✅ 默认值清晰
- ✅ 环境变量覆盖
- ✅ 验证逻辑内置

**适用场景**：
- Python 原生应用
- 需要类型检查
- 配置项不频繁变更

---

### 2.2 GPT-Researcher 的实现：JSON + 动态加载

**核心思想**：使用 JSON 文件存储配置，支持运行时动态加载，处理弃用属性。

**实现代码**：`gpt-researcher/gpt_researcher/config/config.py`

```python
import json
import os
from typing import Any, Dict, Optional
import warnings

class Config:
    """GPT-Researcher 配置类"""

    CONFIG_DIR = os.path.expanduser("~/.gpt_researcher")
    CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

    # 默认配置
    DEFAULT_CONFIG = {
        "llm_provider": "openai",
        "fast_llm": "gpt-4o-mini",
        "smart_llm": "gpt-4o",
        "strategic_llm": "o1-preview",
        "embedding_provider": "openai",
        "embedding_model": "text-embedding-3-small",
        "retriever": "tavily",
        "max_search_results": 10,
        "max_iterations": 3,
        "report_format": "markdown",
        "doc_path": "./my-docs"
    }

    # 弃用属性映射
    DEPRECATED_ATTRS = {
        "llm": "fast_llm",
        "openai_api_key": "Use OPENAI_API_KEY env var instead"
    }

    def __init__(self, config_file: Optional[str] = None):
        """初始化配置

        加载顺序（优先级从高到低）：
        1. 环境变量
        2. 指定的配置文件
        3. 默认配置文件 ~/.gpt_researcher/config.json
        4. 内置默认值
        """
        # 从默认值开始
        self._config = self.DEFAULT_CONFIG.copy()

        # 加载文件配置
        config_path = config_file or self.CONFIG_FILE
        if os.path.exists(config_path):
            with open(config_path) as f:
                file_config = json.load(f)
                self._config.update(file_config)

        # 环境变量覆盖（最高优先级）
        self._load_from_env()

    def _load_from_env(self):
        """从环境变量加载配置"""
        env_mapping = {
            "OPENAI_API_KEY": "openai_api_key",
            "FAST_LLM": "fast_llm",
            "SMART_LLM": "smart_llm",
            "RETRIEVER": "retriever",
            "MAX_SEARCH_RESULTS": "max_search_results",
            "TAVILY_API_KEY": "tavily_api_key"
        }

        for env_key, config_key in env_mapping.items():
            if value := os.getenv(env_key):
                # 类型转换
                if config_key in ("max_search_results", "max_iterations"):
                    value = int(value)
                self._config[config_key] = value

    def __getattr__(self, name: str) -> Any:
        """动态属性访问

        支持：
        - config.fast_llm
        - config.max_search_results

        处理弃用属性警告
        """
        # 检查是否是弃用属性
        if name in self.DEPRECATED_ATTRS:
            new_attr = self.DEPRECATED_ATTRS[name]
            warnings.warn(
                f"'{name}' is deprecated. {new_attr}",
                DeprecationWarning,
                stacklevel=2
            )
            # 如果有映射，返回新属性
            if not new_attr.startswith("Use "):
                return getattr(self, new_attr)

        # 从配置字典获取
        if name in self._config:
            return self._config[name]

        raise AttributeError(f"Config has no attribute '{name}'")

    def get(self, key: str, default: Any = None) -> Any:
        """字典式访问"""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """运行时修改配置"""
        self._config[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return self._config.copy()

    def save(self, path: Optional[str] = None) -> None:
        """保存配置到文件"""
        save_path = path or self.CONFIG_FILE

        # 确保目录存在
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        with open(save_path, 'w') as f:
            json.dump(self._config, f, indent=2)
```

**优势**：
- ✅ 运行时动态修改
- ✅ JSON 格式易读易编辑
- ✅ 弃用属性处理
- ✅ 多级覆盖（默认 → 文件 → 环境变量）

**适用场景**：
- 用户需要修改配置文件
- 配置项经常变更
- 需要持久化用户设置

---

### 2.3 当前 SNI Search 项目的实践

**当前实现**：`src/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Keys
    OPENAI_API_KEY: str
    TAVILY_API_KEY: str
    QDRANT_URL: str = "http://localhost:6333"

    # Search Settings
    MAX_SEARCH_RESULTS: int = 3

    class Config:
        env_file = ".env"

settings = Settings()
```

**优势**：
- ✅ Pydantic 类型验证
- ✅ 自动从 .env 加载
- ✅ 简洁易用

**改进方向**：
1. 添加配置验证逻辑（参考 Deer-Flow）
2. 支持多级配置文件（参考 GPT-Researcher）
3. 添加弃用属性处理
4. 支持运行时配置修改

---

## 3. 日志系统（Logging System）

### 3.1 GPT-Researcher 的实现：彩色日志

**核心思想**：使用 `click` 库实现彩色输出，区分不同日志级别，自定义日志格式。

**实现代码**：`gpt-researcher/gpt_researcher/utils/logger.py`

```python
import logging
import sys
from typing import Literal
import click

TRACE_LOG_LEVEL = 5

class ColourizedFormatter(logging.Formatter):
    """彩色日志格式化器"""

    level_name_colors = {
        5: lambda level_name: click.style(str(level_name), fg="blue"),      # TRACE
        logging.DEBUG: lambda level_name: click.style(str(level_name), fg="cyan"),
        logging.INFO: lambda level_name: click.style(str(level_name), fg="green"),
        logging.WARNING: lambda level_name: click.style(str(level_name), fg="yellow"),
        logging.ERROR: lambda level_name: click.style(str(level_name), fg="red"),
        logging.CRITICAL: lambda level_name: click.style(str(level_name), fg="bright_red"),
    }

    def __init__(self, fmt: str = None, datefmt: str = None, use_colors: bool = None):
        # 自动检测是否支持颜色（TTY）
        if use_colors is None:
            self.use_colors = sys.stdout.isatty()
        else:
            self.use_colors = use_colors

        super().__init__(fmt=fmt, datefmt=datefmt)

    def formatMessage(self, record: logging.LogRecord) -> str:
        """格式化消息"""
        from copy import copy
        recordcopy = copy(record)
        levelname = recordcopy.levelname

        # 对齐（补空格）
        separator = " " * (8 - len(recordcopy.levelname))

        if self.use_colors:
            # 应用颜色
            levelname = self.level_name_colors.get(
                recordcopy.levelno,
                lambda x: x
            )(levelname)

            # 支持 color_message（自定义彩色消息）
            if "color_message" in recordcopy.__dict__:
                recordcopy.msg = recordcopy.__dict__["color_message"]

        recordcopy.__dict__["levelprefix"] = levelname + ":" + separator

        return super().formatMessage(recordcopy)


def get_formatted_logger(name: str = "scraper"):
    """获取格式化日志器"""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 避免重复添加 handler
    if not logger.handlers:
        handler = logging.StreamHandler()

        formatter = ColourizedFormatter(
            "%(levelprefix)s [%(asctime)s] %(message)s",
            datefmt="%H:%M:%S"
        )

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # 禁止传播到父 logger（避免重复日志）
    logger.propagate = False

    return logger
```

**使用示例**：
```python
logger = get_formatted_logger("sni_search")

logger.debug("Debugging information")       # 青色
logger.info("Normal operation")             # 绿色
logger.warning("Warning message")           # 黄色
logger.error("Error occurred")              # 红色
logger.critical("Critical failure")         # 亮红色
```

**优势**：
- ✅ 视觉区分（颜色编码）
- ✅ 自动检测 TTY（终端 vs 文件）
- ✅ 自定义日志级别（TRACE）
- ✅ 防止重复日志

---

### 3.2 Deer-Flow 的实践：节点前缀日志

**实现模式**：在每个节点函数中使用节点名作为日志前缀

```python
# deer-flow/src/agents/coordinator.py
logger.info(f"[coordinator] Detected locale: {locale}")
logger.info(f"[coordinator] Research topic: {topic}")

# deer-flow/src/agents/planner.py
logger.info(f"[planner] Generated {len(plan.steps)} steps")
logger.info(f"[planner] Plan validation: {is_valid}")
```

**优势**：
- ✅ 易于追踪执行流程
- ✅ 快速定位日志来源
- ✅ 便于调试多节点工作流

---

### 3.3 当前 SNI Search 项目的实践

**当前实现**：
```python
# src/graph/nodes.py
logger = logging.getLogger(__name__)

logger.info(f"[round1_planning_node] Generating round 1 queries")
logger.info(f"[round2_planning_node] Discovered organization: {org}")
```

**优势**：
- ✅ 已使用节点前缀
- ✅ 结构化日志

**改进方向**：
1. 引入彩色日志（参考 GPT-Researcher）
2. 添加性能日志（执行时间）
3. 支持日志级别动态调整
4. 添加日志文件输出（除了控制台）

---

## 4. 工具抽象（Tool Abstraction）

### 4.1 GPT-Researcher 的实现：注册表模式

**核心思想**：使用注册表模式管理多个工具实现，支持默认值和回退机制。

**实现代码**：`gpt-researcher/gpt_researcher/actions/retriever.py`

```python
def get_retriever(retriever: str):
    """获取检索器实现

    使用 match-case 模式注册所有支持的检索器
    """
    match retriever:
        case "google":
            from gpt_researcher.retrievers import GoogleSearch
            return GoogleSearch
        case "tavily":
            from gpt_researcher.retrievers import TavilySearch
            return TavilySearch
        case "duckduckgo":
            from gpt_researcher.retrievers import Duckduckgo
            return Duckduckgo
        case "bing":
            from gpt_researcher.retrievers import BingSearch
            return BingSearch
        case "custom":
            from gpt_researcher.retrievers import CustomRetriever
            return CustomRetriever
        case _:
            return None  # 未知检索器


def get_default_retriever():
    """默认检索器"""
    from gpt_researcher.retrievers import TavilySearch
    return TavilySearch


def get_retrievers(headers: dict, cfg) -> list:
    """根据配置获取检索器列表

    优先级（从高到低）：
    1. HTTP Header: retrievers (多个，逗号分隔)
    2. HTTP Header: retriever (单个)
    3. Config: retrievers (列表或逗号分隔字符串)
    4. Config: retriever (单个)
    5. 默认：TavilySearch

    Args:
        headers: HTTP 请求头
        cfg: 配置对象

    Returns:
        检索器类列表
    """
    # 1. 从 headers 获取多个检索器
    if headers.get("retrievers"):
        retrievers = headers.get("retrievers").split(",")

    # 2. 从 headers 获取单个检索器
    elif headers.get("retriever"):
        retrievers = [headers.get("retriever")]

    # 3. 从配置获取多个检索器
    elif cfg.retrievers:
        if isinstance(cfg.retrievers, str):
            retrievers = cfg.retrievers.split(",")
        else:
            retrievers = cfg.retrievers
        retrievers = [r.strip() for r in retrievers]

    # 4. 从配置获取单个检索器
    elif cfg.retriever:
        retrievers = [cfg.retriever]

    # 5. 使用默认检索器
    else:
        retrievers = [get_default_retriever().__name__]

    # 转换为类，无效的使用默认值
    retriever_classes = [
        get_retriever(r) or get_default_retriever()
        for r in retrievers
    ]

    return retriever_classes
```

**使用示例**：
```python
# 示例 1: 单个检索器
cfg = Config(retriever="tavily")
retrievers = get_retrievers({}, cfg)
# 结果: [TavilySearch]

# 示例 2: 多个检索器
cfg = Config(retrievers="tavily,google,duckduckgo")
retrievers = get_retrievers({}, cfg)
# 结果: [TavilySearch, GoogleSearch, Duckduckgo]

# 示例 3: HTTP Header 覆盖
headers = {"retriever": "bing"}
retrievers = get_retrievers(headers, cfg)
# 结果: [BingSearch]

# 示例 4: 无效检索器回退
cfg = Config(retriever="invalid_name")
retrievers = get_retrievers({}, cfg)
# 结果: [TavilySearch] (回退到默认)
```

**优势**：
- ✅ 懒加载（用到才导入）
- ✅ 多优先级支持
- ✅ 自动回退机制
- ✅ 易于扩展新检索器

---

### 4.2 当前 SNI Search 项目的实践

**当前实现**：`src/tools/__init__.py`

```python
from src.tools.sni_tools import SNITools
from src.tools.web_search import get_web_search_tool
from src.tools.crawler import Crawler, crawl_tool

__all__ = ["SNITools", "get_web_search_tool", "Crawler", "crawl_tool"]
```

**问题**：
- ❌ 硬编码工具导入
- ❌ 无法动态切换实现
- ❌ 无回退机制

**改进方向**：
1. 实现工具注册表（参考 GPT-Researcher）
2. 支持多个搜索引擎（Tavily, Google, Bing）
3. 添加工具回退机制
4. 支持配置驱动的工具选择

---

## 5. 状态管理（State Management）

### 5.1 Deer-Flow 的实现：扩展 MessagesState

**核心思想**：继承 LangGraph 的 `MessagesState`，添加工作流特定字段，支持功能开关。

**实现代码**：`deer-flow/src/graph/types.py`

```python
from dataclasses import field
from langgraph.graph import MessagesState
from typing import Optional, List

class State(MessagesState):
    """Deer-Flow 工作流状态

    继承 MessagesState 获得：
    - messages: List[BaseMessage] (消息历史)

    添加自定义字段：
    - 运行时变量
    - 功能开关
    - 工作流控制
    """

    # ========== 运行时变量 ==========
    locale: str = "en-US"
    research_topic: str = ""
    clarified_research_topic: str = ""
    observations: list[str] = []
    resources: list[Resource] = []
    plan_iterations: int = 0
    current_plan: Plan | str = None
    final_report: str = ""
    auto_accepted_plan: bool = False
    enable_background_investigation: bool = True
    background_investigation_results: str = None

    # ========== 功能开关（Feature Flags）==========
    enable_clarification: bool = False  # 是否启用澄清功能
    max_clarification_rounds: int = 3   # 最大澄清轮数

    # ========== 澄清状态追踪 ==========
    clarification_rounds: int = 0
    clarification_history: list[str] = field(default_factory=list)
    is_clarification_complete: bool = False

    # ========== 工作流控制 ==========
    goto: str = "planner"  # 下一个节点（默认 planner）
```

**使用示例**：
```python
# 初始化状态
initial_state = State(
    research_topic="What is LangGraph?",
    locale="en-US",
    enable_clarification=True,  # 启用澄清功能
    max_clarification_rounds=2
)

# 工作流中读取状态
def planner_node(state: State):
    topic = state.clarified_research_topic or state.research_topic
    if state.enable_clarification and not state.is_clarification_complete:
        # 需要澄清
        return {"goto": "clarifier"}

    # 正常规划
    plan = generate_plan(topic)
    return {"current_plan": plan, "goto": "researcher"}
```

**优势**：
- ✅ 类型安全（继承 MessagesState）
- ✅ 功能开关（Feature Flags）
- ✅ 工作流控制（goto）
- ✅ 清晰的字段分组

---

### 5.2 当前 SNI Search 项目的实践

**当前实现**：`src/graph/state.py`

```python
from typing import TypedDict, List, Optional, Dict, Any

class SNIAgentState(TypedDict):
    # 消息历史
    messages: List[BaseMessage]

    # 输入
    query: str
    locale: str

    # 搜索结果
    sni_exact_results: Optional[Dict[str, Any]]
    sni_vector_results: Optional[List[Dict[str, Any]]]
    initial_search_result: Optional[str]

    # Round 1
    extracted_keywords: Optional[List[str]]
    enhanced_query: Optional[str]
    round1_queries: Optional[List[str]]
    round1_results: Optional[List[Dict[str, Any]]]

    # Round 2
    round2_keywords: Optional[List[str]]
    round2_results: Optional[List[Dict[str, Any]]]

    # Final
    final_search_query: Optional[str]
    final_search_result: Optional[str]
    final_answer: Optional[str]
```

**优势**：
- ✅ 清晰的阶段划分
- ✅ Optional 字段支持不同路径

**改进方向**：
1. 继承 MessagesState（参考 Deer-Flow）
2. 添加功能开关（enable_vector_search, skip_web_search）
3. 添加工作流控制字段（goto）
4. 添加统计信息（total_searches, execution_time）

---

## 6. 错误处理（Error Handling）

### 6.1 Deer-Flow 的实践：消息内容验证

**实现模式**：在 ContextManager 中验证消息内容

```python
def validate_message_content(content: str) -> str:
    """验证和清理消息内容

    清理规则：
    1. 移除过长的重复字符（防止垃圾数据）
    2. 截断超长行（防止格式错误）
    3. 验证 JSON 格式（如果是 JSON）
    """
    if not content:
        return ""

    import re

    # 移除连续重复超过 10 次的字符
    content = re.sub(r'(.)\1{10,}', r'\1' * 10, content)

    # 截断超长行
    lines = content.split('\n')
    lines = [line[:2000] + '...' if len(line) > 2000 else line
             for line in lines]

    return '\n'.join(lines)
```

---

### 6.2 GPT-Researcher 的实践：多级回退策略

**实现模式**：在压缩器中实现递进式回退

```python
def compress_to_max_tokens(documents, query, max_tokens):
    """压缩文档直到满足限制

    回退策略：
    1. 尝试标准压缩（相似度阈值 0.75）
    2. 如果超限，提高阈值（0.85）重试
    3. 如果仍超限，硬截断
    4. 添加截断标记
    """
    try:
        # Level 1: 标准压缩
        compressed = self.compress(documents, query)
        text = "\n\n".join(compressed)

        if estimate_tokens(text) <= max_tokens:
            return text

        # Level 2: 更严格的过滤
        self.similarity_threshold = 0.85
        compressed = self.compress(documents, query)
        text = "\n\n".join(compressed)
        self.similarity_threshold = 0.75  # 恢复

        if estimate_tokens(text) <= max_tokens:
            return text

        # Level 3: 硬截断
        max_chars = int(max_tokens * 4)
        return text[:max_chars] + "\n\n[Content truncated]"

    except Exception as e:
        logger.error(f"Compression failed: {e}")
        # Level 4: 返回空字符串（最后的回退）
        return ""
```

---

### 6.3 当前 SNI Search 项目的实践

**当前实现**：简单 try-except

```python
try:
    result = await web_search_tool.ainvoke(query)
    return {"query": query, "result": result, "success": True}
except Exception as e:
    logger.error(f"Search failed: {e}")
    return {"query": query, "error": str(e), "success": False}
```

**改进方向**：
1. 实现重试机制（指数退避）
2. 添加超时控制
3. 分级错误处理（网络错误 vs API 错误）
4. 添加错误统计和监控

---

## 7. 实施建议（Implementation Recommendations）

基于以上分析，为 SNI Search 项目提供以下改进建议，按优先级排序：

### 7.1 高优先级 🔴

**1. 改进上下文管理**
- **目标**：避免粗暴截断，保留关键信息
- **方案**：
  - 实现 Token 计数器（参考 Deer-Flow 字符级估算）
  - 实现优先级保留策略（Final > Round2 > Round1 > Initial）
  - 添加内容验证和清理
- **工作量**：中等（1-2 天）
- **收益**：显著提升合成质量

**2. 添加工具注册表**
- **目标**：支持多个搜索引擎，提高灵活性
- **方案**：
  - 实现 `get_search_tool(name)` 注册表
  - 支持配置驱动的工具选择
  - 添加回退机制
- **工作量**：中等（1-2 天）
- **收益**：提高系统可扩展性和鲁棒性

**3. 增强错误处理**
- **目标**：提高系统稳定性
- **方案**：
  - 添加重试机制（指数退避）
  - 实现超时控制
  - 分级错误处理
- **工作量**：中等（2-3 天）
- **收益**：显著降低失败率

---

### 7.2 中优先级 🟡

**4. 引入彩色日志**
- **目标**：改善开发体验
- **方案**：
  - 集成 `click` 彩色输出
  - 添加性能日志
  - 支持日志文件输出
- **工作量**：低（0.5-1 天）
- **收益**：提升调试效率

**5. 优化配置管理**
- **目标**：更灵活的配置系统
- **方案**：
  - 添加配置验证
  - 支持多级配置文件
  - 添加弃用属性处理
- **工作量**：低（1 天）
- **收益**：提高配置可维护性

**6. 扩展状态管理**
- **目标**：更好的工作流控制
- **方案**：
  - 继承 MessagesState
  - 添加功能开关
  - 添加统计信息
- **工作量**：中等（1-2 天）
- **收益**：提升工作流灵活性

---

### 7.3 低优先级 🟢

**7. 实现语义压缩**（可选）
- **目标**：更智能的内容过滤
- **方案**：
  - 集成 EmbeddingsFilter
  - 实现相似度过滤
- **工作量**：高（3-5 天）
- **收益**：提升内容相关性（但增加复杂度）

**8. 添加性能监控**
- **目标**：量化系统性能
- **方案**：
  - 记录各阶段执行时间
  - 统计 API 调用次数
  - 生成性能报告
- **工作量**：中等（2-3 天）
- **收益**：发现性能瓶颈

---

## 8. 总结对比

| 维度 | Deer-Flow | GPT-Researcher | SNI Search (当前) | 改进方向 |
|------|-----------|----------------|------------------|---------|
| **上下文管理** | 字符级 Token 计数 + 前缀保留 | 嵌入式语义压缩 | 简单截断 | ✅ 实现 Token 计数 + 优先级保留 |
| **配置管理** | Dataclass + 环境变量 | JSON + 动态加载 | Pydantic Settings | ✅ 添加验证 + 多级配置 |
| **日志系统** | 节点前缀 | 彩色日志 + 自定义级别 | 节点前缀 | ✅ 添加彩色输出 + 性能日志 |
| **工具抽象** | 基础 | 注册表 + 多优先级 | 硬编码 | ✅ 实现注册表 + 回退机制 |
| **状态管理** | MessagesState 扩展 + 功能开关 | 自定义内存 | TypedDict | ✅ 继承 MessagesState + Feature Flags |
| **错误处理** | 内容验证 | 多级回退 | 简单 try-except | ✅ 重试 + 超时 + 分级处理 |

---

## 9. 快速实施路线图

**Week 1: 核心改进**
- Day 1-2: 实现 Token 计数器和优先级保留策略
- Day 3-4: 添加工具注册表和回退机制
- Day 5: 增强错误处理（重试 + 超时）

**Week 2: 体验优化**
- Day 1: 引入彩色日志
- Day 2-3: 优化配置管理（验证 + 多级配置）
- Day 4: 扩展状态管理（Feature Flags）
- Day 5: 测试和文档

**Week 3: 可选增强**
- Day 1-3: 实现语义压缩（如果需要）
- Day 4-5: 添加性能监控

---

## 10. 参考资源

**Deer-Flow**:
- Context Manager: `deer-flow/src/utils/context_manager.py`
- Configuration: `deer-flow/src/config/configuration.py`
- State Types: `deer-flow/src/graph/types.py`

**GPT-Researcher**:
- Context Compression: `gpt-researcher/gpt_researcher/context/compression.py`
- Config Management: `gpt-researcher/gpt_researcher/config/config.py`
- Logger: `gpt-researcher/gpt_researcher/utils/logger.py`
- Retriever: `gpt-researcher/gpt_researcher/actions/retriever.py`

**LangGraph 官方文档**:
- MessagesState: https://langchain-ai.github.io/langgraph/reference/graphs/#langgraph.graph.MessagesState
- Checkpointing: https://langchain-ai.github.io/langgraph/concepts/persistence/
- Streaming: https://langchain-ai.github.io/langgraph/concepts/streaming/

---

通过有选择性地吸收这些工程化实践，SNI Search 项目可以在保持当前创新特色的同时，显著提升系统的鲁棒性、可维护性和用户体验。
