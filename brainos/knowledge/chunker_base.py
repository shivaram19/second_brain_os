"""Abstract base class for text chunking strategies.

Chunking splits long markdown notes into semantically coherent segments
that fit within embedding model context limits. Implementations decide
where to split (headings, fixed tokens, sentences, etc.).

The AbstractChunker interface allows swapping strategies without modifying
the ingestion pipeline or RAG engine.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List
from uuid import UUID

from brainos.core.models import Chunk


class AbstractChunker(ABC):
    """Base class for text chunking strategies."""

    @abstractmethod
    def chunk(
        self, idea_id: UUID, text: str, metadata: Dict[str, Any] = None
    ) -> List[Chunk]:
        """Split text into chunks.

        Args:
            idea_id: UUID of the parent Idea
            text: Text to chunk
            metadata: Optional metadata to attach to chunks

        Returns:
            List of Chunk objects
        """
