"""Second Brain OS - Local-first knowledge orchestration system.

This package implements a complete agentic knowledge system built on Obsidian,
Python, and the Model Context Protocol (MCP). It transforms an Obsidian vault
into a queryable, semantic knowledge graph with three-layer context engineering
(Instruction + Knowledge + Tools) optimized for LLM context windows.

Architecture layers (bottom-up):
  - core: Domain models (Pydantic) and configuration loading
  - knowledge: Vault ingestion, chunking, embeddings, vector stores, graphs, RAG
  - context_engineering: Hybrid retrieval, token-aware packing, orchestration
  - agents: Research, drafting, reflection, and publishing agents
  - mcp_servers: Model Context Protocol exposure for Claude Desktop
  - telemetry: SQLite event logging and query analytics
  - orchestration: CLI entry points and main loop
"""

__version__ = "0.1.0"
