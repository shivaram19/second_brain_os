"""MCP server exposing vault and RAG capabilities.

VaultMCPServer is an early MVP implementation demonstrating the MCP interface
for vault queries and graph analytics. It wires together the knowledge-layer
components (vault adapter, embedder, vector store, graph builder, RAG engine)
to answer questions and return statistics.

Most functionality has been superseded by SecondBrainMCPServer (claude_server.py),
which adds context engineering, persona injection, and richer tool schemas.
This module remains as a reference implementation and fallback.
"""

import json
from typing import Any, Dict

from brainos.core import load_config
from brainos.knowledge.obsidian.vault_adapter import VaultAdapter
from brainos.knowledge.chunking.heading_chunker import HeadingChunker
from brainos.knowledge.embedding.sentence_transformers_embedder import (
    SentenceTransformersEmbedder,
)
from brainos.knowledge.vector_store.chroma_store import ChromaVectorStore
from brainos.knowledge.graph.graph_builder import GraphBuilder
from brainos.knowledge.rag.rag_engine import RAGEngine
from brainos.telemetry.schema import TelemetryDB


class VaultMCPServer:
    """MCP server for vault and RAG operations."""

    def __init__(self):
        """Initialize server with all components."""
        config = load_config()
        vault_path = config.paths.get("obsidian_vault", "~/ObsidianVault")
        vector_db_path = config.paths.get("vector_index_dir", "./.brainos/vector_db")
        telemetry_db_path = config.paths.get("telemetry_db", "./.brainos/telemetry.db")

        self.vault_adapter = VaultAdapter(vault_path)
        self.chunker = HeadingChunker()
        self.embedder = SentenceTransformersEmbedder()
        self.vector_store = ChromaVectorStore(vector_db_path)
        self.graph_builder = GraphBuilder()

        self.rag_engine = RAGEngine(self.vector_store, self.embedder, self.graph_builder)
        self.telemetry = TelemetryDB(telemetry_db_path)

    def ask(self, query: str, top_k: int = 10) -> Dict[str, Any]:
        """Ask a question and retrieve facts.

        Args:
            query: Question to ask
            top_k: Number of results

        Returns:
            Dict with semantic and graph results
        """
        results = self.rag_engine.retrieve(query, top_k=top_k)

        # Log to telemetry
        self.telemetry.log_query(
            query,
            len(results.semantic_results),
            len(results.graph_results),
            top_result_score=0.5,  # TODO: compute actual score
        )
        self.telemetry.log_event(
            "query", query=query, num_results=len(results.semantic_results) + len(results.graph_results)
        )

        # Format response
        semantic_list = [
            {
                "title": chunk.metadata.get("title", "Unknown"),
                "preview": chunk.text[:300],
                "score": 0.8,  # TODO: actual score
            }
            for chunk in results.semantic_results[:5]
        ]

        graph_list = [
            {
                "concept": node.label,
                "connections": self.graph_builder.graph.degree(node.node_id),
            }
            for node in results.graph_results[:3]
        ]

        return {
            "query": query,
            "semantic_results": semantic_list,
            "graph_results": graph_list,
            "total_results": len(semantic_list) + len(graph_list),
        }

    def get_graph_stats(self) -> Dict[str, Any]:
        """Get knowledge graph statistics.

        Returns:
            Graph stats
        """
        ideas = self.vault_adapter.ingest_all()
        self.graph_builder.build_from_ideas(ideas)
        stats = self.graph_builder.get_node_stats()

        return {
            "nodes": stats["nodes"],
            "edges": stats["edges"],
            "density": stats["density"],
        }

    def list_resources(self) -> Dict[str, Any]:
        """List available vault resources.

        Returns:
            Dict with available resources
        """
        ideas = self.vault_adapter.ingest_all()

        return {
            "notes": len(ideas),
            "resources": [
                {"name": idea.title, "path": idea.vault_path, "tags": idea.tags}
                for idea in ideas[:10]  # Limit to 10 for MVP
            ],
        }

    def get_query_stats(self) -> Dict[str, Any]:
        """Get query execution statistics.

        Returns:
            Query stats
        """
        top_queries = self.telemetry.get_top_queries(limit=5)

        return {
            "top_queries": top_queries,
            "event_stats": self.telemetry.get_event_stats("query"),
        }
