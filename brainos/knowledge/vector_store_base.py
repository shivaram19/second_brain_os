"""Abstract base class for vector database implementations.

Vector stores persist chunk embeddings and support similarity search.
This interface abstracts over ChromaDB, FAISS, Pinecone, or any future
backend, allowing the RAG engine to remain implementation-agnostic.

Implementations must support upsert, search, delete, get, and clear.
"""

from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from brainos.core.models import Chunk


class AbstractVectorStore(ABC):
    """Base class for vector database implementations."""

    @abstractmethod
    def upsert(self, chunks: List[Chunk]) -> None:
        """Insert or update chunks with their embeddings.

        Args:
            chunks: Chunks with embeddings to store
        """

    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int = 10) -> List[Chunk]:
        """Search for chunks similar to the query embedding.

        Args:
            query_embedding: Query vector
            top_k: Number of top results to return

        Returns:
            List of matching chunks ordered by similarity
        """

    @abstractmethod
    def delete(self, chunk_ids: List[UUID]) -> None:
        """Delete chunks by ID.

        Args:
            chunk_ids: IDs of chunks to delete
        """

    @abstractmethod
    def get(self, chunk_id: UUID) -> Chunk:
        """Retrieve a single chunk by ID.

        Args:
            chunk_id: ID of chunk to retrieve

        Returns:
            The chunk, or raises KeyError if not found
        """

    @abstractmethod
    def clear(self) -> None:
        """Delete all chunks from the store."""
