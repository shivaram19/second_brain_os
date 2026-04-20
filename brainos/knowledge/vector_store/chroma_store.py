"""ChromaDB vector store wrapper.

Implements AbstractVectorStore using ChromaDB's PersistentClient for local,
disk-backed vector storage. Uses cosine similarity (HNSW index) for fast
approximate nearest neighbor search.

Stores chunk text, embeddings, and metadata (idea_id, chunk_index, token_count,
title) to reconstruct Chunk objects during retrieval. The collection is named
'knowledge_vault' and lives in .brainos/vector_db/ by default.

This is the production vector store used by the RAG engine and ingestion pipeline.
"""

from pathlib import Path
from typing import List
from uuid import UUID

import chromadb

from brainos.core.models import Chunk
from brainos.knowledge.vector_store_base import AbstractVectorStore


class ChromaVectorStore(AbstractVectorStore):
    """Vector store backed by ChromaDB."""

    def __init__(self, persist_dir: str | Path = "./.brainos/vector_db"):
        """Initialize ChromaDB store.

        Args:
            persist_dir: Directory for persisting ChromaDB
        """
        persist_dir = Path(persist_dir).expanduser()
        persist_dir.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(persist_dir))
        self.collection = self.client.get_or_create_collection(
            name="knowledge_vault",
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, chunks: List[Chunk]) -> None:
        """Insert or update chunks.

        Args:
            chunks: Chunks to store
        """
        if not chunks:
            return

        ids = [str(chunk.id) for chunk in chunks]
        embeddings = [chunk.embedding for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [
            {
                "idea_id": str(chunk.idea_id),
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                **chunk.metadata,
            }
            for chunk in chunks
        ]

        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def search(self, query_embedding: List[float], top_k: int = 10) -> List[Chunk]:
        """Search for similar chunks.

        Args:
            query_embedding: Query vector
            top_k: Number of results

        Returns:
            List of matching chunks
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )

        chunks = []
        if results and results["ids"] and len(results["ids"]) > 0:
            for i, chunk_id in enumerate(results["ids"][0]):
                chunk = Chunk(
                    id=UUID(chunk_id),
                    idea_id=UUID(results["metadatas"][0][i]["idea_id"]),
                    text=results["documents"][0][i],
                    chunk_index=results["metadatas"][0][i].get("chunk_index", 0),
                    token_count=results["metadatas"][0][i].get("token_count", 0),
                    embedding=results["embeddings"][0][i] if results["embeddings"] else None,
                    metadata=results["metadatas"][0][i],
                )
                chunks.append(chunk)

        return chunks

    def delete(self, chunk_ids: List[UUID]) -> None:
        """Delete chunks by ID.

        Args:
            chunk_ids: IDs to delete
        """
        ids = [str(cid) for cid in chunk_ids]
        self.collection.delete(ids=ids)

    def get(self, chunk_id: UUID) -> Chunk:
        """Get a single chunk.

        Args:
            chunk_id: ID to retrieve

        Returns:
            The chunk

        Raises:
            KeyError if not found
        """
        result = self.collection.get(ids=[str(chunk_id)])
        if not result or not result["ids"]:
            raise KeyError(f"Chunk {chunk_id} not found")

        chunk_id_str = result["ids"][0]
        return Chunk(
            id=UUID(chunk_id_str),
            idea_id=UUID(result["metadatas"][0]["idea_id"]),
            text=result["documents"][0],
            chunk_index=result["metadatas"][0].get("chunk_index", 0),
            token_count=result["metadatas"][0].get("token_count", 0),
            embedding=result["embeddings"][0] if result["embeddings"] else None,
            metadata=result["metadatas"][0],
        )

    def clear(self) -> None:
        """Clear all chunks."""
        # Delete and recreate collection
        self.client.delete_collection(name="knowledge_vault")
        self.collection = self.client.get_or_create_collection(
            name="knowledge_vault",
            metadata={"hnsw:space": "cosine"},
        )
