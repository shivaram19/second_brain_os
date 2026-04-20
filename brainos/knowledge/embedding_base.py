"""Abstract base class for text embedding providers.

Embedders convert text chunks into dense vector representations for
semantic search. Implementations may use local models (Sentence Transformers)
or cloud APIs (Anthropic, OpenAI).

The AbstractEmbedder interface enables the RAG engine and ingestion pipeline
to remain agnostic to the underlying embedding provider.
"""

from abc import ABC, abstractmethod
from typing import List


class AbstractEmbedder(ABC):
    """Base class for text embedding providers."""

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        """Embed a single text string.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts efficiently.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """

    @abstractmethod
    def get_embedding_dim(self) -> int:
        """Get the dimensionality of embeddings.

        Returns:
            Dimension of the embedding space
        """
