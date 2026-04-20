# Second Brain OS - Architectural Memory

## Project Overview

**Mission**: Build a local-first, agentic knowledge orchestration system on Obsidian that fills the context window optimally using three-layer context engineering (Instruction + Knowledge + Tools).

**Scope**: MVP (0.1.0) focuses on core architecture + working RAG + basic CLI. Full agentic loops come later.

**Status**: Phase 1 (Foundation) complete. Building Phase 2 (Knowledge Layer) now.

---

## Architecture Decisions

### 1. Three-Layer Context Stack

**Decision**: Explicitly separate Instruction, Knowledge, and Tool layers in context engineering.

**Why**: Mirrors Karpathy's context-as-architecture principle. Allows independent tuning and composition.

**How to apply**:
- Instruction layer: Load from `config/persona.yaml` + history
- Knowledge layer: Retrieve from vault (semantic + graph)
- Tool layer: Expose via MCP servers
- Each layer has a budget and a relevance score

### 2. Pydantic for All Domain Models

**Decision**: Use Pydantic `BaseModel` exclusively for Idea, Chunk, GraphNode, TaskSpec, etc.

**Why**: Validation, JSON serialization, schema generation (needed for MCP), type safety.

**Trade-off**: Slightly more boilerplate than plain dataclasses, but worth the integration benefits.

### 3. Abstract Base Classes (ABCs) for Subsystems

**Decision**: Define ABCs for Embedder, VectorStore, Chunker, Retriever, Packer, Agent.

**Why**: Swap implementations without changing calling code (e.g., ChromaDB ↔ FAISS, heading chunker ↔ sliding window).

**Trade-off**: Upfront abstraction cost, but critical for testability and extensibility.

### 4. ChromaDB for Vector Store (with Abstraction)

**Decision**: Use ChromaDB as the default vector store, but abstract behind `AbstractVectorStore`.

**Why**: ChromaDB is production-ready, local-first, and has a clean API. Abstraction lets us swap to FAISS, SQLite, Pinecone later without refactoring.

**Trade-off**: Must maintain ChromaDB compatibility. Current version is 0.5.5; migration path to newer versions needs testing.

### 5. NetworkX for Knowledge Graphs

**Decision**: Use pure-Python NetworkX for graph representation, no external graph DB.

**Why**: No external service, in-memory fast, simple to learn, good for small-to-medium graphs (10k nodes easily).

**Trade-off**: Not suitable for graphs > 1M nodes. Can migrate to Neo4j later if needed.

### 6. SQLite for Telemetry

**Decision**: File-based SQLite for all event logging and analytics.

**Why**: No external dependency, versionable, queryable, good enough for personal knowledge graphs.

**Trade-off**: Not distributed; single-user system. Multi-user case requires redesign.

### 7. YAML Configuration

**Decision**: Persona, goals, routing, and paths stored as YAML files in `config/`.

**Why**: Human-readable, versionable, no code changes needed for tuning.

**Trade-off**: No schema validation at the YAML level; Pydantic validates on load.

### 8. Hybrid Retrieval (Semantic + Graph)

**Decision**: Retrieve using both vector similarity and graph neighborhood, then score and rank together.

**Why**: Captures both semantic relevance and structural importance. Fixes the "lost-in-translation" problem of pure vector search.

**How to apply**:
- Vector search: "How does X relate to Y?"
- Graph search: Traverse neighbors of X, ancestors, descendants
- Score: Combine cosine similarity + graph centrality + recency + novelty
- Pack under budget: Greedy selection of highest-scoring results

### 9. Budget-Aware Context Packing

**Decision**: Use explicit token budgets (instruction, knowledge, tool) and a greedy packer.

**Why**: LLM context is finite; must prioritize. Simple greedy packing is fast and good enough for MVP.

**Trade-off**: Optimal packing is NP-hard; we use heuristics. Can upgrade to more sophisticated algorithms later.

### 10. Async Everywhere

**Decision**: All I/O-bound operations are async (MCP servers, embeddings, DB queries).

**Why**: Enables concurrent operations (multiple MCP requests, parallel embedding, file watching).

**Trade-off**: Complexity; requires careful async/await management. Mitigation: use async context managers and proper cancellation.

### 11. No External Services Initially

**Decision**: Everything runs locally on Mac; no cloud APIs required (except LLM providers like Anthropic).

**Why**: Privacy, latency, autonomy. Can add cloud features later (sync, backup, etc.).

**Trade-off**: Can't access real-time data. Mitigation: design ingestion pipeline to pull from external sources on schedule.

---

## Current State

### Completed (Phase 1)

- ✅ Project scaffold (`pyproject.toml`, package structure)
- ✅ Pydantic domain models (Idea, Chunk, GraphNode, TaskSpec, PersonaBlock, ContextSlice, BudgetSpec, AgentResult)
- ✅ Config loaders (YAML parsing + validation)
- ✅ Base ABCs (Embedder, VectorStore, Chunker, Retriever, Packer, Agent)
- ✅ Configuration templates (persona.yaml, goals.yaml, routing.yaml, paths.yaml)
- ✅ Documentation (README, this file)

### In Progress (Phase 2)

- [ ] Obsidian vault adapter (read markdown + frontmatter)
- [ ] Markdown parser (extract content, metadata, WikiLinks)
- [ ] Chunking implementations (heading-based, sliding window)
- [ ] ChromaDB embedder (integrate Anthropic embeddings)
- [ ] ChromaDB vector store (wrapper around Anthropic SDK)
- [ ] Knowledge graph builder (parse links, tags → NetworkX)
- [ ] RAG engine (hybrid retrieval)
- [ ] Demo vault generator (10-15 notes on Systems Thinking)
- [ ] Ingest script (vault → chunks → vectors + graph)

### Pending (Phase 3+)

- [ ] Context engineering (selection, packing, orchestration)
- [ ] MCP servers (vault, graph, telemetry)
- [ ] Telemetry (SQLite schema, logger, queries)
- [ ] CLI (ask, graph-stats, reflect, etc.)
- [ ] Agentic loop (research, drafting, reflection agents)
- [ ] Tests (unit + integration)

---

## Dependencies & Constraints

### Python Version
Target Python 3.11+. Using f-strings, type hints, match/case.

### Key Libraries
- `pydantic>=2.6.0` — domain models, validation
- `networkx>=3.3` — knowledge graphs
- `chromadb>=0.5.5` — vector store
- `anthropic>=0.32.0` — LLM API + embeddings
- `mcp>=0.1.0` — Model Context Protocol
- `pyyaml>=6.0` — config files

### Mac Environment
Assumes Homebrew, Python 3.12 system framework, `uv` package manager available.

### Obsidian Vault
Expects standard Obsidian structure:
- Markdown files with `.md` extension
- YAML frontmatter (tags, status, domain, etc.)
- WikiLinks in `[[note-name]]` format
- Optional folder hierarchy (`concepts/`, `projects/`, etc.)

---

## Design Principles (Bezos + Zuckerberg Energy)

1. **Ship fast**: Get to a working RAG system ASAP. Iterate.
2. **Customer obsession**: What does the user (Shiv) need to do *today*? Build that first.
3. **Long-term vision**: Design for 10x scale, but don't over-engineer until needed.
4. **Day 1 mentality**: Always act like the project is new; ruthlessly cut scope.
5. **SOLID architecture**: Clean code, testable, extensible. Worth the upfront cost.

---

## Known Issues & Mitigations

### Issue 1: ChromaDB API Compatibility
- **Problem**: ChromaDB 0.5.5 uses different API than older versions; docs may reference old API.
- **Mitigation**: Pin to 0.5.5, test thoroughly, plan migration path.

### Issue 2: No Real Obsidian Vault Yet
- **Problem**: Shiv doesn't have an Obsidian vault; design is untested against real data.
- **Mitigation**: Generate demo vault (Systems Thinking domain), test against that. User can swap their vault later.

### Issue 3: Token Budget Enforcement
- **Problem**: LLM providers may return different token counts than we predict.
- **Mitigation**: Add safety margin (10% buffer), measure actual token usage, adjust.

### Issue 4: Graph Scalability
- **Problem**: NetworkX loads entire graph into memory; not suitable for > 1M nodes.
- **Mitigation**: Optimize for 10k–100k nodes. Profile and add lazy loading if needed.

---

## Future Roadmap

### Phase 3: Context Engineering & MCP (Next)
- Implement typed context selection and packing
- Build MCP servers (vault, graph, telemetry)
- Test with Claude Desktop

### Phase 4: Agentic Loop (Following)
- Implement research, drafting, reflection agents
- Build orchestration CLI
- Set up telemetry and analytics

### Phase 5: Polish & Scale (Later)
- Comprehensive test suite
- Performance profiling and optimization
- Multi-user support (if needed)
- Cloud sync and backup

### Phase 6: Research Directions
- Could we auto-detect persona drift using telemetry?
- Could we use reinforcement learning to optimize context packing?
- Could we expose multiple agents as sub-MCP-servers?

---

## Questions for Future Sessions

1. Should we ingest Shiv's *real* Obsidian vault, or start with demo?
2. Should MCP servers be long-lived (daemon) or request-scoped?
3. How do we handle persona evolution over time?
4. Should telemetry be ingested back into the vault as meta-notes?
5. Can we leverage Epistemic Engine's vault builder for seeding?

---

## How to Use This Document

- **Adding features**: Update the "Current State" section and "Phase" as work progresses.
- **Debugging**: Reference "Known Issues" and "Design Decisions" when stuck.
- **Onboarding**: New collaborators should read "Architecture Decisions" and "Design Principles".
- **Planning**: Refer to "Roadmap" to understand scope and dependencies.

Last updated: 2026-03-15
Maintained by: Claude (Lead Architect)
