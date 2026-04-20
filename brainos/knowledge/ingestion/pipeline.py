"""Ingestion pipeline: vault → chunks → vectors + graph.

IngestionPipeline is the end-to-end ETL orchestrator for Second Brain OS.
It wires together all knowledge-layer components to transform raw Obsidian
markdown into a fully indexed, queryable knowledge base.

Pipeline flow:
  1. VaultAdapter reads all .md files into Idea objects
  2. Chunker splits each Idea's content into Chunk objects
  3. Embedder generates vector embeddings for all chunks
  4. VectorStore persists embeddings for semantic search
  5. GraphBuilder constructs a NetworkX graph from WikiLinks and tags

This is typically invoked via CLI: `brainos ingest`
"""

from typing import Dict, List
from uuid import UUID

from brainos.core.models import Idea
from brainos.knowledge.obsidian.vault_adapter import VaultAdapter
from brainos.knowledge.chunker_base import AbstractChunker
from brainos.knowledge.embedding_base import AbstractEmbedder
from brainos.knowledge.vector_store_base import AbstractVectorStore
from brainos.knowledge.graph.graph_builder import GraphBuilder


class IngestionPipeline:
    """End-to-end ingestion from vault to indexed vectors and graph."""

    def __init__(
        self,
        vault_adapter: VaultAdapter,
        chunker: AbstractChunker,
        embedder: AbstractEmbedder,
        vector_store: AbstractVectorStore,
        graph_builder: GraphBuilder,
    ):
        """Initialize ingestion pipeline.

        Args:
            vault_adapter: Reads Obsidian vault
            chunker: Splits text into chunks
            embedder: Generates embeddings
            vector_store: Stores embeddings
            graph_builder: Builds knowledge graph
        """
        self.vault_adapter = vault_adapter
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
        self.graph_builder = graph_builder

    def ingest_all(self) -> Dict[str, int]:
        """Load all vault notes and index them.

        Returns:
            Dict with ingestion stats (ideas_loaded, chunks_created, etc.)
        """
        stats = {
            "ideas_loaded": 0,
            "chunks_created": 0,
            "chunks_embedded": 0,
            "graph_nodes": 0,
            "graph_edges": 0,
        }

        # Load all ideas from vault
        ideas = self.vault_adapter.ingest_all()
        stats["ideas_loaded"] = len(ideas)

        # Chunk and embed
        all_chunks = []
        for idea in ideas:
            chunks = self.chunker.chunk(idea.id, idea.content, metadata={"title": idea.title})
            all_chunks.extend(chunks)

        stats["chunks_created"] = len(all_chunks)

        # Embed chunks
        texts = [chunk.text for chunk in all_chunks]
        embeddings = self.embedder.embed_batch(texts)

        for i, chunk in enumerate(all_chunks):
            chunk.embedding = embeddings[i]

        # Store in vector DB
        self.vector_store.upsert(all_chunks)
        stats["chunks_embedded"] = len(all_chunks)

        # Build knowledge graph
        self.graph_builder.build_from_ideas(ideas)
        stats["graph_nodes"] = self.graph_builder.graph.number_of_nodes()
        stats["graph_edges"] = self.graph_builder.graph.number_of_edges()

        return stats
