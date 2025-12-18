# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SNI RAG is an intelligent SNI (Server Name Indication) recognition system built with LangGraph and Claude AI. The system supports two query modes:

- **Workflow Mode**: Fixed StateGraph with predetermined nodes and routing
- **Agent Mode**: LLM-driven tool calling where Claude actively decides which tools to invoke

## Development Setup

### Installation

```bash
# Install dependencies using uv
uv sync

# Install with dev dependencies
uv sync --group dev
```

### Environment Configuration

Copy `.env.example` to `.env` and configure:
- `ANTHROPIC_API_KEY`: Required for Claude API access
- `QDRANT_URL`: Qdrant vector database URL (default: http://localhost:6333)
- `CLAUDE_MODEL`: Claude model to use (default: claude-3-5-sonnet-20241022)
- `EMBEDDING_MODEL`: SentenceTransformer model for vector embeddings

### Data Import

Before using the system, import SNI data into Qdrant:

```bash
uv run python -m src.import_data --data-dir ./results
```

This reads JSON files from `results/` directory, generates 384-dimensional embeddings using SentenceTransformer, and stores them in Qdrant.

## Running the System

### Start API Server

```bash
uv run python -m src.api_server
```

Default port: 8000 (configurable via `API_PORT` in `.env`)

### CLI Usage

```bash
# Query using CLI
uv run python demo/cli.py "www.google.com"

# Interactive mode with verbose output
uv run python demo/interactive_verbose.py
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_tools.py

# Run with verbose output
pytest -v
```

## Architecture

### Core Components

1. **Tools Layer** (`src/tools.py`):
   - `search_sni_exact(sni)`: Exact match on SNI name using Qdrant filter
   - `search_sni_vector(query, top_k)`: Vector similarity search
   - `search_by_domain(domain, limit)`: Find all SNIs under a domain

2. **Workflow Mode** (`src/graph.py`, `src/nodes.py`):
   - Fixed flow: understand_query → route_query → [exact/vector/domain]_search → aggregate_results → generate_answer
   - Uses LangGraph StateGraph with conditional edges
   - Nodes handle query understanding, routing, searching, and answer generation

3. **Agent Mode** (`src/agent.py`):
   - LLM actively decides which tools to call based on query
   - Iterative process: LLM thinks → calls tools → LLM synthesizes answer
   - Supports streaming output for real-time response

4. **Configuration** (`src/config.py`):
   - Centralized settings using Pydantic BaseSettings
   - Loads from `.env` file with override priority

5. **API Server** (`src/api_server.py`):
   - FastAPI server with two endpoints:
     - `POST /api/query`: Workflow mode
     - `POST /api/query/agent`: Agent mode (with streaming support)

### Data Flow

```
User Query → [CLI/API] → [Workflow/Agent Mode] → Tools Layer → Qdrant DB → Claude LLM → Structured JSON Output
```

### State Management

The workflow mode uses `SNIGraphState` (defined in `src/state.py`) to maintain:
- `query`: Original user query
- `query_type`: Classified as "exact", "vector", or "domain"
- `extracted_entities`: Parsed SNIs, domains from query
- `tool_calls`: History of tool invocations
- `tool_results`: Results from tool executions
- `answer`: Final JSON-formatted response
- `need_more_info`: Flag to trigger additional searches

## Key Implementation Details

### LLM Tool Binding

Agent mode binds tools to Claude using LangChain's `bind_tools()`:

```python
llm_with_tools = self.llm.bind_tools(self.langchain_tools)
```

This enables Claude to see tool schemas and decide when to invoke them.

### Vector Embeddings

The system uses `paraphrase-multilingual-MiniLM-L12-v2` to generate 384-dimensional embeddings:
- Input format: `f"{sni} {domain}"` (concatenated)
- Stored in Qdrant alongside payload (sni, domain, all_snis, alpn_protocols, total_count)

### Query Routing Logic

Workflow mode classifies queries using regex patterns and LLM analysis:
- SNI pattern: `r'\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}\b'`
- Domain pattern: `r'\b[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.[a-z]{2,}\b'`

### Streaming Support

Agent mode supports streaming via `stream_query()` function, yielding chunks for:
- Tool call decisions
- Tool execution results
- Incremental answer generation

## Output Format

Both modes return structured JSON:

```json
{
  "Website/Service": "Service name",
  "Explanation": "Detailed explanation of the SNI/domain",
  "Query Results": "Summary of found matches with counts and domains"
}
```

## Common Patterns

### Adding a New Tool

1. Add method to `SNITools` class in `src/tools.py`
2. Create LangChain tool wrapper using `@tool` decorator in `create_langchain_tools()`
3. Add tool to workflow nodes if needed (for Workflow mode)
4. Tool automatically available in Agent mode

### Modifying LLM Behavior

- System prompts are defined in:
  - Agent mode: `src/agent.py` (line 43)
  - Workflow nodes: `src/nodes.py` (various methods)
- Adjust `temperature` parameter in LLM initialization for creativity vs determinism

### Changing Vector Search Threshold

Modify `score_threshold` in `search_sni_vector()` within `src/tools.py`:

```python
results = self.client.query_points(
    collection_name=self.collection_name,
    query=query_vector,
    limit=top_k,
    score_threshold=0.5  # Adjust this value
)
```

## Dependencies

Key packages:
- `langgraph>=0.2.0`: State graph orchestration
- `langchain-anthropic>=0.3.0`: Claude integration
- `qdrant-client>=1.12.0`: Vector database client
- `sentence-transformers>=3.0.0`: Embedding generation
- `fastapi>=0.115.0`: API server
- `pydantic>=2.10.0`: Settings and validation

## Project Structure

- `src/`: Main source code
  - `agent.py`: Agent mode implementation
  - `graph.py`: Workflow mode StateGraph definition
  - `nodes.py`: Graph node implementations
  - `tools.py`: SNI search tools
  - `config.py`: Configuration management
  - `state.py`: State type definitions
  - `import_data.py`: Data import script
  - `api_server.py`: FastAPI server
- `demo/`: Example usage scripts
- `results/`: SNI data JSON files
- `tests/`: Test suite
- `model/`: Local sentence-transformer model files

## Performance Considerations

- Workflow mode: ~3-5s response time, lower token usage
- Agent mode: ~3-5s response time, higher token usage (typically 30k+ tokens)
- Qdrant queries: ~100ms
- Initial model load (SentenceTransformer): ~2-3s (cached afterward)

## Troubleshooting

### Qdrant Connection Issues

Ensure Qdrant is running and accessible at `QDRANT_URL`. Check collection exists:

```python
from qdrant_client import QdrantClient
client = QdrantClient(url="http://localhost:6333")
print(client.get_collections())
```

### API Key Errors

Verify `ANTHROPIC_API_KEY` is set in `.env` and has valid access. Check `ANTHROPIC_BASE_URL` if using a proxy/custom endpoint.

### Embedding Model Not Found

The system will download `paraphrase-multilingual-MiniLM-L12-v2` on first run. Ensure internet connectivity or pre-download to `model/` directory.
