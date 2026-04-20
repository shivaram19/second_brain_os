# Second Brain OS

A local-first, agentic knowledge orchestration system built on Obsidian, Python, and the Model Context Protocol.

## Vision

Transform your Obsidian vault into a **queryable, agentic knowledge system** that:
- Understands your ideas as a connected graph
- Retrieves knowledge semantically and structurally
- Fills your context window optimally for any task
- Executes complex workflows over your knowledge
- Learns and reflects on its own execution

## Architecture

### Three-Layer Context Stack

1. **Instruction Layer**: Your persona, values, goals, and decision frameworks (from `config/` YAML)
2. **Knowledge Layer**: Your Obsidian vault, indexed for semantic search and graph traversal
3. **Tool Layer**: MCP servers exposing vault queries, graph operations, and telemetry

### Core Concepts

- **Idea**: A note in your Obsidian vault with frontmatter metadata
- **Chunk**: A text segment from an Idea, ready for embedding
- **GraphNode / GraphEdge**: Nodes and relationships built from vault links and tags
- **ContextSlice**: A scored piece of context from one of the three layers
- **RetrievedFacts**: Results from hybrid retrieval (semantic + graph)
- **BudgetSpec**: Token budget for context packing

### Knowledge Flow

```
Obsidian Vault (source of truth)
    ↓
Chunking (heading-based, sliding window)
    ↓
Embedding (ChromaDB)
    ↓
Vector Index + Knowledge Graph (NetworkX)
    ↓
Hybrid Retrieval (semantic + graph)
    ↓
Context Packing (token-aware)
    ↓
Context Orchestration (fills 3 layers)
    ↓
MCP Exposure (Claude, local agents)
```

## Tech Stack

- **Language**: Python 3.11+
- **Models**: Pydantic (types), NetworkX (graphs), ChromaDB (vectors)
- **Configuration**: YAML
- **APIs**: Anthropic SDK, Moonshot AI (Kimi), OpenAI-compatible, Model Context Protocol
- **Storage**: SQLite (telemetry), local files (vault)

## Integrations

- **Claude Desktop**: MCP server (`CLAUDE_DESKTOP_SETUP.md`)
- **Kimi CLI**: MCP server + skill (`KIMI_SETUP.md`)

## Quick Start

### 1. Setup

```bash
cd ~/Developer/second_brain_os
python -m venv venv
source venv/bin/activate
pip install -e .
```

### 2. Configure

Update `config/paths.yaml` with your Obsidian vault path:

```yaml
paths:
  obsidian_vault: "/path/to/your/vault"
```

Optionally update `config/persona.yaml` with your values and decision framework.

#### LLM Provider

By default, agents use Anthropic Claude. To use **Moonshot AI (Kimi)** instead:

```bash
export MOONSHOT_API_KEY="your-api-key"
```

Agents will auto-detect and fall back to Moonshot when Anthropic is unavailable.

### 3. Ingest

Generate a demo vault (or use your own):

```bash
python scripts/generate_demo_vault.py
python scripts/ingest_vault_once.py
```

### 4. Query

```bash
python -m brainos ask "How does systems thinking relate to effective altruism?"
```

## Module Structure

```
brainos/
  core/             # Domain models (Pydantic), config loaders
  instruction/      # Persona, goals, routing
  knowledge/        # Vault, chunking, embeddings, vectors, graphs
  context_engineering/  # Retrieval, packing, orchestration
  agents/           # Agent base class and subagents
  mcp_servers/      # MCP server implementations
  telemetry/        # Event logging and analytics
  orchestration/    # CLI and main loop
```

## Development

### Running Tests

```bash
pytest tests/
```

### Running the CLI

```bash
python -m brainos ask "your question here"
brainos graph-stats
brainos reflect --daily
```

## Design Decisions

See `claude.md` for detailed architectural decisions, trade-offs, and future roadmap.

## License

Apache 2.0
