"""Production MCP Server for Claude integration.

SecondBrainMCPServer exposes Second Brain OS as MCP tools and resources for
Claude Desktop. This is the primary integration surface between the user's
knowledge system and Claude.

Tools (what Claude can call):
  - ask: Query the knowledge base and get packed three-layer context
  - reflect: Run knowledge reflection (core concepts, blindspots, suggestions)
  - search_notes: Semantic search over vault notes
  - get_connections: Graph traversal for related concepts
  - graph_stats: Knowledge graph topology overview

Resources (what Claude can read):
  - vault/index: List of all notes
  - persona: Instruction layer (values, tone, framework)
  - telemetry: Query patterns and usage stats

All tool calls are logged to telemetry for analytics and reflection loops.
"""

import json
from typing import Any

from brainos.agents.reflection_agent import ReflectionAgent
from brainos.context_engineering.orchestrator import ContextOrchestrator
from brainos.context_engineering.packing import GreedyContextPacker
from brainos.context_engineering.selection import HybridRetriever
from brainos.core import load_config
from brainos.core.models import BudgetSpec, PersonaBlock
from brainos.knowledge.obsidian.vault_adapter import VaultAdapter
from brainos.knowledge.chunking.heading_chunker import HeadingChunker
from brainos.knowledge.embedding.sentence_transformers_embedder import (
    SentenceTransformersEmbedder,
)
from brainos.knowledge.vector_store.chroma_store import ChromaVectorStore
from brainos.knowledge.graph.graph_builder import GraphBuilder
from brainos.knowledge.rag.rag_engine import RAGEngine
from brainos.telemetry.schema import TelemetryDB


class SecondBrainMCPServer:
    """MCP Server exposing Second Brain OS to Claude."""

    def __init__(self):
        """Initialize server with all components."""
        self.config = load_config()

        vault_path = self.config.paths.get("obsidian_vault", "~/ObsidianVault")
        vector_db_path = self.config.paths.get("vector_index_dir", "./.brainos/vector_db")
        telemetry_db_path = self.config.paths.get("telemetry_db", "./.brainos/telemetry.db")

        # Core components
        self.vault_adapter = VaultAdapter(vault_path)
        self.chunker = HeadingChunker()
        self.embedder = SentenceTransformersEmbedder()
        self.vector_store = ChromaVectorStore(vector_db_path)
        self.graph_builder = GraphBuilder()

        # Knowledge components
        self.rag_engine = RAGEngine(self.vector_store, self.embedder, self.graph_builder)
        self.telemetry = TelemetryDB(telemetry_db_path)

        # Context engineering
        self.retriever = HybridRetriever(self.rag_engine)
        self.packer = GreedyContextPacker()

        # Load persona for context layer
        persona_config = self.config.persona
        self.persona = PersonaBlock(
            name=persona_config.get("name", "Systems Architect"),
            values=persona_config.get("values", []),
            tone=persona_config.get("tone", ""),
            reasoning_style=persona_config.get("reasoning_style", ""),
            decision_framework=persona_config.get("decision_framework", ""),
        )

        # Context orchestrator
        self.orchestrator = ContextOrchestrator(self.retriever, self.packer, self.persona)

        # Reflection
        self.reflection_agent = None  # Lazy-loaded

    def _load_reflection_agent(self):
        """Lazy-load reflection agent."""
        if self.reflection_agent is None:
            vault_path = self.config.paths.get("obsidian_vault", "~/ObsidianVault")
            telemetry_db_path = self.config.paths.get("telemetry_db", "./.brainos/telemetry.db")
            self.reflection_agent = ReflectionAgent(vault_path, telemetry_db_path)
        return self.reflection_agent

    # ============================================================
    # TOOLS - What Claude can call
    # ============================================================

    def tool_ask(self, query: str, budget_tokens: int = 100000) -> dict[str, Any]:
        """Ask a question and get packed context.

        Args:
            query: Natural language question
            budget_tokens: Total token budget

        Returns:
            Dict with packed context layers
        """
        try:
            # Create budget
            budget = BudgetSpec(
                total_tokens=budget_tokens,
                instruction_budget=budget_tokens // 6,
                knowledge_budget=budget_tokens // 2,
                tool_budget=budget_tokens // 6,
            )

            # Orchestrate context
            context_slices = self.orchestrator.orchestrate(query, budget)

            # Log to telemetry
            self.telemetry.log_event(
                "query",
                query=query,
                num_results=len(context_slices),
                tokens_used=sum(s.token_count for s in context_slices),
                context_layers=",".join(s.layer.value for s in context_slices),
            )
            self.telemetry.log_query(query, len(self.retriever.retrieve(query).semantic_results), 0)

            return {
                "status": "success",
                "query": query,
                "context_slices": [
                    {
                        "layer": s.layer.value,
                        "content": s.content,
                        "token_count": s.token_count,
                        "source": s.source,
                        "relevance_score": s.relevance_score,
                    }
                    for s in context_slices
                ],
                "total_tokens_used": sum(s.token_count for s in context_slices),
                "instruction": "Use the context above to answer the user's question. Instruction layer (persona/values) should guide your reasoning. Knowledge layer contains relevant facts. Tool layer shows available capabilities.",
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to answer question. Did you ingest the vault?",
            }

    def tool_reflect(self) -> dict[str, Any]:
        """Reflect on your knowledge and get insights.

        Returns:
            Dict with reflection insights
        """
        try:
            agent = self._load_reflection_agent()
            reflection_data = agent.get_reflection_json()

            self.telemetry.log_event("reflect", metadata={"reflection_type": "api"})

            return {
                "status": "success",
                "reflection": reflection_data,
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }

    def tool_search_notes(self, query: str, top_k: int = 10) -> dict[str, Any]:
        """Search for notes matching a query.

        Args:
            query: Search query
            top_k: Number of results

        Returns:
            Dict with matching notes
        """
        try:
            results = self.retriever.retrieve(query, top_k=top_k)

            self.telemetry.log_event("search", query=query, num_results=len(results.semantic_results))

            return {
                "status": "success",
                "query": query,
                "results": [
                    {
                        "title": chunk.metadata.get("title", "Unknown"),
                        "preview": chunk.text[:500],
                        "source": chunk.metadata.get("vault_path", ""),
                    }
                    for chunk in results.semantic_results[:top_k]
                ],
                "total_results": len(results.semantic_results),
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }

    def tool_get_connections(self, concept: str) -> dict[str, Any]:
        """Get related concepts for a given concept.

        Args:
            concept: Concept name to explore

        Returns:
            Dict with connected concepts
        """
        try:
            # Find the concept in the graph
            matching_nodes = []
            for node_id, node_data in self.graph_builder.graph.nodes(data=True):
                if concept.lower() in node_data.get("label", "").lower():
                    matching_nodes.append((node_id, node_data.get("label")))

            if not matching_nodes:
                return {
                    "status": "not_found",
                    "concept": concept,
                    "message": f"Concept '{concept}' not found in knowledge graph",
                }

            # Get connections for the first match
            node_id, label = matching_nodes[0]
            neighbors = self.graph_builder.get_neighbors(node_id, depth=2)

            neighbor_labels = [
                self.graph_builder.graph.nodes[n].get("label", n) for n in neighbors
            ]

            return {
                "status": "success",
                "concept": label,
                "direct_connections": len(list(self.graph_builder.graph.successors(node_id))),
                "neighbors": neighbor_labels[:20],
                "neighbors_count": len(neighbor_labels),
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }

    def tool_graph_stats(self) -> dict[str, Any]:
        """Get knowledge graph statistics.

        Returns:
            Dict with graph statistics
        """
        try:
            # Rebuild graph from ideas
            ideas = self.vault_adapter.ingest_all()
            self.graph_builder.build_from_ideas(ideas)

            stats = self.graph_builder.get_node_stats()
            top_concepts = self.graph_builder.pagerank(top_k=10)

            self.telemetry.log_event("graph_stats")

            return {
                "status": "success",
                "nodes": stats["nodes"],
                "edges": stats["edges"],
                "density": round(stats["density"], 4),
                "avg_connections_per_concept": round(
                    2 * stats["edges"] / max(1, stats["nodes"]), 2
                ),
                "top_concepts": [
                    {"name": label, "connections": int(rank)}
                    for label, rank in top_concepts
                ],
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }

    # ============================================================
    # RESOURCES - What Claude can read
    # ============================================================

    def resource_vault_index(self) -> dict[str, Any]:
        """Get list of all notes in vault.

        Returns:
            Dict with vault contents
        """
        try:
            ideas = self.vault_adapter.ingest_all()

            return {
                "status": "success",
                "vault_size": len(ideas),
                "notes": [
                    {
                        "title": idea.title,
                        "path": idea.vault_path,
                        "tags": idea.tags,
                    }
                    for idea in ideas[:50]  # Limit to 50 for brevity
                ],
                "total_notes": len(ideas),
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }

    def resource_persona(self) -> dict[str, Any]:
        """Get the instruction layer (persona, values, framework).

        Returns:
            Dict with persona configuration
        """
        return {
            "status": "success",
            "persona": {
                "name": self.persona.name,
                "values": self.persona.values,
                "tone": self.persona.tone,
                "reasoning_style": self.persona.reasoning_style,
                "decision_framework": self.persona.decision_framework,
            },
        }

    def resource_telemetry_summary(self) -> dict[str, Any]:
        """Get telemetry summary (what you've queried, patterns).

        Returns:
            Dict with telemetry insights
        """
        try:
            top_queries = self.telemetry.get_top_queries(limit=10)
            event_stats = self.telemetry.get_event_stats("query")

            return {
                "status": "success",
                "total_queries": event_stats.get("event_count", 0),
                "avg_tokens_per_query": round(event_stats.get("avg_tokens", 0), 0),
                "top_queries": top_queries[:5],
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }
