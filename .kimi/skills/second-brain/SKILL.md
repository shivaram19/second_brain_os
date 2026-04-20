---
name: second-brain
description: >
  Second Brain OS integration. Use when the user refers to their notes, vault,
  knowledge graph, personal knowledge base, Obsidian, or asks questions that
  should be answered from their own accumulated knowledge rather than general
  training data. Also use when the user wants to research, draft, reflect, or
  publish content grounded in their vault.
---

# Second Brain OS — Kimi Skill

## What It Is

Second Brain OS is a local-first, agentic knowledge orchestration system built
on the user's Obsidian vault. It indexes notes with semantic embeddings
(ChromaDB) and builds a knowledge graph (NetworkX) for hybrid retrieval.

## When to Use This Skill

- User asks about "my notes", "my vault", "my knowledge", "Second Brain"
- User wants to research a topic using their own accumulated ideas
- User wants to draft content grounded in their existing thinking
- User wants introspection on their knowledge (blindspots, core concepts)
- User mentions Obsidian, WikiLinks, knowledge graphs, or context engineering

## Architecture Overview

```
Obsidian Vault (markdown + frontmatter + WikiLinks)
    ↓
VaultAdapter → Chunker → Embedder → VectorStore (ChromaDB)
    ↓                                    ↓
GraphBuilder (NetworkX) ←──────────────┘
    ↓
RAG Engine (hybrid: semantic + graph)
    ↓
ContextOrchestrator (3-layer: Instruction + Knowledge + Tools)
    ↓
Agents (Research, Drafting, Reflection, Publishing)
    ↓
MCP Server → exposed to Kimi / Claude / other MCP clients
```

## Available MCP Tools

If the Second Brain OS MCP server is connected, prefer these tools over
reading raw vault files:

- **`ask`** — Query the knowledge base with hybrid retrieval. Returns
  three-layer context optimized for the question.
- **`reflect`** — Run knowledge introspection (core concepts, blindspots,
  suggested connections, thinking patterns).
- **`search_notes`** — Semantic search for specific notes by keyword.
- **`get_connections`** — Graph traversal to find related concepts.
- **`graph_stats`** — Knowledge graph topology overview.

## Available Resources

- **Vault Index** (`second-brain://vault/index`) — List of all notes
- **Persona** (`second-brain://persona`) — User's values, tone, framework
- **Telemetry** (`second-brain://telemetry`) — Query patterns and insights

## Workflows

### Research a Topic
1. Call `ask` with the topic
2. Summarize findings, citing concepts from the knowledge base
3. If depth needed, call `get_connections` on key concepts

### Draft Content
1. Call `ask` to gather relevant context
2. Draft in the user's tone (refer to Persona resource)
3. Cite sources from the knowledge base

### Reflect on Knowledge
1. Call `reflect` for full introspection report
2. Call `graph_stats` for quantitative overview
3. Suggest actions based on blindspots and suggested connections

## Important Rules

- **Always ingest first**: The vault must be indexed before querying.
  Ingestion command: `brainos ingest` (or `python -m brainos.orchestration.cli ingest`)
- **Token efficiency**: The MCP `ask` tool returns ~10-15k tokens of relevant
  context instead of dumping the whole vault (~100k tokens).
- **Persona-guided**: All agent outputs use the user's persona config
  (`config/persona.yaml`) for tone, values, and decision framework.
- **Local-first**: All data stays on the user's machine. No cloud services
  except the LLM API (Anthropic or Moonshot AI).

## Project Layout

```
config/           # persona, goals, routing, paths (YAML)
brainos/
  core/           # Pydantic models, config loader
  knowledge/      # vault, chunking, embeddings, vectors, graphs, RAG
  context_engineering/  # retrieval, packing, orchestration
  agents/         # research, drafting, reflection, publishing
  mcp_servers/    # MCP server for Kimi / Claude Desktop
  telemetry/      # SQLite event logging
  orchestration/  # CLI entry points
scripts/          # demo vault generator, vault setup
```

## Troubleshooting

- "Vault not found" → Check `config/paths.yaml` `obsidian_vault` path
- "No results" → Run `brainos ingest` to index the vault
- "Slow first query" → First embedding model download (~2-3 min one-time)
