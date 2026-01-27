# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SNI Recognition System using LangGraph and RAG (Retrieval-Augmented Generation).

**Key Technologies:**
- Python ≥3.11 required
- Package manager: `uv` (modern pip alternative)
- LangGraph for deterministic workflow orchestration
- Qdrant vector database for semantic search
- Multi-provider LLM support (Claude/OpenAI)
- Multi-language prompt system (English/Chinese)

## Essential Commands

### Setup & Installation

```bash
# Install all dependencies
uv sync

# Install including dev dependencies
uv sync --all-groups

# Create environment configuration
cp .env.example .env
# Edit .env with your API keys and configuration
```

### Running the System

**Start Required Services:**
```bash
# Start Qdrant vector database (required)
docker run -p 6333:6333 qdrant/qdrant
```

**Initialize Data:**
```bash
# Initialize TGT standard library collection (optional)
uv run python scripts/init_tgt_library.py

# Import SNI data (if you have data)
uv run python -m src.import_data --data-dir ./results

# Download embedding model for offline use (optional)
uv run python scripts/download_embedding_model.py
```

**Start API Server:**
```bash
# Run the FastAPI server
uv run python -m src.api_server
# Server will start at http://0.0.0.0:8000 (or configured port)
```

**Run Demo:**
```bash
# Test multi-round search workflow
uv run python demo/test_multi_round_search.py
```

### Testing

```bash
uv run pytest tests/
```

## High-Level Architecture

### Core Innovation: Deterministic LangGraph Workflow

This system implements a **4-2-1 multi-round search strategy** where flow control is **100% Python code** (NO LLM decision-making for routing). This design achieves:
- 40%+ reduction in token usage vs traditional agent patterns
- Predictable, debuggable execution flow
- Reliable multi-step orchestration

### Workflow Structure

```
User Query
    ↓
[1] Exact Match Search (Qdrant)
    ↓ (if no match)
[2] Vector Similarity Search (Qdrant)
    ↓
[3] Initial Web Search (direct SNI domain crawl)
    ↓
[4] Keyword Extraction (LLM analyzes vector + web results)
    ↓
[5] Round 1 Planning (LLM generates 4 diverse queries)
    ↓
[6] Round 1 Execution (4 parallel web searches)
    ↓
[7] Round 2 Planning (LLM extracts 2 focused keywords)
    ↓
[8] Round 2 Execution (2 parallel web searches)
    ↓
[9] Final Search Planning (LLM generates comprehensive query)
    ↓
[10] Final Search Execution (1 verification search)
    ↓
[11] Synthesis (LLM consolidates all sources → structured JSON answer)
    ↓
[12] TGT Standardization (entity canonicalization)
```

**Total: Up to 8 web searches** (1 initial + 4 round1 + 2 round2 + 1 final)

### 12 Workflow Nodes

Defined in `src/graph/nodes.py`:

1. `sni_exact_query_node` - Exact match lookup in Qdrant
2. `sni_vector_query_node` - Vector similarity search
3. `initial_web_search_node` - Direct SNI domain crawl
4. `keyword_extraction_node` - LLM extracts keywords from results
5. `round1_planning_node` - LLM generates 4 diverse search queries
6. `round1_parallel_search_node` - Execute 4 searches in parallel
7. `round2_planning_node` - LLM extracts 2 focused keywords from R1
8. `round2_parallel_search_node` - Execute 2 searches in parallel
9. `final_search_planning_node` - LLM generates final verification query
10. `final_search_node` - Execute final comprehensive search
11. `synthesize_node` - LLM consolidates all data into structured answer
12. `tgt_standardization_node` - Canonicalize entity names

### State Management

**State Schema:** `src/graph/state.py`

- `SNIAgentState` is a TypedDict with 20+ fields
- Each node returns a dictionary of only changed fields
- LangGraph automatically merges updates into state
- Immutable pattern: nodes never mutate state directly

**Key State Fields:**
- `query`: Original user query
- `sni_exact_results`, `sni_vector_results`: Database search results
- `initial_search_result`: Direct SNI web search
- `round1_queries`, `round1_results`: First round parallel searches
- `round2_keywords`, `round2_results`: Second round focused searches
- `final_search_query`, `final_search_result`: Final verification
- `final_answer`: Synthesized JSON answer
- `tgt_metadata`: Entity standardization metadata

## Code Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│ API Layer                                               │
│ src/api_server.py - FastAPI + SSE streaming             │
└───────────────────────┬─────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Agent Layer                                             │
│ src/agent.py - SNIAgent (sync/async/streaming)          │
└───────────────────────┬─────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Workflow Layer (LangGraph)                              │
│ ├─ src/graph/builder.py - Graph construction            │
│ ├─ src/graph/nodes.py - 12 node implementations         │
│ └─ src/graph/state.py - State schema (TypedDict)        │
└───────────────────────┬─────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Tools Layer                                             │
│ ├─ src/tools/sni_tools.py - Qdrant queries              │
│ ├─ src/tools/search.py - Web search engines             │
│ ├─ src/tools/crawl.py - Web content extraction          │
│ ├─ src/tools/tgt_library.py - Entity canonicalization   │
│ └─ src/prompts/ - Multi-language Jinja2 templates       │
└─────────────────────────────────────────────────────────┘
```

## Key Patterns & Conventions

### 1. Multi-Language Prompt System

**Location:** `src/prompts/`

**Pattern:**
- Base template: `keyword_extraction.md` (English)
- Locale variant: `keyword_extraction.zh_CN.md` (Chinese)
- Jinja2 variables for dynamic content
- Runtime selection via `locale` parameter
- Auto-fallback to English if locale variant missing

**Example:**
```python
# In nodes.py
prompt_template = get_prompt_template("keyword_extraction", locale="zh-CN")
rendered = prompt_template.render(context=context_data)
```

### 2. Pluggable Tool Architecture

**LLM Providers:**
- Configured via `LLM_PROVIDER` environment variable
- Supported: `claude` (default), `openai`
- Model selection via `CLAUDE_MODEL` or `OPENAI_MODEL`

**Search Engines:**
- Configured via `SEARCH_API` environment variable
- Supported: `tavily`, `duckduckgo`, `searchapi`, `infoquest`, `brave`, `serper`, `wikipedia`, `arxiv`, `searx`
- DuckDuckGo requires no API key (good for testing)

**Crawlers:**
- Configured via `CRAWLER_ENGINE` environment variable
- Supported: `jina` (default), `infoquest`
- Jina Reader works without API key (rate-limited)

**Embedding Models:**
- Any SentenceTransformer-compatible model
- Online: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- Local: Download with `scripts/download_embedding_model.py`

### 3. Configuration Hierarchy

Configuration is loaded in this priority order:

1. **Environment variables** (highest priority)
2. **`.env` file** (API keys, secrets)
3. **`conf.yaml`** (search engine parameters, crawler settings)
4. **`src/config.py`** (Pydantic validation, defaults)

**Critical Environment Variables:**
```bash
# Required
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=sni_domain_mapping
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=your-key
CLAUDE_MODEL=claude-sonnet-4-5-20250929
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
SEARCH_API=duckduckgo
CRAWLER_ENGINE=jina
DATA_DIR=./results

# Optional
QDRANT_TGT_COLLECTION=tgt_standard_library
TGT_LIBRARY_ENABLED=true
API_HOST=0.0.0.0
API_PORT=8000
```

### 4. Conditional Flow Functions

**Location:** `src/graph/builder.py`

**Key Pattern:** Pure Python functions determine routing (NO LLM calls)

**Example:**
```python
def should_try_vector_search(state: SNIAgentState) -> str:
    """Decide whether to use vector search or go directly to synthesis."""
    if state.get("sni_exact_results"):
        return "synthesize"  # Found exact match
    return "vector_search"  # Need to search
```

**Benefits:**
- Predictable flow
- Fast execution (no API calls)
- Easy to debug
- Cost-efficient

### 5. Parallel Execution Pattern

**Implementation:** `asyncio.Semaphore` for concurrency control

**Round 1 (4 parallel searches):**
```python
sem = asyncio.Semaphore(4)
tasks = [search_with_semaphore(query, sem) for query in round1_queries]
results = await asyncio.gather(*tasks)
```

**Round 2 (2 parallel searches):**
```python
sem = asyncio.Semaphore(2)
tasks = [search_with_semaphore(keyword, sem) for keyword in round2_keywords]
results = await asyncio.gather(*tasks)
```

**Benefits:** Significant latency reduction (4-5x faster than sequential)

### 6. Domain Decomposition Strategy

**SNI Format:** `prefix.suffix` (e.g., `shuc-pc-hunt.ksord.com`)

**Analysis Approach:**
- **Suffix** (e.g., `ksord.com`): Organization identifier → Round 1 focus
- **Prefix** (e.g., `shuc-pc-hunt`): Service/product details → Round 2 focus

This strategy mirrors human research approach: first identify the organization, then understand the specific service.

### 7. Content Truncation

**Implementation:** `safe_truncate()` function in `src/tools/search_postprocessor.py`

**Features:**
- Multi-byte safe (UTF-8 compatible)
- Critical for Chinese/Japanese/Korean text
- Default cap: 15,000 characters per input
- Prevents token overflow in LLM context

**Configuration:**
```python
# src/config.py
MAX_CONTEXT_CHARS = 500000  # Total context limit (~150K tokens)
```

### 8. Keyword Extraction Philosophy

**Aggressive Filtering (defined in prompts):**

**Exclude:**
- HTTP error codes (404, 502, etc.)
- Web server software (Nginx, Apache)
- Generic terms (website, service)

**Include:**
- Company/organization names
- Product names
- Service identifiers
- Domain-specific terminology

**Prompt Guidance:** "Does this keyword help identify the TARGET SNI?"

## API Endpoints

**Base URL:** `http://localhost:8000` (configurable via `API_HOST` and `API_PORT`)

### Main Endpoints

```
POST /query
  - Full SNI query with optional SSE streaming
  - Body: {"query": "example.com", "locale": "en-US"}
  - Returns: JSON answer or SSE stream

POST /tools/exact
  - Direct exact search in Qdrant
  - Body: {"sni": "example.com"}

POST /tools/vector
  - Direct vector similarity search
  - Body: {"query": "example service"}

POST /tools/domain
  - Search by domain
  - Body: {"domain": "example.com"}

GET /health
  - Health check endpoint
  - Returns: {"status": "ok"}
```

### Streaming (SSE)

**Pattern:**
```javascript
const eventSource = new EventSource('/query?stream=true');
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Node: ${data.node}, Status: ${data.status}`);
};
```

**Event Types:**
- `node_start`: Node execution begins
- `node_end`: Node execution completes
- `final_answer`: Complete answer ready

## Critical Dependencies

### Required Services

1. **Qdrant Vector Database**
   - Must be running before starting application
   - Default: `http://localhost:6333`
   - Start with: `docker run -p 6333:6333 qdrant/qdrant`

2. **LLM API**
   - Either Anthropic (Claude) or OpenAI API key required
   - Claude recommended for best performance

### Required Python Packages

See `pyproject.toml` for full list. Key dependencies:
- `langgraph>=0.2.0` - Workflow orchestration
- `langchain-anthropic>=0.3.0` - Claude integration
- `qdrant-client>=1.12.0` - Vector database client
- `sentence-transformers>=3.0.0` - Embeddings
- `fastapi>=0.115.0` - API server
- `sse-starlette>=2.1.0` - Server-sent events

## File Organization Conventions

### Naming Patterns

- `*_node` - Workflow node functions (in `src/graph/nodes.py`)
- `*_search` - Search functions (in `src/tools/search.py`)
- `*_extraction` - Data extraction functions
- `*_planning` - Query planning nodes (LLM-driven)

### Module Structure

```
src/
├── agent.py                    # High-level user interface
├── api_server.py              # FastAPI HTTP service
├── config.py                  # Centralized configuration
├── import_data.py             # Data import utilities
├── graph/
│   ├── builder.py             # LangGraph workflow construction
│   ├── nodes.py               # 12 node implementations
│   └── state.py               # State schema (TypedDict)
├── prompts/
│   ├── template.py            # Template loader
│   ├── keyword_extraction.md  # Base English template
│   ├── keyword_extraction.zh_CN.md  # Chinese variant
│   └── [other prompts...]     # Multi-language prompts
└── tools/
    ├── sni_tools.py           # Qdrant queries
    ├── search.py              # Web search engines
    ├── crawl.py               # Web content extraction
    ├── tgt_library.py         # Entity canonicalization
    └── [search/crawler modules...]
```

## Modification Guidelines

### When Modifying Workflow

**Critical Rules:**
1. **Flow control MUST remain Python-based** - No LLM routing decisions
2. **Read existing prompt templates** before changing node logic
3. **Maintain state immutability** - Return dicts, don't mutate state
4. **All tools should return normalized dict format**
5. **Add locale variants** for new prompts (base + locale-specific)

**Example Node Pattern:**
```python
def my_new_node(state: SNIAgentState) -> Dict[str, Any]:
    """Node description."""
    # Extract needed data from state
    query = state["query"]

    # Perform operation
    result = do_something(query)

    # Return ONLY changed fields
    return {
        "my_new_field": result
    }
```

### When Adding New Search Engines

**Steps:**
1. Add enum to `SearchEngine` in `src/config.py`
2. Implement in `get_web_search_tool()` in `src/tools/search.py`
3. Add YAML config section to `conf.yaml`
4. Update `.env.example` with API key requirements
5. Add import for new search module if needed

**Example:**
```python
# In src/config.py
class SearchEngine(enum.Enum):
    MY_ENGINE = "my_engine"

# In src/tools/search.py
elif settings.SEARCH_API == SearchEngine.MY_ENGINE.value:
    from src.tools.myengine_search import MyEngineSearch
    return MyEngineSearch(api_key=os.getenv("MYENGINE_API_KEY"))
```

### When Adding Workflow Nodes

**Steps:**
1. Define function in `src/graph/nodes.py`
2. Add node to graph in `src/graph/builder.py`
3. Update `SNIAgentState` in `src/graph/state.py` if new fields needed
4. Create prompt template if LLM-driven node
5. Add conditional edge function if branching logic needed

**Example:**
```python
# In src/graph/state.py
class SNIAgentState(TypedDict):
    # ... existing fields ...
    my_new_field: Optional[str]

# In src/graph/nodes.py
def my_new_node(self, state: SNIAgentState) -> Dict[str, Any]:
    # Implementation
    return {"my_new_field": result}

# In src/graph/builder.py
workflow.add_node("my_new_node", nodes.my_new_node)
workflow.add_edge("previous_node", "my_new_node")
```

### When Adding Prompts

**Steps:**
1. Create base template: `src/prompts/my_prompt.md` (English)
2. Create locale variant: `src/prompts/my_prompt.zh_CN.md` (Chinese)
3. Use Jinja2 syntax for variables: `{{ variable_name }}`
4. Load in node with: `get_prompt_template("my_prompt", locale=locale)`

**Template Example:**
```markdown
# Task Description

Analyze the following SNI: {{ sni }}

Context:
{{ context }}

Output format: JSON
```

## Vector Database Collections

**Qdrant Collections:**

1. **SNI Data Collection**
   - Name: `sni_domain_mapping` (configured via `QDRANT_COLLECTION`)
   - Purpose: Store SNI domain mappings with embeddings
   - Used by: `sni_exact_query_node`, `sni_vector_query_node`

2. **TGT Standard Library**
   - Name: `tgt_standard_library` (configured via `QDRANT_TGT_COLLECTION`)
   - Purpose: Canonical entity names (organizations, products)
   - Used by: `tgt_standardization_node`
   - Enables entity normalization across different name variants

**Embedding Model:**
- Lazy-loaded SentenceTransformer
- Shared across all collections
- Cached after first use

## Important Implementation Details

### Token Usage Optimization

**Design Philosophy:**
- Deterministic Python routing eliminates ~40% of LLM calls
- Context truncation prevents token overflow
- Streaming reduces perceived latency
- Parallel searches reduce total wall-clock time

### Error Handling

**Pattern:** Graceful degradation
- If exact search fails → continue to vector search
- If vector search fails → continue to web search
- If a parallel search fails → other searches continue
- Always return best available answer

### Logging

**Pattern:** Structured logging at each node
```python
logger.info(f"[node_name] Starting operation")
logger.info(f"[node_name] Results: {summary}")
```

**View logs:** Check console output when running API server or demos

## Testing

**Test Structure:**
```
tests/
├── test_api.py           # API endpoint tests
├── test_graph.py         # Workflow tests
└── test_tools.py         # Tool function tests
```

**Run Tests:**
```bash
uv run pytest tests/              # All tests
uv run pytest tests/test_api.py   # Specific test file
uv run pytest -v                  # Verbose output
```

## Frontend Integration

**Location:** `frontend/`

**Stack:**
- React + TypeScript
- Vite build tool
- Tailwind CSS
- Zustand for state management

**Setup:**
```bash
cd frontend
npm install
npm run dev
```

**SSE Integration:**
- Uses `EventSource` API
- Real-time timeline display
- Displays node-by-node progress

## Troubleshooting

### Common Issues

**1. "Qdrant connection failed"**
- Ensure Qdrant is running: `docker run -p 6333:6333 qdrant/qdrant`
- Check `QDRANT_URL` in `.env`

**2. "API key not found"**
- Verify `.env` file exists
- Check `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` is set
- Ensure no leading/trailing spaces in API key

**3. "Embedding model not found"**
- For online: Check internet connection
- For offline: Run `uv run python scripts/download_embedding_model.py`
- Verify `EMBEDDING_MODEL` path in `.env`

**4. "Import error: No module named..."**
- Run `uv sync` to install dependencies
- Check Python version: `python --version` (must be ≥3.11)

**5. Search returns no results**
- Verify search engine API key (if required)
- Check `SEARCH_API` configuration
- Try DuckDuckGo (requires no API key)

## Development Workflow

**Typical Development Session:**
```bash
# Terminal 1: Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Terminal 2: Start API server
uv run python -m src.api_server

# Terminal 3: Run tests or make changes
uv run pytest tests/
# Or edit code and test with:
uv run python demo/test_multi_round_search.py
```

**Before Committing:**
1. Run tests: `uv run pytest tests/`
2. Verify API server starts: `uv run python -m src.api_server`
3. Check prompt changes render correctly
4. Update documentation if adding features

## Performance Considerations

**Workflow Execution Time:**
- Exact match: <100ms
- Vector search: <500ms
- Each web search: 2-5 seconds
- Total workflow: 15-30 seconds (with parallel execution)

**Optimization Strategies:**
- Parallel searches reduce latency by 4-5x
- Exact match cache hits are fastest
- Increase `asyncio.Semaphore` limit for more parallelism (with caution)
- Use local embedding model to reduce network latency

**Token Usage:**
- Deterministic routing saves ~40% vs agent-based routing
- Context truncation prevents runaway token costs
- Typical query: 10K-50K tokens total

## Additional Resources

**Documentation:**
- `docs/ARCHITECTURE.md` - Detailed architecture documentation
- `docs/langgraph-architecture.md` - LangGraph workflow details
- `docs/workflow-visualization.md` - Workflow diagram
- `docs/engineering-practices.md` - Development guidelines

**Key Files to Reference:**
- `README.md` - Basic usage instructions
- `.env.example` - Configuration template
- `conf.yaml` - Search/crawler configuration
- `pyproject.toml` - Dependencies and metadata
